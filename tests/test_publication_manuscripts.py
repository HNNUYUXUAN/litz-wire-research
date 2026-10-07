"""Acceptance of source-bound quantities, paired chapters, and physical dimensions."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import PublicationManuscripts as p

class PublicationAcceptance(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=p.read(ROOT/'manuscript/publication.json');cls.q=p.metrics(cls.m)
 def test_640_common_terminal_field_unit(self):
  q=self.q['coax_voltage_re'];self.assertEqual(q['unit'],'V/m');self.assertAlmostEqual(q['complex_quantity']['real'],.41185624504164947,14);self.assertAlmostEqual(q['complex_quantity']['imag'],4.064969102953991,14)
 def test_bundle_power_and_resistance(self):
  self.assertAlmostEqual(self.q['coax_bundle_loss']['value'],20**2*self.q['coax_rac']['value'],11)
  self.assertAlmostEqual(self.q['coax_area']['value']*self.q['coax_area']['display_scale'],5.018477584873505,12)
 def test_si_reference_layer(self):
  self.assertEqual(self.q['skin_depth']['unit'],'m');self.assertAlmostEqual(self.q['skin_depth']['value'],.00014777165489999475,16)
  self.assertEqual(self.q['q1_rac']['unit'],'ohm/m');self.assertEqual(self.q['q1_rac']['formatted'],'20.016203628')
 def test_matched_canonical_block_identities(self):
  for ed in self.m['edition'].values():
   for ch in ed['chapters']:
    z=p.blocks(ROOT/ch['sources']['zh-CN']);e=p.blocks(ROOT/ch['sources']['en']);self.assertEqual([b['id'] for b in z],[b['id'] for b in e])
 def test_single_figure_location(self):
  for ed in ['report','paper']:
   n=p.numbering(self.m,ed);self.assertEqual(len(n['figure']),21);self.assertEqual(len(n['equation']),9)
 def test_frozen_indices(self):
  for f,h in self.m['scientific_hashes'].items():self.assertEqual(p.sha(ROOT/f),h)
 def test_caption_components(self):
  for fid,spec in self.m['figures'].items():
   for lang in ['zh-CN','en']:
    self.assertTrue(spec['title'][lang].strip())
    for edition in ['report','paper']:
     self.assertTrue(spec['descriptions'][edition][lang].strip())
     self.assertNotIn(spec['title'][lang],spec['descriptions'][edition][lang])
 def test_model_reference_relationships(self):
  from PublicationDiagrams import diagram,digest
  for lang in ['zh-CN','en']:
   d=diagram('model_hierarchy',lang)
   self.assertEqual({(e['source'],e['target']) for e in d['semantics']['edges']},{('bessel','disk_fem'),('bessel','peec')})
   self.assertEqual(d['semantic_sha256'],digest(d['semantics']))
   limits=diagram('ansys_limits',lang)
   self.assertEqual(limits['semantics']['edges'],[])
 def test_figure_source_hashes(self):
  baseline=ROOT/self.m['panel_run'];data=p.read(baseline/'panel_manifest.json')
  for panel in data['panels']:
   for a in panel['assets']:self.assertEqual(p.sha(baseline/a['path_relative_to_run']),a['sha256'])

if __name__=='__main__':unittest.main()
