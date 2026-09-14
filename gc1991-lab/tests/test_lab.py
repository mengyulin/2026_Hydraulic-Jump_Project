"""Small scientific/interface checks; no grid studies or long integrations."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import lab
from core import standard_step as ss

class TeachingChecks(unittest.TestCase):
    def test_belanger_momentum_and_energy(self):
        h=.043;q=h*2.737;y2=ss.conjugate(h,q)
        self.assertAlmostEqual(ss.force(h,q),ss.force(y2,q),places=12)
        self.assertAlmostEqual(ss.energy(h,q)-ss.energy(y2,q),(y2-h)**3/(4*h*y2),places=12)
        self.assertGreater(y2,ss.critical(q))

    def test_standard_step_against_archived_independent_branches(self):
        p=lab.load_case()['physical']
        s=ss.solve(p['hin_m']*p['uin_m_s'],p['hin_m'],p['hout_m'],p['manning_n'],dx=.005)
        old=lab.read_json(lab.ROOT/'reference/standard_step.json')
        self.assertLess(abs(s['jump']['x_m']-old['jump']['x_m']),.002)
        self.assertLess(s['jump']['relative_force_residual'],1e-6)

    def test_gvf_initial_coordinates_units_and_archived_states(self):
        case=lab.load_case()
        for method in ('sv','custom'):
            rows=np.array(list(lab.initial_rows(case,method)))
            frozen=np.loadtxt(lab.ROOT/f'reference/{method}_initial.dat')
            np.testing.assert_allclose(rows,frozen,rtol=1e-12,atol=1e-12)
            q=rows[:,1]*rows[:,2] if method=='sv' else rows[:,2]
            np.testing.assert_allclose(q,.043*2.737,rtol=1e-12)
            self.assertTrue((rows[:,1]<ss.critical(.043*2.737)).all())

    def test_edited_case_is_not_silently_accepted(self):
        baseline=lab.load_case()
        for key,value in [('CFL',True),('CFL',float('nan')),('intervals',184),('intervals',92.0),('kappa',.04)]:
            c=deepcopy(baseline);c['custom'][key]=value
            with self.assertRaises(ValueError):lab.validate_case(c)
        c=deepcopy(baseline);c['custom']['boussinesq']=True
        with self.assertRaises(ValueError):lab.validate_case(c)
        self.assertEqual(lab.load_case(),baseline)

    def test_observation_domain_and_units(self):
        p=lab.load_case()['physical']
        obs=lab.read_json(lab.ROOT/'data/test4_observations.json')['points']
        scored=[a for a in obs if p['x0_m']<=a['x_reported_m']<=p['xout_m']]
        self.assertEqual(len(obs),14);self.assertEqual(len(scored),13)
        self.assertAlmostEqual(p['hin_m']*p['uin_m_s']*p['width_m'],.05413786)

if __name__=='__main__':unittest.main()
