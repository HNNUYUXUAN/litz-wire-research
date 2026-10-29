"""Cross-check release files against their provenance and object dependencies."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ReleaseManifestTests(unittest.TestCase):
    def test_current_publication_documents_and_download_identities(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        from CheckSourceCheckout import validate_current_edition
        index=json.loads((ROOT/'docs/current-edition.json').read_text(encoding='utf-8'))
        self.assertEqual(validate_current_edition(ROOT, index), [])
        self.assertEqual(len(index['documents']), 6)
        self.assertEqual(sum(row['layout'] == 'single' for row in index['documents']), 2)
        self.assertTrue(all(row['main'].endswith('/main.tex') for row in index['documents']))

    def test_catalogue_provenance_and_dependency_coverage(self):
        catalogue=json.loads((ROOT/'data/catalog.json').read_text(encoding='utf-8'))
        records=json.loads((ROOT/'provenance/candidate_files.json').read_text(encoding='utf-8'))
        provenance={(r['dataset'],r['path']):r for r in records}
        self.assertEqual(catalogue['schema_version'],1)
        seen=set()
        for name,dataset in catalogue['datasets'].items():
            available={x['sha256'] for x in dataset['objects']}
            for dependency in dataset['dependencies']:
                self.assertIn(dependency,catalogue['datasets'])
                available.update(x['sha256'] for x in catalogue['datasets'][dependency]['objects'])
            for f in dataset['files']:
                self.assertIn(f['sha256'],available)
                key=(name,f['path']);self.assertNotIn(key,seen);seen.add(key)
                self.assertEqual(f['sha256'],provenance[key]['sha256'])
                self.assertTrue(provenance[key]['license'])
                self.assertTrue(provenance[key]['inspection'])
            for part in dataset['parts']:
                self.assertLessEqual(part['bytes'],2**30)
                self.assertEqual(len(part['sha256']),64)
        self.assertEqual(seen,set(provenance))
if __name__=='__main__':unittest.main()
