"""Coarse execution coverage of case families and exposed controls, not convergence."""
from pathlib import Path
import argparse
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import lab


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--N',type=int,default=512);a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);rows=[]
    jobs=[(f'P{i}{suffix}',m,dict(N=a.N)) for i in range(1,6) for suffix in 'LH' for m in ['sv','b']]
    jobs += [('P0','sv',dict(N=512,CFL=.2)),('P0','sv',dict(N=512,initial='tanh',center=16)),
             ('P0','b',dict(N=512,CFL=.05)),('P0','b',dict(N=512,lam=2)),('P0','b',dict(N=512,B=0))]
    for case,method,settings in jobs:
        try:
            p=lab.run_method(lab.load_case(case),method,output=a.output/'runs',**settings)
            m=lab.read(p/'metadata.json');row=dict(case=case,method=method,settings=settings,
                passed_integrity=True,steady_screen=m['steady_screen'],run=str(p.relative_to(a.output)),
                wall_seconds=m['wall_seconds'])
        except Exception as error:
            row=dict(case=case,method=method,settings=settings,passed_integrity=False,error=str(error))
        rows.append(row)
        lab.save(a.output/'interface_checks.json',dict(passed=all(r['passed_integrity'] for r in rows),checks=rows,
             scope='Coarse execution and parameter wiring only; not production-grid or model-physics validation.'))
    if not all(r['passed_integrity'] for r in rows):raise RuntimeError('Some interface checks failed; see retained logs.')
    print('All interface execution checks passed.')


if __name__=='__main__':main()
