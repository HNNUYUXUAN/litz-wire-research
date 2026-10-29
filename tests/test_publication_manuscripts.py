"""Scientific quantities and bilingual identities in canonical LaTeX sources."""
import json
from pathlib import Path
import re
import unittest

from litz_research.latex_publication import document_inputs, verify_metrics

ROOT = Path(__file__).resolve().parents[1]


class PublicationAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'manuscript/latex-publication.json').read_text(encoding='utf-8'))
        cls.quantities = json.loads((ROOT / 'manuscript/metrics.json').read_text(encoding='utf-8'))

    def test_scientific_quantities_and_source_recomputation(self):
        q = self.quantities
        verify_metrics(ROOT, q)
        self.assertEqual(q['coax_voltage_re']['unit'], 'V/m')
        self.assertAlmostEqual(q['coax_voltage_re']['complex_quantity']['real'], .41185624504164947, 14)
        self.assertAlmostEqual(q['coax_voltage_re']['complex_quantity']['imag'], 4.064969102953991, 14)
        self.assertAlmostEqual(q['coax_bundle_loss']['value'], 20**2 * q['coax_rac']['value'], 11)
        self.assertAlmostEqual(q['coax_area']['value'] * q['coax_area']['display_scale'], 5.018477584873505, 12)
        self.assertEqual(q['skin_depth']['unit'], 'm')
        self.assertAlmostEqual(q['skin_depth']['value'], .00014777165489999475, 16)
        self.assertEqual(q['q1_rac']['formatted'], '20.0162')

    def test_paired_blocks_references_and_unique_labels(self):
        identities = {}
        for doc in self.manifest['documents']:
            text = '\n'.join((ROOT / path).read_text(encoding='utf-8') for path in doc['sections'])
            labels = re.findall(r'\\label\{([^}]+)\}', text)
            self.assertEqual(len(labels), len(set(labels)), doc['id'])
            for label in re.findall(r'\\ref\{([^}]+)\}', text):
                self.assertIn(label, labels)
            identity = (re.findall(r'^% block-id: (.+)$', text, re.M),
                        re.findall(r'\\cite\{([^}]+)\}', text), labels)
            if doc['edition'] in identities:
                self.assertEqual(identity, identities[doc['edition']])
            identities[doc['edition']] = identity
            document_inputs(ROOT, doc)
            main = (ROOT / doc['main']).read_text(encoding='utf-8')
            self.assertIn(r'\documentclass[11pt,a4paper]{article}' if doc['edition'] == 'report'
                          else r'\documentclass[journal,10pt]{IEEEtran}', main)
