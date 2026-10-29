"""Publication navigation requires source and generated-reading identity."""
from contextlib import redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import BuildPublicationIndex as INDEX

class PublicationIndexTests(unittest.TestCase):
    def load(self, root, path):
        return json.loads((root/path).read_text(encoding='utf-8-sig'))
    def write(self, root, path, value):
        target=root/path; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def fixture(self,root):
        receipt=self.load(ROOT,INDEX.RECEIPT)
        paths={INDEX.RECEIPT,receipt['source_manifest'],'data/catalog.json','provenance/editorial/online-assets.json'}
        for doc in receipt['documents']:
            paths.update(doc['input_hashes']); paths.add(doc['markdown'])
        for path in paths:
            target=root/path; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/path,target)
        self.assertFalse((root/'outputs').exists())
    def test_future_build_updates_current_identity_and_preserves_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); self.fixture(root)
            receipt=self.load(root,INDEX.RECEIPT); receipt['run_id']='future_publication_01'
            self.write(root,INDEX.RECEIPT,receipt)
            historical=(root/'provenance/editorial/online-assets.json').read_bytes()
            generated=INDEX.generate(root); index=json.loads(generated['docs/current-edition.json'])
            self.assertEqual(index['run_id'],'future_publication_01')
            self.assertEqual(len(index['documents']),6)
            self.assertEqual({x['layout'] for x in index['documents']},{'single','ieee-journal'})
            self.assertIn('future_publication_01',generated['publications/DELIVERY.md'])
            self.assertEqual(historical,(root/'provenance/editorial/online-assets.json').read_bytes())
            self.assertFalse((root/'outputs').exists())
    def test_source_and_reading_changes_require_new_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            receipt=self.load(root,INDEX.RECEIPT); doc=receipt['documents'][0]
            for path in [doc['source'],next(iter(doc['sections'])),doc['markdown']]:
                target=root/path; original=target.read_bytes();target.write_bytes(original+b'\nchanged\n')
                with self.subTest(path=path),self.assertRaisesRegex(ValueError,'SHA256'):
                    INDEX.generate(root)
                target.write_bytes(original)
    def test_check_rejects_stale_online_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            with redirect_stdout(io.StringIO()): INDEX.build(root);INDEX.build(root,check=True)
            target=root/'publications/ONLINE.md'; stale=target.read_bytes()+b'\nstale\n';target.write_bytes(stale)
            with self.assertRaisesRegex(ValueError,'Stale publication indexes: .*ONLINE'):
                INDEX.build(root,check=True)
            self.assertEqual(target.read_bytes(),stale)
    def test_historical_links_use_catalog_identity_and_encoded_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            self.write(root,'data/catalog.json',{'repository':'FixtureOrg/research-data'})
            online=self.load(root,'provenance/editorial/online-assets.json');online['release_tag']='release/one #1'
            for row in online['artifacts']: row['name']='public copy #1_'+row['name']
            self.write(root,'provenance/editorial/online-assets.json',online)
            extra={'release_tag':'license/2','artifacts':[{'name':'license companion #1.zip'}]}
            self.write(root,'provenance/maintenance/supplemental-assets.json',extra)
            generated=INDEX.generate(root)
            for suffix in ('','.zh-CN'):
                text=generated[f'publications/HISTORY{suffix}.md']
                for group in [online,extra]:
                    for row in group['artifacts']:
                        url='https://github.com/FixtureOrg/research-data/releases/download/'+quote(group['release_tag'],safe='')+'/'+quote(row['name'],safe='')
                        self.assertIn(']('+url+')',text)
    def test_migration_changes_history_links_without_rewriting_frozen_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            before=(root/'provenance/editorial/online-assets.json').read_bytes()
            self.write(root,'provenance/repository-migration.json',{'archive_repository':'FixtureOrg/research-archive'})
            generated=INDEX.generate(root)
            self.assertIn('https://github.com/FixtureOrg/research-archive/releases/',generated['publications/HISTORY.md'])
            self.assertEqual((root/'provenance/editorial/online-assets.json').read_bytes(),before)

    def test_section_order_is_part_of_build_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            receipt=self.load(root,INDEX.RECEIPT); manifest=self.load(root,receipt['source_manifest'])
            manifest['documents'][0]['sections'].reverse()
            self.write(root,receipt['source_manifest'],manifest)
            receipt['source_manifest_sha256']=hashlib.sha256((root/receipt['source_manifest']).read_bytes()).hexdigest()
            self.write(root,INDEX.RECEIPT,receipt)
            with self.assertRaisesRegex(ValueError,'section order'): INDEX.generate(root)

if __name__=='__main__':unittest.main()
