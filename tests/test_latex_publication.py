import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from litz_research.latex_publication import (
    adapt_tex, brace_argument, check_raw, expand_inputs, pandoc_path,
    render_markdown, verify_metrics, verify_page_review, sha, write_reading,
)


class LatexPublicationTests(unittest.TestCase):
    def test_reading_write_preserves_existing_file_when_replacement_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'reading.md'
            target.write_bytes(b'original')
            with patch('litz_research.latex_publication.os.replace', side_effect=OSError(5, 'fixture failure')):
                with self.assertRaises(OSError):
                    write_reading(target, b'new complete content')
            self.assertEqual(target.read_bytes(), b'original')
            self.assertEqual(list(Path(folder).iterdir()), [target])
            write_reading(target, b'new complete content')
            self.assertEqual(target.read_bytes(), b'new complete content')

    def test_page_review_binds_every_page_to_the_compiled_pdf(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            page = run / 'page.png'
            page.write_bytes(b'rendered page fixture')
            compiled = [{'id': 'one', 'pdf_sha256': 'a' * 64, 'page_count': 1}]
            self.assertEqual(verify_page_review(run, compiled), 'requires_page_review')
            review = [{'document': 'one', 'pdf_sha256': 'a' * 64, 'visual_review': 'passed',
                       'reviewed_pages': [1], 'pages': ['page.png'], 'page_hashes': {'page.png': sha(page)}}]
            (run / 'page-review.json').write_text(json.dumps(review), encoding='utf-8')
            self.assertEqual(verify_page_review(run, compiled), 'passed')
            review[0]['reviewed_pages'] = []
            (run / 'page-review.json').write_text(json.dumps(review), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'every page'):
                verify_page_review(run, compiled)
            review[0]['reviewed_pages'] = [1]
            (run / 'page-review.json').write_text(json.dumps(review), encoding='utf-8')
            page.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'image changed'):
                verify_page_review(run, compiled)

    def test_unknown_content_and_missing_references_fail(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported LaTeX'):
            check_raw({'t': 'RawInline', 'c': ['latex', r'\mystery{lost text}']})
        with self.assertRaisesRegex(ValueError, 'Unresolved cross-reference'):
            adapt_tex(r'\ref{eq:missing}', {})
        with self.assertRaisesRegex(ValueError, 'Unbalanced'):
            brace_argument('{outer{inner}', 0)

    def test_nested_inputs_are_relative_to_main_and_cannot_escape(self):
        with tempfile.TemporaryDirectory(prefix='LaTeX 中文 ') as temp:
            root = Path(temp)
            folder = root / 'manuscript/doc'
            (folder / 'sections').mkdir(parents=True)
            (folder / 'main.tex').write_text(r'\input{sections/a.tex}', encoding='utf-8')
            (folder / 'sections/a.tex').write_text(r'\input{sections/b.tex}', encoding='utf-8')
            (folder / 'sections/b.tex').write_text('内容', encoding='utf-8')
            self.assertEqual(expand_inputs(folder / 'main.tex', root), '内容')
            (folder / 'sections/b.tex').write_text(r'\input{../../outside.tex}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                expand_inputs(folder / 'main.tex', root)
            (folder / 'sections/b.tex').write_text(r'\input{main.tex}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Cyclic'):
                expand_inputs(folder / 'main.tex', root)

    def test_numeric_mapping_is_recomputed_not_just_hash_checked(self):
        root = Path(__file__).resolve().parents[1]
        metrics = json.loads((root / 'manuscript/metrics.json').read_text(encoding='utf-8'))
        verify_metrics(root, metrics)
        altered = copy.deepcopy(metrics)
        altered['q1_rac']['formatted'] = '99'
        with self.assertRaisesRegex(ValueError, 'Formatted value'):
            verify_metrics(root, altered)
        altered = copy.deepcopy(metrics)
        altered['coax_spread']['value'] *= 2
        with self.assertRaisesRegex(ValueError, 'Mapped value'):
            verify_metrics(root, altered)

    def test_pandoc_keeps_unicode_math_tables_ids_and_citations(self):
        try:
            pandoc = pandoc_path()
        except ValueError:
            self.skipTest('Pandoc 3.13 integration dependency unavailable')
        with tempfile.TemporaryDirectory(prefix='稿件 path ') as temp:
            root = Path(temp)
            folder = root / 'manuscript/doc'
            folder.mkdir(parents=True)
            main = folder / 'main.tex'
            main.write_text(r'''\documentclass{article}
\title{中文试验}\author{Author}
\begin{document}\maketitle
\begin{abstract}Preserve evidence.\end{abstract}
\section{Results}
% block-id: test.p1
\hypertarget{test.p1}{}
电阻 \metric{r}，see \eqref{eq:e} and \cite{C01}.
\begin{equation}P=|I|^2R\label{eq:e}\end{equation}
\begin{table*}\caption{数值}
\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}X}
\toprule Name & Value\\\midrule R & 20.0162\\\bottomrule
\end{tabularx}\end{table*}
\end{document}''', encoding='utf-8')
            doc = {'id': 'test_en', 'main': main.relative_to(root).as_posix()}
            text, identities = render_markdown(root, doc, pandoc, {'r': {'formatted': '20.0162'}})
            self.assertIn('20.0162', text)
            self.assertIn('[@C01]', text)
            self.assertIn('中文试验', text)
            self.assertNotIn(r'\begin{equation}', text)
            self.assertEqual(identities['block_ids'], ['test.p1'])
            main.write_text(main.read_text(encoding='utf-8').replace('电阻', r'\mystery{hidden} 电阻'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Unsupported LaTeX'):
                render_markdown(root, doc, pandoc, {'r': {'formatted': '20.0162'}})
