import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from CheckReaderLinks import check


class ReaderLinkTests(unittest.TestCase):
    def test_ignored_local_artifact_does_not_mask_broken_github_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'outputs').mkdir()
            (root / 'outputs/book.pdf').write_bytes(b'local')
            (root / 'README.md').write_text('[Book](outputs/book.pdf)', encoding='utf-8')
            result = check(root, {'README.md'})
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['failed_links'][0]['resolved'], 'outputs/book.pdf')

    def test_tracked_paths_with_spaces_and_code_examples(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'docs').mkdir()
            (root / 'docs/guide one.md').write_text('# Guide', encoding='utf-8')
            (root / 'README.md').write_text('[Guide](<docs/guide one.md>)\n```md\n[Example](missing.md)\n```\n[Site](https://example.com)\n[Anchor](#title)', encoding='utf-8')
            result = check(root, {'README.md', 'docs/guide one.md'})
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['relative_links'], 1)
