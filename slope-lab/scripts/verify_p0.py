"""Recompute P0 against independent, frozen S3/SS references shipped in kit."""
from pathlib import Path
import argparse
import json
import platform
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import lab
from postprocess import plot_compare


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--fine',action='store_true')
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    c=lab.load_case();checks=[];folders=[]
    for method,N,refname in [('ss',1024,'ss_P0_dx0025.csv'),('sv',512,'sv_N512_T300.dat'),('b',1024,'b_N1024.dat')]+([('b',2048,'b_N2048.dat')] if args.fine else []):
        folder=lab.run_method(c,method,N=N,dx=.025,initial='uniform',output=args.output/'runs');folders.append(folder)
        a=np.genfromtxt(folder/'profile.csv',names=True,delimiter=',',dtype=None,encoding='utf8')
        if method=='ss':
            ref=np.genfromtxt(ROOT/'reference'/refname,names=True,delimiter=',');xx=ref['x_m'];hh=ref['h_m'];tol=1e-8
        else:
            ref=np.loadtxt(ROOT/'reference'/refname);xx=ref[:,0];hh=ref[:,1];tol=2e-4 if method=='sv' else 1e-5
        assert len(xx)==len(a) and np.max(abs(xx-a['x_m']))<1e-8
        err=float(np.max(abs(hh-a['h_m'])));meta=lab.read(folder/'metadata.json')
        checks.append(dict(method=method,N=N if method!='ss' else None,run=str(folder.relative_to(args.output)),
                           reference=refname,reference_sha256=lab.sha(ROOT/'reference'/refname),max_depth_difference_m=err,
                           tolerance_m=tol,passed=err<=tol,wall_seconds=meta['wall_seconds'],steady_screen=meta['steady_screen'],
                           summary=meta['summary'],checks=meta['checks']))
        lab.save(args.output/'acceptance.json',dict(passed=all(r['passed'] for r in checks),checks=checks,
                 platform=platform.platform(),python=sys.version,HEC_RAS_engine_verified=False,
                 scope='P0 implementation reproduction, not physical validation or B grid convergence.'))
        assert err<=tol,(method,N,err)
    plot_compare(folders,args.output/'figures')
    print('P0 reproduction passed:',args.output)


if __name__=='__main__':main()
