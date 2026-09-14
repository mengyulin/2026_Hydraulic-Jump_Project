"""GC1991 Test 4: one interface for three independently defined methods.

Student entry points: load_case(), run_method(), run_all(), plot_compare().
Run folders contain actual generated inputs, copied numerical sources and logs.
All depths/coordinates are metres; q is discharge PER UNIT WIDTH (m2/s).
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

from core import standard_step as ss

ROOT = Path(__file__).resolve().parent
METHODS = ('standard_step', 'sv', 'custom')
LABELS = {'standard_step': 'Standard step (zero-length jump)',
          'sv': 'Explicit Saint-Venant (N=512)',
          'custom': 'Custom steady B correction (M=92, B on)'}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_case(name='test4'):
    """Return a fresh configuration. Version 1 exposes the fixed accepted case."""
    if name != 'test4':
        raise ValueError('This teaching release provides test4 only.')
    case = read_json(ROOT/'cases/test4.json')
    validate_case(case)
    return deepcopy(case)


def validate_case(case):
    # Reference inputs are independent of the active case. A typo or an edited
    # setting must not silently redefine the acceptance target.
    baseline = read_json(ROOT/'reference/expected.json')['case']
    if case != baseline:
        raise ValueError('Version 1 runs the fixed Test 4 baseline. Restore cases/test4.json '
                         'from reference/expected.json (the case object); see docs/instructor.md.')
    def same_types(a, b):
        if isinstance(b, dict):
            return isinstance(a, dict) and a.keys() == b.keys() and all(same_types(a[k], b[k]) for k in b)
        if type(b) is int:
            return type(a) is int
        if isinstance(b, float):
            return type(a) in (int, float) and math.isfinite(a)
        return type(a) is type(b)
    if not same_types(case, baseline):
        raise ValueError('Case numbers must be finite numbers, not booleans or strings.')


def _new_run(method):
    folder = ROOT/'runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+method+'_'+uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def initial_rows(case, method):
    """Supercritical GVF throughout the domain: no jump is pre-positioned.

    SV reads cell-centred x,h,u; the custom solver reads nodal x,h,q.
    RK4 substeps preserve the archived initialization procedure for each grid.
    """
    p = case['physical']; q = p['hin_m']*p['uin_m_s']
    x0, xout = p['x0_m'], p['xout_m']; h = p['hin_m']; current = x0
    count = case['sv']['cells'] if method == 'sv' else case['custom']['intervals']
    dx = (xout-x0)/count
    def rhs(y):
        radius = p['width_m']*y/(p['width_m']+2*y)
        sf = (p['manning_n']*q/y/radius**(2/3))**2
        return sf/(q*q/(p['gravity_m_s2']*y**3)-1)
    for j in range(count if method == 'sv' else count+1):
        x = x0+(j+.5)*dx if method == 'sv' else x0+j*dx
        substeps = 8 if method == 'sv' else max(8, math.ceil((x-current)/.005))
        step = (x-current)/substeps
        for _ in range(substeps):
            a=rhs(h); b=rhs(h+step*a/2); c=rhs(h+step*b/2); d=rhs(h+step*c)
            h += step*(a+2*b+2*c+d)/6
        if not 0 < h < ss.critical(q):
            raise ValueError('GVF initializer left the supercritical branch.')
        current = x
        yield x, h, q/h if method == 'sv' else q


def _compiler():
    stamp = ROOT/'.tools/installation.json'
    if not stamp.exists():
        raise RuntimeError('Run bash setup.sh first (or python scripts/setup_basilisk.py).')
    installation = read_json(stamp)
    qcc = Path(installation['identity']['qcc'])
    if installation['identity']['kit_directory'] != str(ROOT) or not qcc.is_file():
        raise RuntimeError('This folder was moved or the compiler is missing. Run bash setup.sh again.')
    env = os.environ.copy(); env['BASILISK'] = str(qcc.parent)
    for key in ('CC99','CPP99','CFLAGS','LDFLAGS','CC'):
        env.pop(key, None)
    return qcc, env, installation


def _diagnostics(path):
    lines = Path(path).read_text().splitlines()
    return dict(zip(lines[0].lstrip('# ').split(), map(float, lines[1].split())))


def _c_run(case, method, folder, meta):
    qcc, env, installation = _compiler()
    meta['basilisk'] = installation
    names = ['sv_case.c','sv_instrumented.h'] if method=='sv' else ['custom_solver.c']
    for name in names:
        shutil.copyfile(ROOT/'core'/name, folder/name)
    source = names[0]
    command = [str(qcc), '-O2', '-Wall', '-disable-dimensions']
    if method == 'sv': command += ['-DMODEL_GN=0']
    command += [source, '-o', 'solver', '-lm']
    start = time.perf_counter()
    with (folder/'build.log').open('w') as log:
        subprocess.run(command, cwd=folder, env=env, stdout=log, stderr=log, check=True, timeout=120)
    meta['compile_seconds'] = time.perf_counter()-start
    meta['build_command'] = command
    meta['source_sha256'] = {name:sha(folder/name) for name in names}
    meta['binary_sha256'] = sha(folder/'solver')
    with (folder/'initial.dat').open('w') as out:
        for row in initial_rows(case,method): out.write(' '.join(format(v,'.17g') for v in row)+'\n')
    p=case['physical']; m=case[method]
    if method == 'sv':
        args=[p['hin_m'],p['uin_m_s'],p['hout_m'],p['manning_n'],p['x0_m'],p['xout_m'],
              m['cells'],m['end_s'],m['mean_start_s'],m['CFL'],m['boundary_kind'],0,'initial.dat']
    else:
        config=[m['intervals'],m['boussinesq'],m['periodic'],m['scheme'],p['hin_m'],p['uin_m_s'],p['hout_m'],
                p['manning_n'],p['x0_m'],p['xout_m'],m['CFL'],m['kappa'],m['end_s'],m['mean_start_s'],m['max_dt_s']]
        (folder/'config.dat').write_text(' '.join(format(v,'.17g') for v in config)+'\n')
        (folder/'options.dat').write_text(f"{m['source_mode']} {m['strip_mode']}\n")
        args=['config.dat','initial.dat','options.dat']
    command=['./solver']+list(map(str,args)); meta['run_command']=command
    start=time.perf_counter()
    with (folder/'stdout.log').open('w') as out, (folder/'stderr.log').open('w') as err:
        subprocess.run(command,cwd=folder,env=env,stdout=out,stderr=err,check=True,timeout=300)
    meta['flow_seconds']=time.perf_counter()-start
    diagnostics=_diagnostics(folder/('verification.dat' if method=='sv' else 'budget.dat'))
    if not all(math.isfinite(v) for v in diagnostics.values()): raise RuntimeError('Nonfinite solver diagnostic.')
    meta['diagnostics']=diagnostics
    if method=='sv':
        completed=re.search(r'Completed t=([0-9.eE+-]+)',(folder/'stderr.log').read_text())
        checks = [completed is not None and abs(float(completed[1])-m['end_s'])<1e-6,
                  abs(diagnostics['mean_weight']-(m['end_s']-m['mean_start_s']))<1e-6,
                  diagnostics['max_mass_error']<1e-7,diagnostics['max_momentum_error']<1e-7,
                  diagnostics['max_inlet_error']<1e-8,diagnostics['min_stage_h']>0]
    else:
        checks = [diagnostics['rejected']==0,abs(diagnostics['actual_time']-m['end_s'])<1e-6,
                  abs(diagnostics['weight']-(m['end_s']-m['mean_start_s']))<1e-6,
                  diagnostics['mass_error_max']<1e-7,diagnostics['momentum_error_max']<1e-7,
                  diagnostics['min_stage_h']>0]
    if not all(checks): raise RuntimeError('Incomplete integration or failed budget/depth checks; see metadata.json.')


def profile(result):
    """Return x,h. The standard-step discontinuity retains two depths at x_jump."""
    import numpy as np
    folder=Path(result['folder']); method=result['method']
    a=np.loadtxt(folder/'profile.dat',ndmin=2)
    return a[:,0],a[:,1] if method!='custom' else a[:,3]


def _rmse(result):
    import numpy as np
    x,h=profile(result)
    obs=read_json(ROOT/'data/test4_observations.json')['points']
    p=result['case']['physical']
    obs=[a for a in obs if p['x0_m']<=a['x_reported_m']<=p['xout_m']]
    xx=np.array([a['x_reported_m'] for a in obs]); hh=np.array([a['h_m'] for a in obs])
    if result['method']=='standard_step':
        s=read_json(Path(result['folder'])/'solution.json'); xj=s['jump']['x_m']
        # Evaluate the appropriate GVF branch at each observation; never smooth
        # the idealized zero-length jump across neighbouring grid points.
        model=np.where(xx<xj,np.interp(xx,s['x'][:len(s['h_super'])],s['h_super']),np.interp(xx,s['x'],s['h_sub']))
    else: model=np.interp(xx,x,h)
    return float(np.sqrt(np.mean((model-hh)**2))),len(obs)


def check_result(result):
    """Check installation reproduction against frozen reference profiles.

    The 0.2-mm numerical tolerance is not a claim about experimental uncertainty.
    No longer integration or finer-grid run is requested when a check passes.
    """
    import numpy as np
    x,h=profile(result); method=result['method']; expected=read_json(ROOT/'reference/expected.json')
    if not np.isfinite(x).all() or not np.isfinite(h).all() or not (h>0).all(): raise RuntimeError('Invalid profile.')
    if np.any(np.diff(x)<0) or (method!='standard_step' and np.any(np.diff(x)<=0)): raise RuntimeError('Invalid coordinates.')
    checks={'finite_positive_profile':True}
    if method=='standard_step':
        sol=read_json(Path(result['folder'])/'solution.json'); ref=read_json(ROOT/'reference/standard_step.json')
        error=abs(sol['jump']['x_m']-ref['jump']['x_m'])
        if error>expected['standard_step_jump_tolerance_m']: raise RuntimeError('Standard-step jump reproduction failed.')
        checks['jump_difference_m']=error
    else:
        ref=np.loadtxt(ROOT/f'reference/{method}_profile.dat')
        if len(x)!=len(ref) or np.max(abs(x-ref[:,0]))>1e-8: raise RuntimeError('Reference grid mismatch.')
        error=float(np.max(abs(h-ref[:,1 if method=='sv' else 3])))
        if error>expected['profile_max_abs_tolerance_m']: raise RuntimeError(f'{method} reference depth error {error:g} m.')
        checks['max_reference_depth_difference_m']=error
    checks['passed']=True
    return checks


def run_method(case, method):
    """Execute a real calculation, preserving any failed run and its logs."""
    validate_case(case)
    if method not in METHODS: raise ValueError(f'Method must be one of {METHODS}.')
    folder=_new_run(method)
    result={'method':method,'folder':str(folder),'case':deepcopy(case)}
    meta={'method':method,'case':case,'status':'running','python':sys.version,
          'interface_sha256':sha(ROOT/'lab.py'),'observations_sha256':sha(ROOT/'data/test4_observations.json')}
    write_json(folder/'case.json',case);write_json(folder/'metadata.json',meta)
    print(f'Running {method} ...',flush=True)
    try:
        if method=='standard_step':
            p=case['physical'];start=time.perf_counter()
            s=ss.solve(p['hin_m']*p['uin_m_s'],p['hin_m'],p['hout_m'],p['manning_n'],
                       p['width_m'],p['x0_m'],p['xout_m'],case[method]['dx_m'])
            meta['flow_seconds']=time.perf_counter()-start
            if s['jump'] is None: raise RuntimeError('No bracketed zero-length jump.')
            write_json(folder/'solution.json',s)
            shutil.copyfile(ROOT/'core/standard_step.py',folder/'standard_step.py')
            meta['source_sha256']={'standard_step.py':sha(folder/'standard_step.py')}
            xj=s['jump']['x_m']
            rows=[(x,h) for x,h in zip(s['x'],s['h_super']) if x<xj]
            rows += [(xj,s['jump']['h1_m']),(xj,s['jump']['h2_m'])]
            rows += [(x,h) for x,h in zip(s['x'],s['h_sub']) if x>xj]
            with (folder/'profile.dat').open('w') as out:
                out.write('# x h (two rows at x_jump preserve a zero-length jump)\n')
                for x,h in rows: out.write(f'{x:.17g} {h:.17g}\n')
        else: _c_run(case,method,folder,meta)
        meta['checks']=check_result(result)
        meta['rmse_m'],meta['observation_count']=_rmse(result)
        meta['status']='passed'
        meta['profile_sha256']=sha(folder/'profile.dat')
        print(f"{method}: RMSE {1000*meta['rmse_m']:.2f} mm; calculation {meta['flow_seconds']:.2f} s; reproduction passed.",flush=True)
    except Exception as error:
        meta['status']='failed';meta['error']=str(error)
        raise RuntimeError(f'{method} failed; inspect {folder}/metadata.json and logs. {error}') from error
    finally:
        write_json(folder/'metadata.json',meta)
    return result|{'summary':meta}


def run_all(case=None):
    case=load_case() if case is None else case
    return {method:run_method(case,method) for method in METHODS}


def plot_compare(results, xlim=(.25,4.5), save=True):
    """Draw actual fresh results and unshifted Table 2 observations."""
    import matplotlib.pyplot as plt
    if set(results)!=set(METHODS): raise ValueError('Run all three methods before the comparison.')
    fig,ax=plt.subplots(figsize=(9,4.9),layout='constrained')
    colours={'standard_step':'#64748b','sv':'#2563eb','custom':'#cf4a24'}
    for method in METHODS:
        result=results[method];x,h=profile(result);rmse=result['summary']['rmse_m']
        ax.plot(x,h,label=f'{LABELS[method]} | RMSE {rmse*1000:.2f} mm',
                color=colours[method],lw=1.9,ls='--' if method=='standard_step' else '-')
    points=read_json(ROOT/'data/test4_observations.json')['points']
    ax.scatter([p['x_reported_m'] for p in points[1:]],[p['h_m'] for p in points[1:]],
               s=32,facecolors='white',edgecolors='#111827',linewidths=1.3,zorder=5,label='GC1991 Test 4 (13 scored stations)')
    ax.scatter([points[0]['x_reported_m']],[points[0]['h_m']],marker='x',c='#111827',s=32,zorder=5,label='x = 0.30 m (outside domain, not scored)')
    ax.axvline(.305,color='#94a3b8',lw=.8,ls=':')
    ax.set(xlim=xlim,ylim=(.025,.25),xlabel='Downstream coordinate x (m)',ylabel='Water depth h = surface elevation (m)',
           title='GC1991 Test 4 | same hydraulic inputs, fixed teaching settings')
    ax.grid(alpha=.18);ax.legend(fontsize=8,loc='lower right')
    fig.get_layout_engine().set(rect=(0,.06,1,.94))
    fig.text(.5,.015,'Flat bed; unshifted coordinates. Custom jump smoothing depends on the chosen grid.',ha='center',fontsize=9)
    if save:
        folder=_new_run('comparison')
        fig.savefig(folder/'comparison.png',dpi=180)
        fig.savefig(folder/'comparison.pdf')
        write_json(folder/'comparison.json',{'runs':{k:os.path.relpath(v['folder'],folder) for k,v in results.items()},
                                            'rmse_mm':{k:v['summary']['rmse_m']*1000 for k,v in results.items()}})
        print('Comparison saved:',folder,flush=True)
    return fig


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('method',choices=(*METHODS,'all'),nargs='?',default='all')
    args=parser.parse_args()
    try:
        if args.method=='all': plot_compare(run_all())
        else: run_method(load_case(),args.method)
    except (RuntimeError,ValueError,OSError) as error:
        print(error,file=sys.stderr);return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
