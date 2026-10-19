"""Reject incomplete current publications before generating reader download links."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from CheckSourceCheckout import validate_current_edition


class CurrentEditionContractTests(unittest.TestCase):
    def fixture(self, root):
        documents = []
        for work in ("report", "paper", "automation"):
            for language in ("en", "zh-CN"):
                identity = f"{work}_{language}"
                markdown = f"publications/{work}/{language}/README.md"
                path = root / markdown
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Research manuscript\n", encoding="utf-8")
                def asset(name, suffix):
                    return {"local_path": f"outputs/example/{name}{suffix}",
                            "asset_name": f"review_{name}{suffix}", "sha256": "a" * 64}
                documents.append({"id": identity, "edition": work, "language": language,
                                  "markdown": markdown, "notebook": asset(identity, ".nb"),
                                  "pdfs": {layout: asset(identity + "_" + layout, ".pdf")
                                           for layout in ("single", "ieee-journal", "ieee-conference")}})
        return {"schema_version": 2, "run_id": "example", "source_edition": "example",
                "documents": documents}

    def test_complete_bilingual_set_is_accepted(self):
        with tempfile.TemporaryDirectory(prefix="Litz source contract ") as folder:
            root = Path(folder)
            index = self.fixture(root)
            self.assertEqual(validate_current_edition(root, index), [])
            self.assertFalse((root / "outputs").exists())

    def test_missing_or_duplicate_language_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = self.fixture(root)
            missing = copy.deepcopy(original)
            missing["documents"].pop()
            duplicate = copy.deepcopy(original)
            duplicate["documents"][-1] = duplicate["documents"][0]
            for index in (missing, duplicate):
                with self.subTest(ids=[row["id"] for row in index["documents"]]):
                    self.assertTrue(any("six unique" in e for e in validate_current_edition(root, index)))

    def test_missing_pdf_layout_or_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            index = self.fixture(root)
            del index["documents"][0]["pdfs"]["ieee-conference"]
            index["documents"][1]["notebook"]["sha256"] = "unverified"
            failures = validate_current_edition(root, index)
            self.assertTrue(any("three PDF layouts" in error for error in failures))
            self.assertTrue(any("SHA256" in error for error in failures))

    def test_markdown_cannot_leave_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "checkout"
            root.mkdir()
            index = self.fixture(root)
            (root.parent / "outside.md").write_text("# Outside\n", encoding="utf-8")
            index["documents"][0]["markdown"] = "../outside.md"
            self.assertTrue(any("Markdown must" in e for e in validate_current_edition(root, index)))


if __name__ == "__main__":
    unittest.main()
