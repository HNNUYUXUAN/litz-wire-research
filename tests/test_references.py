import json
from pathlib import Path
import tempfile
import unittest

from litz_research.references import verify


class ReferenceTests(unittest.TestCase):
    def test_latex_citations_are_checked_with_options_and_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'references').mkdir()
            (root / 'manuscript').mkdir()
            (root / 'references/library.bib').write_text('@article{Known,title={Title},year={2026}}', encoding='utf-8')
            source = {'key': 'Known', 'role': {'en': 'test', 'zh-CN': '测试'},
                      'use_status': {'en': 'cited', 'zh-CN': '引用'}}
            (root / 'references/sources.json').write_text(json.dumps({'sources': [source]}), encoding='utf-8')
            path = root / 'manuscript/main.tex'
            path.write_text(r'\cite{Known} % \cite{Ignored}' + '\n' + r'\citep[see][p. 2]{Known, Missing}', encoding='utf-8')
            result = verify(root)
            self.assertEqual(result['errors'], ['manuscript/main.tex: unknown citation Missing'])
            path.write_text(r'\cite{Known}', encoding='utf-8')
            self.assertEqual(verify(root)['failed_checks'], 0)
