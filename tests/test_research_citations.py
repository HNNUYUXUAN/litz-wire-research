from pathlib import Path
import tempfile
import unittest

from litz_research.research_citations import export


class ResearchCitationTests(unittest.TestCase):
    def test_preserves_project_keys_conflicts_and_reproducible_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'references').mkdir()
            (root / 'references/library.bib').write_text(
                '@article{Stable,title={中文 title},doi={10.1234/CASE},year={2026}}', encoding='utf-8')
            data = {'results': [{'doi': 'https://doi.org/10.1234/case'}],
                    'conflicts': [{'field': 'year', 'values': [2025, 2026]}]}
            target = root / 'selected.bib'
            receipt = export(root, data, target)
            self.assertEqual(receipt['keys'], ['Stable'])
            self.assertEqual(receipt['normalization_conflicts'], data['conflicts'])
            first = target.read_bytes()
            export(root, data, target)
            self.assertEqual(target.read_bytes(), first)
            with self.assertRaisesRegex(ValueError, 'Review and adopt'):
                export(root, [{'doi': '10.1234/UNKNOWN'}], target)
            self.assertEqual(target.read_bytes(), first)
