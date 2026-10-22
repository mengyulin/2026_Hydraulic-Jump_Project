"""One physical case definition for SS, SV, B and HEC-RAS; SI throughout."""
from copy import deepcopy
import json
import math
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'core'))
import variable_bed_standard_step as ss


def load_case(name='P0'):
    if name not in ['P0']+[f'P{i}{s}' for i in range(1,6) for s in 'LH']:
        raise ValueError('Choose P0 or P1L/P1H ... P5L/P5H.')
    return resolve(json.loads((ROOT/'cases'/f'{name}.json').read_text()))


def resolve(case):
    c=deepcopy(case)
    if not isinstance(c.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',c['id']):
        raise ValueError('Case id must contain 1–40 ASCII letters, digits, underscores or hyphens.')
    for key in ['length_m','width_m','Q_m3s','g_m_s2','n','S1','S2',
                'transition_center_m','transition_length_m','hout_m','z_out_m','Cc','Ce']:
        v=c[key]
        if type(v) not in (int,float) or not math.isfinite(v):
            raise ValueError(f'{key} must be a finite number.')
    if c['width_m']!=.46 or c['g_m_s2']!=9.81:
        raise ValueError('The preserved PDE cores require width=0.46 m and g=9.81 m/s².')
    if c['Cc']!=0 or c['Ce']!=0:
        raise ValueError('This matched teaching matrix fixes Cc=Ce=0.')
    if min(c[k] for k in ['length_m','Q_m3s','n','S1','S2','transition_length_m','hout_m'])<=0:
        raise ValueError('Require positive geometry, flow, roughness, slopes and depths.')
    a=c['transition_center_m']-c['transition_length_m']/2
    b=c['transition_center_m']+c['transition_length_m']/2
    if not 0<a<b<c['length_m']:
        raise ValueError('The smooth transition must be inside the domain.')
    c['q_m2s']=c['Q_m3s']/c['width_m']
    flow=ss.Flow(c['q_m2s'],c['width_m'],c['n'])
    c['hin_m']=flow.normal_depth(c['S1'])
    c['yc_m']=flow.yc;c['Fr_in']=flow.fr(c['hin_m']);c['Fr_out']=flow.fr(c['hout_m'])
    if c['Fr_in']<=1 or c['Fr_out']>=1:
        raise ValueError('This release requires a supercritical normal-depth inlet and subcritical tailwater.')
    c['bed_native']=[1,c['S1'],c['S2'],a,b,c['length_m'],c['z_out_m'],0]
    return c


def bed_z(x,c):
    a,b=c['bed_native'][3:5];s1,s2=c['S1'],c['S2'];lt=b-a
    za=c['z_out_m']+s2*(c['length_m']-b)+(s1+s2)*lt/2
    if x<=a:return za+s1*(a-x)
    if x>=b:return c['z_out_m']+s2*(c['length_m']-x)
    r=x-a
    return za-(s1+s2)*r/2-(s1-s2)*lt/(2*math.pi)*math.sin(math.pi*r/lt)


def sections(c,dx):
    if not math.isfinite(dx) or dx<=0 or dx>c['length_m']:
        raise ValueError('Invalid section spacing.')
    count=math.ceil(c['length_m']/dx)
    xs={min(round(i*dx,12),c['length_m']) for i in range(count+1)}
    xs.update(c['bed_native'][3:5])
    return [[x,bed_z(x,c)] for x in sorted(xs)]


def standard_step(c,dx=.025):
    data=dict(id=c['id'],Q_m3s=c['Q_m3s'],width_m=c['width_m'],n=c['n'],
              bed=sections(c,dx),upstream=dict(type='normal_depth',slope=c['S1']),
              downstream=dict(type='depth',depth_m=c['hout_m']),
              losses=dict(contraction=0.,expansion=0.))
    out=ss.solve(data,dx*(1+1e-9));s=out['summary']
    if s['status']!='single_momentum_match':
        raise ValueError(f"Case has no unique admissible SS jump: {s['status']}")
    j=s['jumps'][0];xj=j['x_m'];bed=ss.Bed(data['bed'])
    rows=[(r['x_m'],r['z_m'],r['depth_m']) for r in out['upstream_trace']['rows']
          if r['x_m']<xj and r['step_kind']!='critical_endpoint']
    rows += [(xj,bed.z(xj),j['y1_m']),(xj,bed.z(xj),j['y2_m'])]
    rows += [(r['x_m'],r['z_m'],r['depth_m']) for r in out['downstream_trace']['rows']
             if r['x_m']>xj and r['step_kind']!='critical_endpoint']
    rows.sort(key=lambda r:r[0])
    if rows[0][0]!=0 or rows[-1][0]!=c['length_m']:
        raise ValueError('The selected SS profile is incomplete.')
    s['nominal_dx_m']=dx
    return out,rows
