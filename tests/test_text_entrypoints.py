import importlib.util
import json
from pathlib import Path
import shlex
import unittest

from litz_research.cli import parser
from litz_research.tasks import parameters

ROOT = Path(__file__).resolve().parents[1]


class TextEntrypointTests(unittest.TestCase):
    def test_all_twenty_guides_preserve_model_inputs_and_valid_cli_commands(self):
        rows = json.loads((ROOT / 'configs/research_entries.json').read_text(encoding='utf-8'))
        self.assertEqual(len(rows), 20)
        self.assertEqual(len({(r['route'], r['language']) for r in rows}), 20)
        for row in rows:
            with self.subTest(route=row['route'], language=row['language']):
                inputs = json.loads((ROOT / row['parameters_path']).read_text(encoding='utf-8'))
                self.assertEqual(inputs, row['parameters'])
                self.assertEqual(parameters(row['model_id'], inputs, row['case']), inputs)
                guide = (ROOT / row['path']).read_text(encoding='utf-8')
                self.assertIn('physical_acceptance_status', guide)
                self.assertIn('execution_status', guide)
                self.assertNotIn('](notebooks/', guide)
                for command in row['commands'].values():
                    parser().parse_args(shlex.split(command)[1:])

    def test_generation_is_deterministic_and_contains_every_registered_guide(self):
        spec = importlib.util.spec_from_file_location('guides', ROOT / 'tools/BuildResearchGuides.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        outputs = module.generate(ROOT)
        self.assertEqual(len(outputs), 21)
        for path, content in outputs.items():
            self.assertEqual((ROOT / path).read_text(encoding='utf-8'), content)
