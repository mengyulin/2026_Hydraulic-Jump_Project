"""Standalone slope-channel teaching interface. Never modifies frozen references.

Each run has a unique folder; failed integrations and their inputs/logs remain.
B uses native coarse startup, portable fixed-point continuation, then native
time stepping. That continuation verifies a root, not general transient physics.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid

from case_tools import ROOT, load_case, resolve, bed_z, standard_step


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def build():
    stamp=ROOT/'.tools/installation.json'
    if not stamp.exists():raise RuntimeError('First run bash setup.sh; see docs/start.html.')
    install=read(stamp);qcc=Path(install['identity']['qcc'])
    if install['identity']['kit_directory']!=str(ROOT) or not qcc.is_file():
        raise RuntimeError('Folder moved or compiler unavailable. Run bash setup.sh again.')
    dest=ROOT/'.tools/solvers';dest.mkdir(parents=True,exist_ok=True)
    names=['sv_case.c','sv_instrumented.h','bed.h','custom_solver.c','bridge.c']
    hashes={name:sha(ROOT/'core'/name) for name in names}
    stamp=dest/'build.json';extension='.dylib' if platform.system()=='Darwin' else '.so'
    if stamp.exists():
        prior=read(stamp)
        if prior['source_sha256']==hashes and prior['installation']==install and all(
            (dest/name).is_file() and sha(dest/name)==h for name,h in prior['binary_sha256'].items()):
            return dest,extension
    for name in names:shutil.copy2(ROOT/'core'/name,dest/name)
    env=os.environ.copy();env['BASILISK']=str(qcc.parent)
    for key in ['CC','CC99','CPP99','CFLAGS','LDFLAGS']:env.pop(key,None)
    commands=[[str(qcc),'-O2','-Wall','-disable-dimensions','-DMODEL_GN=0','sv_case.c','-o','sv','-lm'],
              [str(qcc),'-O2','-Wall','-disable-dimensions','custom_solver.c','-o','b','-lm'],
              ['cc','-O2','-shared','-fPIC','bridge.c','-o','bridge'+extension,'-lm']]
    with (dest/'build.log').open('w') as log:
        for cmd in commands:
            log.write(' '.join(cmd)+'\n');log.flush()
            subprocess.run(cmd,cwd=dest,env=env,stdout=log,stderr=log,check=True,timeout=180)
    save(stamp,dict(source_sha256=hashes,installation=install,commands=commands,
                   binary_sha256={n:sha(dest/n) for n in ['sv','b','bridge'+extension]},
                   compiler=subprocess.check_output(['cc','--version'],text=True)))
    return dest,extension


def diagnostics(path):
    lines=Path(path).read_text().splitlines()
    return dict(zip(lines[0].lstrip('# ').split(),map(float,lines[1].split())))


def native(folder,c,method,n,cfl,initial,end,mean_start,lam=1.,bon=1,kap=.03,timeout=1800):
    import numpy as np
    folder.mkdir(parents=True,exist_ok=False)
    binaries,_=build()
    np.savetxt(folder/'initial.dat',initial,fmt='%.17g')
    (folder/'bed.dat').write_text(' '.join(map(str,c['bed_native']))+'\n')
    if method=='sv':
        args=[c['hin_m'],c['q_m2s']/c['hin_m'],c['hout_m'],c['n'],0.,c['length_m'],
              n,end,mean_start,cfl,1,0,'initial.dat','bed.dat']
    else:
        values=[n,bon,0,1,c['hin_m'],c['q_m2s']/c['hin_m'],c['hout_m'],c['n'],0.,c['length_m'],
                cfl,kap,end,mean_start,1.]
        (folder/'config.dat').write_text(' '.join(map(str,values))+'\n')
        (folder/'options.dat').write_text('0 2\n')
        (folder/'dissipation.dat').write_text(f'{lam:.17g}\n')
        args=['config.dat','initial.dat','options.dat','bed.dat']
    cmd=[str(binaries/method)]+list(map(str,args));start=time.monotonic()
    save(folder/'execution.json',dict(command=cmd,status='running',binary_sha256=sha(binaries/method)))
    try:
        with (folder/'stdout.log').open('w') as out,(folder/'stderr.log').open('w') as err:
            subprocess.run(cmd,cwd=folder,stdout=out,stderr=err,check=True,timeout=timeout)
        data=np.loadtxt(folder/'profile.dat',ndmin=2)
        d=diagnostics(folder/('verification.dat' if method=='sv' else 'budget.dat'))
        if method=='sv':
            done=re.search(r'Completed t=([0-9.eE+-]+)',(folder/'stderr.log').read_text())
            passed=done is not None and abs(float(done[1])-end)<1e-7 and abs(d['mean_weight']-(end-mean_start))<1e-7
            passed=passed and d['max_mass_error']<1e-7 and d['max_momentum_error']<1e-7 and d['max_inlet_error']<1e-8
        else:
            passed=d['rejected']==0 and abs(d['actual_time']-end)<1e-8 and abs(d['weight']-(end-mean_start))<1e-7
            passed=passed and d['mass_error_max']<1e-7 and d['momentum_error_max']<1e-7
        passed=passed and d['min_stage_h']>0 and np.isfinite(data).all() and np.isfinite(list(d.values())).all()
        if not passed:raise RuntimeError(f'Native {method} integrity check failed: {d}')
        save(folder/'execution.json',dict(command=cmd,status='passed_integrity',wall_seconds=time.monotonic()-start,
                                         binary_sha256=sha(binaries/method),diagnostics=d))
        return data,d
    except Exception as error:
        save(folder/'execution.json',dict(command=cmd,status='failed',error=str(error),wall_seconds=time.monotonic()-start))
        raise


def initial_state(c,n,method,kind='uniform',center=None):
    import numpy as np
    dx=c['length_m']/n
    x=(np.arange(n)+.5)*dx if method=='sv' else np.linspace(0,c['length_m'],n+1)
    if kind=='uniform':h=np.full_like(x,c['hin_m'])
    elif kind=='linear':h=c['hin_m']+(c['hout_m']-c['hin_m'])*x/c['length_m']
    elif kind=='tanh':
        xc=c['transition_center_m'] if center is None else center
        h=c['hin_m']+(c['hout_m']-c['hin_m'])*.5*(1+np.tanh((x-xc)/.5))
    else:raise ValueError('initial must be uniform, linear or tanh.')
    return np.column_stack([x,h,c['q_m2s']/h if method=='sv' else np.full_like(h,c['q_m2s'])])


def solve_b(folder,c,n,cfl,lam,bon,kap,initial,center,seed):
    import numpy as np
    from b_operator import Operator
    binaries,extension=build()
    bedfile=folder/'bed.dat';bedfile.write_text(' '.join(map(str,c['bed_native']))+'\n')
    if seed is not None:
        # Explicit warm start; recorded, never silently use frozen references.
        a=np.loadtxt(seed,ndmin=2)
        if a.shape[1]!=3 or not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0) or np.any(a[:,1]<=0):
            raise ValueError('seed must be state.dat with columns x,h,q and positive depths.')
        if abs(a[0,0])>1e-8 or abs(a[-1,0]-c['length_m'])>1e-8:
            raise ValueError('Seed domain differs from the case.')
        levels=[n]
    else:
        start_n=min(128,n)
        a,_=native(folder/'bootstrap',c,'b',start_n,cfl,
                   initial_state(c,start_n,'b',initial,center),300.,200.,lam,bon,kap)
        a=a[:,:3];levels=[];k=start_n
        while k<n:levels.append(k);k*=2
        levels.append(n)
    logs=[]
    for count in levels:
        x=np.linspace(0,c['length_m'],count+1)
        u=np.column_stack([np.interp(x,a[:,0],a[:,1]),np.interp(x,a[:,0],a[:,2])]).ravel()
        op=Operator(binaries/('bridge'+extension),c,count,bon,lam,kap,cfl,bedfile)
        u,log,passed=op.newton(u)
        logs.append(dict(N=count,passed=passed,iterations=log))
        a=np.column_stack([x,u.reshape(-1,2)])
        np.savetxt(folder/f'root_N{count}.dat',a,header='x h q',fmt='%.17g')
        save(folder/'newton.json',dict(levels=logs,passed=passed,seed=None if seed is None else str(seed),
                                     seed_sha256=None if seed is None else sha(seed)))
        if not passed:raise RuntimeError(f'B fixed-point solve failed at N={count}; retain logs and do not call this convergence.')
    r=op.residual(u,op.dt(u))
    return a,dict(levels=logs,h_residual_ms=float(abs(r[::2]).max()),q_residual_m2s2=float(abs(r[1::2]).max()),native_dt=op.dt(u))


def run_method(case,method,N=1024,dx=.125,CFL=None,lam=1.,B=1,kappa=.03,
               initial='tanh',center=None,end=300.,mean_start=200.,continuation=.1,
               seed=None,output=None):
    import numpy as np
    from postprocess import summarize,write_profile
    c=resolve(case)
    if method not in ('ss','sv','b'):raise ValueError('method: ss, sv or b')
    if type(N) is not int or N<32 or N>8192 or N&(N-1):raise ValueError('N must be a power of two from32 to8192.')
    if B not in (0,1) or type(B) is bool:raise ValueError('B must be integer0 or1.')
    if not math.isfinite(lam) or not 0<lam<=4 or not math.isfinite(kappa) or kappa<0:raise ValueError('Invalid dissipation settings.')
    CFL=(.4 if method=='sv' else .1) if CFL is None else CFL
    if not math.isfinite(CFL) or not 0<CFL<=.65:raise ValueError('CFL must lie in (0,0.65].')
    if not all(math.isfinite(v) for v in [end,mean_start,continuation]) or not end>mean_start>=0 or continuation<=0:
        raise ValueError('Require end>mean_start>=0 and positive continuation duration.')
    if initial not in ('uniform','linear','tanh'):raise ValueError('Unknown initialization.')
    if center is not None and (not math.isfinite(center) or not 0<center<c['length_m']):raise ValueError('Invalid initial center.')
    safeid=re.sub(r'[^A-Za-z0-9_-]','_',str(c['id']))
    folder=Path(output or ROOT/'runs')/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+safeid+'_'+method+'_'+uuid.uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    config=dict(N=N,dx_requested_m=dx,CFL=CFL,lambda_rusanov=lam,B=B,kappa=kappa,
                initial=initial,center=center,end=end,mean_start=mean_start,continuation_tau=continuation,
                seed=None if seed is None else str(Path(seed).resolve()))
    meta=dict(case=c,method=method,numerics=config,status='running',python=sys.version,
              platform=platform.platform(),interface_sha256=sha(__file__),start_utc=datetime.now(timezone.utc).isoformat())
    save(folder/'case.json',c);save(folder/'metadata.json',meta)
    start=time.monotonic();print(f"Running {c['id']} {method}: {folder.name}",flush=True)
    try:
        ref,ssrows=standard_step(c,.025)
        save(folder/'ss_reference.json',ref['summary'])
        if method=='ss':
            result,rows=standard_step(c,dx);save(folder/'solution.json',result)
            a=np.array(rows);x,z,h=a.T;u=c['q_m2s']/h
            detail=dict(jump=result['summary']['jumps'][0],energy_residual_m=result['summary']['maximum_energy_residual_m'])
            state_kind='steady';integrity=True
        elif method=='sv':
            a,d=native(folder/'native',c,'sv',N,CFL,initial_state(c,N,'sv',initial,center),end,mean_start)
            x,h,u=a[:,0],a[:,1],a[:,3];z=np.array([bed_z(v,c) for v in x]);state_kind='time_mean'
            detail=dict(native=d,block_depth_change_m=float(abs(a[:,4]-a[:,5]).max()),max_depth_sd_m=float(a[:,2].max()),
                        steady_screen=bool(abs(a[:,4]-a[:,5]).max()<1e-4 and a[:,2].max()<1e-4))
            np.savetxt(folder/'state.dat',a[:,[0,6,8]],header='x h_final q_final',fmt='%.17g');integrity=True
        else:
            root,detail=solve_b(folder,c,N,CFL,lam,B,kappa,initial,center,None if seed is None else Path(seed).resolve())
            a,d=native(folder/'native',c,'b',N,CFL,root,continuation,continuation/2,lam,B,kappa)
            x,h=a[:,0],a[:,1];u=a[:,2]/h;z=np.array([bed_z(v,c) for v in x]);state_kind='fixed_point_native_endpoint'
            change=float(abs(h-root[:,1]).max())
            detail|=dict(native=d,root_endpoint_difference_m=change,max_depth_sd_m=float(a[:,5].max()),
                         block_depth_change_m=float(abs(a[:,6]-a[:,7]).max()),
                         steady_screen=bool(change<1e-5 and abs(a[:,6]-a[:,7]).max()<1e-4),
                         time_note='Relaxation time; short root maintenance, not arbitrary-start transient convergence.')
            np.savetxt(folder/'state.dat',a[:,:3],header='x h_final q_final',fmt='%.17g');integrity=change<1e-5
            if not integrity:raise RuntimeError('Native B continuation does not maintain the computed root.')
        write_profile(folder/'profile.csv',x,z,h,u,c,state_kind)
        features=summarize(x,h,c,ref['summary']['jumps'][0],method)
        save(folder/'summary.json',features|dict(method=method,state_kind=state_kind,checks=detail))
        meta|=dict(status='passed_integrity',integrity=integrity,wall_seconds=time.monotonic()-start,
                    steady_screen=detail.get('steady_screen',True),summary=features,
                    model_validation=False,checks=detail)
        if method!='ss':meta['build']=read(ROOT/'.tools/solvers/build.json')
        meta['outputs_sha256']={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file() and p.name!='metadata.json'}
        save(folder/'metadata.json',meta)
        print('Completed; integrity passed. Wave convergence is a separate question.',flush=True)
        return folder
    except Exception as error:
        meta|=dict(status='failed',error=str(error),wall_seconds=time.monotonic()-start)
        save(folder/'metadata.json',meta);raise


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('build');sub.add_parser('cases')
    r=sub.add_parser('run');r.add_argument('--case',default='P0');r.add_argument('--method',choices=['ss','sv','b'],required=True)
    r.add_argument('--N',type=int,default=1024);r.add_argument('--dx',type=float,default=.125);r.add_argument('--cfl',type=float)
    r.add_argument('--lam',type=float,default=1.);r.add_argument('--B',type=int,default=1);r.add_argument('--kappa',type=float,default=.03)
    r.add_argument('--initial',choices=['uniform','linear','tanh'],default='tanh');r.add_argument('--center',type=float)
    r.add_argument('--end',type=float,default=300.);r.add_argument('--mean-start',type=float,default=200.)
    r.add_argument('--continuation',type=float,default=.1);r.add_argument('--seed',type=Path);r.add_argument('--output',type=Path)
    h=sub.add_parser('hec');h.add_argument('--case',default='P0');h.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('plot');p.add_argument('folders',nargs='+',type=Path);p.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    if a.command=='build':print(build()[0])
    elif a.command=='cases':
        for name in ['P0']+[f'P{i}{s}' for i in range(1,6) for s in 'LH']:
            c=load_case(name);print(name,'Fr=',round(c['Fr_in'],4),'n=',c['n'],'tailwater=',round(c['hout_m'],6))
    elif a.command=='run':
        print(run_method(load_case(a.case),a.method,a.N,a.dx,a.cfl,a.lam,a.B,a.kappa,a.initial,a.center,
                         a.end,a.mean_start,a.continuation,a.seed,a.output))
    elif a.command=='hec':
        from hec_tools import export_project
        print(export_project(load_case(a.case),a.output))
    elif a.command=='plot':
        from postprocess import plot_compare
        plot_compare(a.folders,a.output)


if __name__=='__main__':main()
