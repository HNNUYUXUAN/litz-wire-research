import tempfile
import unittest
from pathlib import Path

from litz_research.paper_identity import inspect, contains_doi


class PaperIdentityTests(unittest.TestCase):
    def test_doi_prefix_is_not_an_identity_match(self):
        self.assertFalse(contains_doi('DOI: 10.1234/example.12', '10.1234/example.1'))
        self.assertFalse(contains_doi('DOI: 10.1234/example.1/supp', '10.1234/example.1'))
        self.assertTrue(contains_doi('DOI: 10.1234/\nexample.1. More text.', '10.1234/example.1'))

    def test_valid_pdf_is_not_enough_to_accept_another_paper(self):
        from reportlab.pdfgen.canvas import Canvas
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'paper.pdf'
            canvas = Canvas(str(path))
            canvas.drawString(40, 700, 'A test of conductor losses')
            canvas.drawString(40, 680, '10.1234/example.1')
            canvas.save()
            good = inspect(path, 'A test of conductor losses', '10.1234/example.1')
            self.assertEqual(good['identity_status'], 'verified')
            wrong = inspect(path, 'Another conductor paper', '10.1234/example.2')
            self.assertEqual(wrong['pdf_status'], 'parser_validated')
            self.assertEqual(wrong['identity_status'], 'mismatch')
            self.assertEqual(wrong['redistribution'], 'unknown')
            self.assertEqual(inspect(path, 'A test of conductor losses')['identity_status'], 'unverified')

    def test_html_and_malformed_pdf_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'paper.pdf'
            for contents in (b'<html>Sign in</html>', b'%PDF-1.7\ncorrupt'):
                path.write_bytes(contents)
                self.assertEqual(inspect(path, 'Paper', '10.1234/example')['pdf_status'], 'failed')
