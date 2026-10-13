"""Source identities, display units and cross-references in the Chinese specimen."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import PublicationManuscripts as publication


class ChinesePaperReading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = publication.read(ROOT / "manuscript/publication.json")
        cls.specimen = publication.read(ROOT / "manuscript/specimens/publication.paper-zh-CN.json")

    def test_scientific_values_and_sources_are_preserved(self):
        before = publication.metrics(self.baseline)
        after = publication.metrics(self.specimen)
        for name in before:
            for field in ("value", "unit", "display_scale", "source", "source_sha256", "locator"):
                self.assertEqual(before[name][field], after[name][field], (name, field))
            self.assertEqual(after[name]["formatted"], format(after[name]["value"] * after[name]["display_scale"], ".6g"))

    def test_block_identities_and_cross_references(self):
        numbers = publication.numbering(self.specimen, "paper")
        self.assertEqual(len(numbers["figure"]), 21)
        self.assertEqual(len(numbers["equation"]), 9)
        for original, draft in zip(self.baseline["edition"]["paper"]["chapters"], self.specimen["edition"]["paper"]["chapters"]):
            old_blocks = publication.blocks(ROOT / original["sources"]["zh-CN"])
            new_blocks = publication.blocks(ROOT / draft["sources"]["zh-CN"])
            self.assertEqual({b["id"] for b in old_blocks}, {b["id"] for b in new_blocks})
            for block in new_blocks:
                for kind, key in re.findall(r"\{\{(eqref|figref):([\w]+)\}\}", block["markdown"]):
                    self.assertIn(key, numbers["equation" if kind == "eqref" else "figure"])

    def test_table_display_conversions(self):
        tables = publication.table_cells(publication.input_path("data/publication"), "zh-CN")
        self.assertEqual(tables[0]["rows"][0][2], "Rac (mΩ/m)")
        self.assertAlmostEqual(float(tables[0]["rows"][1][2]), 20.1572, places=4)
        self.assertEqual(tables[2]["rows"][0], ["单元数", "积分阶数", "损耗 (mW)"])
        self.assertAlmostEqual(float(tables[2]["rows"][1][2]), .927463, places=6)
        self.assertEqual(tables[4]["rows"][0][-1], "图示相对变化 (%)")
        self.assertEqual(len(tables[4]["rows"]), 12)
        self.assertAlmostEqual(float(tables[4]["rows"][1][-1]), .298640, places=6)


if __name__ == "__main__":
    unittest.main()
