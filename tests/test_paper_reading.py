"""Retain original manuscript identities through the canonical LaTeX migration."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PaperMigrationTests(unittest.TestCase):
    def test_every_original_block_survives_in_its_target_section(self):
        receipt = json.loads((ROOT / 'manuscript/migration-receipt.json').read_text(encoding='utf-8'))
        for chapter in receipt['chapters']:
            text = (ROOT / chapter['target']).read_text(encoding='utf-8')
            ids = re.findall(r'^% block-id: (.+)$', text, re.M)
            self.assertEqual(len(ids), len(set(ids)), chapter['target'])
            self.assertEqual([identity for identity in ids if identity in chapter['block_ids']],
                             chapter['block_ids'], chapter['target'])

    def test_full_migration_audit_is_bound_to_the_selected_edition(self):
        audit = json.loads((ROOT / 'provenance/current-publication/migration-text-audit.json').read_text(encoding='utf-8'))
        reading = json.loads((ROOT / 'provenance/current-publication/reading-receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(audit['run_id'], reading['run_id'])
        self.assertEqual(audit['status'], 'passed')
        self.assertEqual(len(audit['blocks']), audit['original_blocks'])
        self.assertEqual(audit['original_blocks'], sum(audit[key] for key in
                         ['exact_or_reference_style_matches', 'figure_identity_and_caption_matches', 'reviewed_maintenance_updates']))
