"""Physical parameter propagation, evidence identity and task cancellation tests."""
from pathlib import Path
import hashlib,json,tempfile,unittest,shutil,os
from litz_research.common import project,write,evidence_path,evidence_root,sha
from litz_research.tasks import execute,parameters
from litz_research.analytical import solve

class AutomationTests(unittest.TestCase):
    def test_changed_frequency_keeps_independent_integrals_and_skips_reference(self):
        root=project()
        with tempfile.TemporaryDirectory() as tmp:
            from litz_research.analytical import execute as run
            result=run(root,Path(tmp),{'frequency_Hz':100000.})
            self.assertFalse(result['reference_comparison_applicable'])
            self.assertEqual(result['physical_acceptance_status'],'passed')
            self.assertLess(result['diagnostics']['current_error'],1e-8)
            self.assertLess(result['diagnostics']['power_error'],1e-8)
            self.assertLess(result['values']['Q1_Rac_mohm_per_m'],20.016203627649382)

    def test_frequency_extension_preserves_dc_limit_and_integrals(self):
        with tempfile.TemporaryDirectory() as tmp:
            from litz_research.analytical import execute as run
            r=run(project(),Path(tmp),case='frequency-sweep')
            self.assertEqual(r['physical_acceptance_status'],'passed')
            self.assertAlmostEqual(r['frequency_sweep'][0]['values']['Q1_Rac_Rdc'],1.,places=6)
            self.assertTrue(all(row['diagnostics']['power_error']<1e-8 for row in r['frequency_sweep']))

    def test_corrupted_mounted_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);content=b'20 A RMS';digest=hashlib.sha256(content).hexdigest()
            write(root/'data/catalog.json',{'tag':'fixture','datasets':{'analytic':{'files':[{'path':'outputs/run/results.json','sha256':digest,'bytes':len(content)}]}}})
            path=evidence_root(root)/'outputs/run/results.json';path.parent.mkdir(parents=True);path.write_bytes(content)
            self.assertEqual(evidence_path(root,'outputs/run/results.json'),path)
            path.write_bytes(b'corrupted')
            with self.assertRaises(ValueError):evidence_path(root,'outputs/run/results.json')

    def test_cancel_before_worker_prevents_solver_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cancel=root/'outputs/.jobs/cancelled_01.cancel';cancel.parent.mkdir(parents=True);cancel.touch()
            result=execute(root,'analytic','cancelled_01')
            self.assertEqual(result['execution_status'],'cancelled')
            self.assertFalse(result['solver_started'])

    def test_dataset_version_controls_mount_and_automatic_readback(self):
        from litz_research.data import fetch,cached_object
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache=root/'cache';data=b'new run';identity=hashlib.sha256(data).hexdigest()
            write(root/'data/catalog.json',{'tag':'v1','datasets':{'new':{'source_version':'v2','dependencies':[],'objects':[{'sha256':identity,'bytes':len(data)}],'files':[{'path':'outputs/new/results.txt','sha256':identity,'bytes':len(data)}],'parts':[]}}})
            obj=cached_object(cache,identity);obj.parent.mkdir(parents=True);obj.write_bytes(data)
            self.assertEqual(fetch(root,'new',cache,offline=True)[0]['status'],'passed')
            self.assertEqual(evidence_path(root,'outputs/new/results.txt'),evidence_root(root,'v2')/'outputs/new/results.txt')
            self.assertFalse((evidence_root(root,'v1')/'outputs/new/results.txt').exists())

    def test_tutorial_rejects_accidental_large_campaign(self):
        for model,p in [('coax',{'strands':640}),('peec',{'cross_divisions':80}),('rt0',{'dimensions':[16,16,32]}),('gpu',{'matrix_size':65537})]:
            with self.assertRaises(ValueError):parameters(model,p)

    def test_restore_supports_long_windows_snapshot_paths(self):
        from litz_research.data import fetch,cached_object
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cache=root/'cache';data=b'saved source';identity=hashlib.sha256(data).hexdigest()
            relative='outputs/'+('long_snapshot_'*6)+'/source_snapshot/'+('subdirectory_'*6)+'/source.json'
            write(root/'data/catalog.json',{'tag':'fixture','datasets':{'snapshot':{'dependencies':[],'objects':[{'sha256':identity,'bytes':len(data)}],'files':[{'path':relative,'sha256':identity,'bytes':len(data)}],'parts':[]}}})
            obj=cached_object(cache,identity);obj.parent.mkdir(parents=True);obj.write_bytes(data)
            try:
                self.assertEqual(fetch(root,'snapshot',cache,offline=True)[0]['status'],'passed')
                self.assertEqual(sha(evidence_path(root,relative)),identity)
            finally:
                # tempfile's Windows cleanup also needs the extended prefix
                # once this fixture intentionally exceeds MAX_PATH.
                branch=(evidence_root(root)/'outputs').resolve()
                assert branch.is_relative_to(root.resolve())
                if branch.exists():shutil.rmtree('\\\\?\\'+str(branch) if os.name=='nt' else branch)

    def test_parameters_must_be_actual_supported_inputs(self):
        with self.assertRaises(ValueError):parameters('aphi',{'frequency_Hz':100000})
        with self.assertRaises(ValueError):parameters('fem2',{'radius_m':.002})
        with self.assertRaises(ValueError):parameters('fem2',case='preflight')
        self.assertEqual(parameters('ansys',{'frequency_Hz':100000},case='maxwell-seven')['frequency_Hz'],100000)

if __name__=='__main__':unittest.main()
