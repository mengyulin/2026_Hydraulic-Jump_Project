"""Small hydraulic/format checks. Full P0 integrations are separate."""
import json
import csv
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from case_tools import load_case,resolve,standard_step,bed_z,ss
from hec_tools import export_project,check_project,compare_export
from postprocess import crossings,summarize


class TeachingChecks(unittest.TestCase):
    def test_boundary_physics_and_family_controls(self):
        base=load_case()
        for i in range(1,6):
            for suffix in 'LH':
                c=load_case(f'P{i}{suffix}');flow=ss.Flow(c['q_m2s'],c['width_m'],c['n'])
                self.assertAlmostEqual(flow.sf(c['hin_m']),c['S1'],places=10)
                self.assertGreater(c['Fr_in'],1);self.assertLess(c['Fr_out'],1)
                self.assertEqual(bed_z(c['length_m'],c),c['z_out_m'])
                if i!=2:self.assertEqual(c['hout_m'],base['hout_m'])
                if i not in (1,5):self.assertEqual(c['hin_m'],base['hin_m'])
        self.assertGreater(load_case('P5L')['Fr_in'],base['Fr_in'])

    def test_no_silent_unsupported_core_parameters(self):
        for key,value in [('width_m',1.),('g_m_s2',10.),('Cc',.1),('n',float('nan')),('transition_length_m',0),('hout_m',.01)]:
            with self.assertRaises(ValueError):resolve(load_case()|{key:value})

    def test_all_eleven_have_positive_energy_and_conjugate_match(self):
        for name in ['P0']+[f'P{i}{s}' for i in range(1,6) for s in 'LH']:
            result,rows=standard_step(load_case(name),.125);j=result['summary']['jumps'][0]
            self.assertEqual(rows[0][0],0);self.assertEqual(rows[-1][0],30)
            self.assertTrue(all(h>0 for _,_,h in rows));self.assertGreater(j['energy_loss_m'],0)
            ratio=.5*(np.sqrt(1+8*j['Fr1']**2)-1)
            self.assertAlmostEqual(j['y2_m']/j['y1_m'],ratio,places=10)

    def test_multiple_crossings_are_not_silently_unique(self):
        x=np.arange(7,dtype=float);h=np.array([.05,.1,.2,.08,.2,.18,.17])
        self.assertEqual(len(crossings(x,h,.125)),2)
        s=summarize(x,h,load_case(),dict(x_m=2.,y1_m=.05,y2_m=.2),'b')
        self.assertIsNone(s['x50_unique_m']);self.assertIsNotNone(s['first_x50_supplementary_m'])

    def test_hec_round_trip_and_reject_mismatched_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=export_project(load_case(),Path(tmp)/'P0')
            for project in out.glob('*/*.prj'):
                self.assertTrue(check_project(project)['static_check_passed'])
            bad=Path(tmp)/'bad.csv';bad.write_text('river_station,water_surface_m,Fr,Q_m3_s\n0,.167,0.5,.0541379\n')
            with self.assertRaises(ValueError):compare_export(out/'dx0p5',bad,Path(tmp)/'rejected')

    def test_windows_csv_bom_crlf_and_hec_text_line_endings(self):
        # Synthetic transport fixture, not output from the HEC engine.
        with tempfile.TemporaryDirectory() as tmp:
            out=export_project(load_case(),Path(tmp)/'Windows exchange')
            for folder in sorted(p for p in out.iterdir() if p.is_dir()):
                project=next(folder.glob('*.prj'))
                for suffix in ('.prj','.g01','.f01','.p01'):
                    path=project.with_suffix(suffix)
                    path.write_bytes(path.read_text().replace('\n','\r\n').encode('utf-8'))
                self.assertTrue(check_project(project)['static_check_passed'])
                e=json.loads((folder/'expected.json').read_text())
                a=np.genfromtxt(folder/'paired_ss.csv',delimiter=',',names=True)
                c=e['case'];depth=a['eta_m']-a['z_m'];Q=e['Q_written_m3s']
                Fr=Q/c['width_m']/np.sqrt(c['g_m_s2']*depth**3)
                csvpath=folder/'synthetic_windows_transport_only.csv'
                with csvpath.open('w',encoding='utf-8-sig',newline='') as fh:
                    writer=csv.writer(fh,lineterminator='\r\n')
                    writer.writerow(['river_station','water_surface_m','Fr','Q_m3_s'])
                    writer.writerows(zip(a['river_station'],a['eta_m'],Fr,np.full(len(a),Q)))
                self.assertTrue(csvpath.read_bytes().startswith(b'\xef\xbb\xbf'))
                compared=compare_export(folder,csvpath,folder/'transport_check')
                self.assertLess(compared['eta_Linf_m'],1e-12)


if __name__=='__main__':unittest.main()
