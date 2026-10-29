"""Exercise process isolation and restart identity, not implementation mirrors."""
from pathlib import Path
import os,shutil,subprocess,sys,tempfile,time,unittest
from litz_research.common import project,write
from litz_research.tasks import execute,submit,status,resume,bounded_process
from litz_research.processes import stop_owned

class LifecycleTests(unittest.TestCase):
    def test_saved_solver_result_does_not_publish_completion_before_cleanup(self):
        import psutil
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'outputs/example'
            write(out/'results.json',{'execution_status':'completed','physical_acceptance_status':'passed'})
            write(out/'process_status.json',{'execution_status':'running'})
            write(root/'outputs/.jobs/example.process.json',{'pid':os.getpid(),'created':psutil.Process().create_time()})
            result=status(root,'example')
            self.assertEqual(result['execution_status'],'running')
            self.assertEqual(result['worker_status'],'finishing')
            # A reused identity must not turn an incomplete task into success.
            write(root/'outputs/.jobs/example.process.json',{'pid':os.getpid(),'created':psutil.Process().create_time()+1})
            self.assertEqual(status(root,'example')['execution_status'],'interrupted_worker_missing')
            write(out/'process_status.json',{'execution_status':'completed'})
            self.assertEqual(status(root,'example')['execution_status'],'completed')

    def fixture(self,folder):
        root=Path(folder);source=project()
        (root/'configs').mkdir()
        (root/'pyproject.toml').write_text('[project]\nname="fixture"\n')
        for name in ['reference_parameters.json','reference_values.json']:shutil.copy2(source/'configs'/name,root/'configs'/name)
        return root

    def wait(self,root,rid):
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            result=status(root,rid)
            if result['execution_status'] not in {'submitted','running'}:
                import psutil,json
                identity=json.loads((root/'outputs/.jobs'/(rid+'.process.json')).read_text())
                try:alive=psutil.Process(identity['pid']).create_time()==identity['created']
                except psutil.Error:alive=False
                if not alive:return result
            time.sleep(.05)
        self.fail('Analytical worker did not finish')

    def test_async_restart_preserves_inputs_and_rejects_duplicate_identity(self):
        with tempfile.TemporaryDirectory(prefix='litz lifecycle space ') as tmp:
            root=self.fixture(tmp)
            submit(root,'analytic','first',supplied={'frequency_Hz':100000.})
            self.assertEqual(self.wait(root,'first')['physical_acceptance_status'],'passed')
            with self.assertRaises((FileExistsError,ValueError)):submit(root,'analytic','first')
            restarted=resume(root,'first','second')
            self.assertEqual(restarted['parent']['resume_method'],'restart_from_verified_saved_inputs')
            self.assertEqual(self.wait(root,'second')['parameters']['frequency_Hz'],100000.)

    def test_restart_rejects_a_corrupted_saved_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.fixture(tmp);execute(root,'analytic','first')
            (root/'outputs/first/source_snapshot/configs/reference_parameters.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'checkpoint identity'):resume(root,'first','second')
            self.assertFalse((root/'outputs/second').exists())

    def test_queued_cancel_can_restart_without_a_solver_checkpoint(self):
        from litz_research.tasks import plan
        from litz_research.common import sha
        with tempfile.TemporaryDirectory() as tmp:
            root=self.fixture(tmp);ticket=root/'outputs/.jobs/first.json'
            write(ticket,plan(root,'analytic','first'))
            write(ticket.with_name('first.process.json'),{'ticket_sha256':sha(ticket)})
            ticket.with_suffix('.cancel').touch();execute(root,'analytic','first')
            restarted=resume(root,'first','second')
            self.assertFalse(restarted['parent']['original_solver_started'])
            self.assertEqual(self.wait(root,'second')['physical_acceptance_status'],'passed')

    def test_timeout_releases_only_owned_processes(self):
        import psutil
        twin=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try:
            created=psutil.Process(twin.pid).create_time()
            self.assertFalse(stop_owned(twin.pid,created+1))
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                result=bounded_process([sys.executable,'-c','import time;time.sleep(30)'],root,root,dict(os.environ),{'cpu_threads':8,'task_memory_bytes':24*2**30,'system_reserve_bytes':8*2**30,'timeout_seconds':.2})
                self.assertEqual(result['failure_reason'],'timeout')
                self.assertIsNone(twin.poll())
        finally:
            twin.terminate();twin.wait(timeout=5)

    def test_reused_parent_pid_does_not_adopt_an_older_process(self):
        from litz_research.processes import owned_tree
        class Process:
            def __init__(self,pid,created,children=()):self.pid=pid;self.created=created;self.descendants=list(children)
            def create_time(self):return self.created
            def children(self,recursive=False):return self.descendants
        unrelated=Process(2,10);grandchild=Process(4,22)
        child=Process(3,21,[grandchild,Process(5,19)])
        root=Process(1,20,[unrelated,child])
        self.assertEqual([p.pid for p in owned_tree(root)],[1,3,4])

if __name__=='__main__':unittest.main()
