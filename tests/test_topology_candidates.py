"""Meaningful geometry regression checks; no electromagnetic assertions."""
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from TopologyCandidates import Candidate, hamilton_cycle


class GeometryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "configs" / "topology_candidates.json").read_text(encoding="utf-8"))

    def test_all_slot_cycles_are_adjacent_unique_and_closed(self):
        for count, shape in self.config["strand_grids"].items():
            with self.subTest(strands=count):
                cycle = hamilton_cycle(*shape)
                self.assertEqual(len(set(map(tuple, cycle))), int(count))
                self.assertTrue(np.all(np.abs(np.roll(cycle, -1, axis=0) - cycle).sum(axis=1) == 1))

    def test_nominal_area_and_straight_dc_reference(self):
        reference_area = 640 * math.pi * (.0001/2)**2
        for count in (80, 160, 640):
            candidate = Candidate(self.config, count, "straight", 12)
            area = count * math.pi * (candidate.diameter/2)**2
            self.assertAlmostEqual(area / reference_area, 1., places=14)
            lengths = candidate.lengths(1., 32)
            rdc = 1 / np.sum(self.config["conductivity_S_m"] * area/count / lengths)
            self.assertAlmostEqual(rdc * self.config["conductivity_S_m"] * reference_area, 1., places=14)

    def test_hamilton_full_period_each_id_visits_all_slots(self):
        # This catches a wrong physical-ID permutation even if positions close.
        for count in (80, 160, 640):
            candidate = Candidate(self.config, count, "hamilton_crosslayer", 12)
            z = np.arange(count) * candidate.step_length
            positions = candidate.evaluate(z)[0]
            for strand in (0, count//2, count-1):
                expected = candidate.slots[(np.arange(count)+strand) % count]
                self.assertLess(np.max(np.linalg.norm(positions[:,strand]-expected,axis=1)), 1e-12)

    def test_hamilton_C2_at_internal_knots_and_period(self):
        candidate = Candidate(self.config, 80, "hamilton_crosslayer", 12)
        # Analytic derivatives go to zero from both adjacent directed edges.
        for step in (1, 19, 40, 80):
            eps = candidate.step_length * 1e-9
            p,v,a = candidate.evaluate([step*candidate.step_length-eps, step*candidate.step_length, step*candidate.step_length+eps])
            self.assertLess(np.max(np.linalg.norm(p[2]-p[0],axis=1)), 1e-12)
            self.assertLess(np.max(np.linalg.norm(v,axis=-1)), 1e-12)
            self.assertLess(np.max(np.linalg.norm(a,axis=-1)), 1e-4)

    def test_continuous_certificate_against_different_z_pair_search(self):
        # A deliberate cross-z falsification search. The proof itself is in
        # certificate(); this search is independent of its quadratic minimizer.
        for family in self.config["families"]:
            candidate = Candidate(self.config, 80, family, 12)
            bound = candidate.certificate()["continuous_3D_centre_distance_lower_bound_m"]
            best = math.inf
            for phase in np.linspace(.1,.9,13):
                z = candidate.pitch*phase
                for offset in np.linspace(-2*candidate.diameter,2*candidate.diameter,11):
                    p = candidate.evaluate([z,z+offset])[0]
                    dist = np.sqrt(np.sum((p[0,:,None,:]-p[1,None,:,:])**2,axis=-1)+offset**2)
                    np.fill_diagonal(dist, math.inf)
                    best = min(best, float(np.min(dist)))
            with self.subTest(family=family):
                self.assertGreaterEqual(best + 1e-12, bound)
                self.assertGreater(bound-candidate.diameter,.05*candidate.diameter)

    def test_arc_integral_is_not_polyline_length(self):
        candidate = Candidate(self.config, 80, "hamilton_crosslayer", 12)
        fine = candidate.lengths(1.,32)
        self.assertTrue(np.all(fine>1.))
        self.assertLess(np.max(abs(fine/candidate.lengths(1.,64)-1)),1e-10)
        # Refined chord lengths approach the integrated smooth path from below.
        z = np.linspace(0., candidate.step_length, 2001)
        points = np.column_stack((candidate.evaluate(z)[0][:,0],z))
        chord = np.linalg.norm(np.diff(points,axis=0),axis=1).sum()
        arc = candidate.lengths(candidate.step_length,64)[0]
        self.assertLessEqual(chord, arc+1e-12)
        self.assertLess(abs(chord/arc-1),1e-6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
