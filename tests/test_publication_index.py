"""Publication navigation follows the selected build and checks without rewriting."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from urllib.parse import quote

HERE = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("LITZ_PUBLICATION_TEST_ROOT", str(HERE)))
SPEC = importlib.util.spec_from_file_location("publication_index", ROOT / "tools/BuildPublicationIndex.py")
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)


class PublicationIndexTests(unittest.TestCase):
    def fixture(self, root):
        paths = ["provenance/editorial/delivery-manifest.json",
                 "provenance/editorial/online-assets.json", "publications/manifest.json"]
        paths += [f"publications/{work}/{language}/README.md"
                  for work in ("report", "automation", "paper")
                  for language in ("en", "zh-CN")]
        for relative in paths:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        (root / 'data').mkdir()
        repository = self.load(ROOT, 'data/catalog.json')['repository']
        self.write(root, 'data/catalog.json', {'repository': repository})
        self.assertFalse((root / "outputs").exists())
        self.assertFalse((root / "data/evidence").exists())

    def load(self, root, name):
        return json.loads((root / name).read_text(encoding="utf-8-sig"))

    def write(self, root, name, value):
        (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")

    def test_future_manifest_updates_online_assets_and_delivery_counts(self):
        with tempfile.TemporaryDirectory(prefix="Litz future reading ") as folder:
            root = Path(folder)
            self.fixture(root)
            delivery_path = "provenance/editorial/delivery-manifest.json"
            reading_path = "publications/manifest.json"
            online_path = "provenance/editorial/online-assets.json"
            delivery = self.load(root, delivery_path)
            reading = self.load(root, reading_path)
            online = self.load(root, online_path)
            old_run = delivery["run_id"]
            future_run = "publication_future_fixture_01"
            delivery["run_id"] = reading["source_edition"] = future_run
            for artifact in delivery["artifacts"]:
                artifact["path"] = artifact["path"].replace(old_run, future_run)
            for resource in reading["files"]:
                if "source" in resource:
                    resource["source"] = resource["source"].replace(old_run, future_run)
            old_prefix = next(asset["name"][:-len("report_en.nb")]
                              for asset in online["artifacts"]
                              if asset["name"].endswith("report_en.nb"))
            new_prefix = "release_future_fixture_"
            for asset in online["artifacts"]:
                if asset["name"].startswith(old_prefix):
                    asset["name"] = new_prefix + asset["name"][len(old_prefix):]
            delivery["counts"].update(pdf_pages=317, latex_manuscripts=27,
                                       templates=8, scientific_figure_families=23)
            for name, value in ((delivery_path, delivery), (reading_path, reading),
                                (online_path, online)):
                self.write(root, name, value)

            generated = INDEX.generate(root)
            current = json.loads(generated["docs/current-edition.json"])
            self.assertEqual(current["run_id"], future_run)
            self.assertEqual(current["source_edition"], future_run)
            for suffix in ("", ".zh-CN"):
                with self.subTest(language=suffix or "en"):
                    online_text = generated[f"publications/ONLINE{suffix}.md"]
                    self.assertNotIn(old_prefix, online_text)
                    self.assertIn(new_prefix + "report_en", online_text)
                    for asset in online["artifacts"]:
                        if asset["name"].endswith(".zip"):
                            self.assertIn(asset["name"], online_text)
                    summary = generated[f"publications/DELIVERY{suffix}.md"]
                    self.assertIn("317", summary)
                    self.assertIn("23", summary)
                    self.assertTrue("35" in summary or ("27" in summary and "8" in summary))
                    self.assertNotIn("six editable templates", summary)
                    self.assertNotIn("六份可编辑模板", summary)
            self.assertFalse((root / "outputs").exists())

    def test_check_rejects_stale_online_without_rewriting_it(self):
        for suffix in ("", ".zh-CN"):
            with self.subTest(language=suffix or "en"), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                self.fixture(root)
                with redirect_stdout(io.StringIO()):
                    INDEX.build(root)
                    INDEX.build(root, check=True)
                target = root / f"publications/ONLINE{suffix}.md"
                stale = target.read_bytes() + b"\nStale fixture download entry.\n"
                target.write_bytes(stale)
                with redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "Stale publication indexes: .*ONLINE"):
                    INDEX.build(root, check=True)
                self.assertEqual(target.read_bytes(), stale)

    def test_public_links_use_catalog_identity_tag_and_encoded_asset_names(self):
        with tempfile.TemporaryDirectory(prefix='Litz public links ') as folder:
            root = Path(folder)
            self.fixture(root)
            self.write(root, 'data/catalog.json', {'repository': 'FixtureOrg/research-data'})
            online_path = 'provenance/editorial/online-assets.json'
            online = self.load(root, online_path)
            online['release_tag'] = 'future release/1'
            online['release_url'] = 'https://example.invalid/obsolete-release-list'
            for item in online['artifacts']:
                item['name'] = 'public copy #1_' + item['name']
            self.write(root, online_path, online)
            supplemental = {'release_tag': 'license release/2',
                            'artifacts': [{'name': 'license companion #1.zip'}]}
            (root / 'provenance/maintenance').mkdir(parents=True)
            self.write(root, 'provenance/maintenance/supplemental-assets.json', supplemental)
            frozen_paths = ('provenance/editorial/delivery-manifest.json', online_path,
                            'publications/manifest.json')
            before = {name: (root / name).read_bytes() for name in frozen_paths}

            generated = INDEX.generate(root)
            base = 'https://github.com/FixtureOrg/research-data/releases/'
            tag = quote(online['release_tag'], safe='')
            current = json.loads(generated['docs/current-edition.json'])
            self.assertEqual(current['release']['url'], base + 'tag/' + tag)
            for suffix in ('', '.zh-CN'):
                text = generated[f'publications/ONLINE{suffix}.md']
                self.assertIn(base + 'tag/' + tag, text)
                self.assertNotIn('example.invalid', text)
                self.assertNotIn('private repository', text)
                self.assertNotIn('私有仓库', text)
                for item in online['artifacts']:
                    url = base + 'download/' + tag + '/' + quote(item['name'], safe='')
                    self.assertIn('](' + url + ')', text)
                license_url = (base + 'download/' + quote(supplemental['release_tag'], safe='')
                               + '/' + quote(supplemental['artifacts'][0]['name'], safe=''))
                self.assertIn('](' + license_url + ')', text)
            for name in frozen_paths:
                self.assertEqual((root / name).read_bytes(), before[name])
            self.assertFalse((root / 'outputs').exists())


if __name__ == "__main__":
    unittest.main()
