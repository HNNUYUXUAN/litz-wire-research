"""Guard scientific thresholds, exact mesh identity and shared task cancellation."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest
from litz_research.tasks import parameters, execute

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'adapters/ansys'))
from MeshIdentity import canonical


class ConvergenceCases(unittest.TestCase):
    def test_thresholds_and_candidate_meshes(self):
        for case in ['manufactured','cylinder-calibration','extrusion-control']:
            self.assertEqual(parameters('aphi', case=case)['phi_tolerance'], 1e-8)
            with self.assertRaises(ValueError): parameters('aphi', {'phi_tolerance':1e-7}, case)
            with self.assertRaises(ValueError): parameters('aphi', {'solve_timeout_seconds':601}, case)
        with self.assertRaises(ValueError): parameters('ansys', {'mesh_length_m':1e-6}, 'maxwell-seven-convergence')

    def test_cancelled_new_cases_never_start_solver(self):
        for model,case in [('aphi','manufactured'),('aphi','cylinder-calibration'),('aphi','extrusion-control'),('ansys','maxwell-seven-convergence')]:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); cancel=root/'outputs/.jobs/cancelled.cancel'
                cancel.parent.mkdir(parents=True); cancel.touch()
                result=execute(root,model,'cancelled',case)
                self.assertFalse(result['solver_started'])
                self.assertEqual(result['execution_status'],'cancelled')

    def mesh(self, root, nodes, records):
        with (root/'mesh_nodes_SI.csv').open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['mesh_file','node_id','x_m','y_m','z_m']);writer.writerows(nodes)
        with (root/'mesh_records.csv').open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['mesh_file','record_kind','declared_arity','native_values']);writer.writerows(records)
        return canonical(root)['sha256']

    def test_numbering_only_normalization_preserves_geometry_and_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=self.mesh(root,[['a',1,0,0,0],['a',2,1,0,0],['a',3,0,1,0]],[['a','t',6,'1,1,2,3,13,0']])
            renumbered=self.mesh(root,[['b',9,0,1,0],['b',7,0,0,0],['b',8,1,0,0]],[['b','t',6,'4,8,9,7,13,0']])
            self.assertEqual(original,renumbered)
            changed=self.mesh(root,[['b',9,0,1,0],['b',7,0,0,0],['b',8,'1.000000000000001',0,0]],[['b','t',6,'4,8,9,7,13,0']])
            self.assertNotEqual(original,changed)
            marker=self.mesh(root,[['a',1,0,0,0],['a',2,1,0,0],['a',3,0,1,0]],[['a','t',6,'1,1,2,3,14,0']])
            self.assertNotEqual(original,marker)


if __name__=='__main__': unittest.main()
