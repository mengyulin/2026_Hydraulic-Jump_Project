"""Common profiles and transparent feature definitions; no curve alignment."""
import csv
import json
from pathlib import Path
import numpy as np


PROFILE_COLUMNS=['case_id','state_kind','x_m','z_m','h_m','eta_m','u_m_s','q_m2_s','Fr','H_engineering_m']


def write_profile(path,x,z,h,u,c,kind):
    with Path(path).open('w',newline='') as f:
        w=csv.writer(f);w.writerow(PROFILE_COLUMNS)
        for xx,zz,hh,uu in zip(x,z,h,u):
            w.writerow([c['id'],kind,xx,zz,hh,zz+hh,uu,hh*uu,uu/np.sqrt(c['g_m_s2']*hh),zz+hh+uu*uu/(2*c['g_m_s2'])])


def crossings(x,h,level):
    # Include a level attained exactly at a sample once, never twice.
    out=[]
    for a,b,ha,hb in zip(x[:-1],x[1:],h[:-1],h[1:]):
        if ha<level<=hb:
            out.append(float(a+(level-ha)/(hb-ha)*(b-a)))
    return out


def extrema(x,h,lo,hi,amplitude=1e-5):
    peaks=np.flatnonzero((h[1:-1]>h[:-2])&(h[1:-1]>h[2:]))+1
    troughs=np.flatnonzero((h[1:-1]<h[:-2])&(h[1:-1]<h[2:]))+1
    rows=[]
    for i in peaks:
        after=troughs[troughs>i]
        if not len(after) or not lo<x[i]<hi:continue
        j=after[0]
        if x[j]>hi or h[i]-h[j]<amplitude:continue
        def vertex(k):
            # Native PDE grids are uniform. Geometry/HEC profiles skip waves.
            yy=h[k-1:k+2];den=yy[0]-2*yy[1]+yy[2];off=.5*(yy[0]-yy[2])/den
            return float(x[k]+off*(x[1]-x[0])),float(yy[1]-.25*(yy[0]-yy[2])*off)
        xp,hp=vertex(i);xt,ht=vertex(j)
        rows.append(dict(peak_x_m=xp,peak_h_m=hp,trough_x_m=xt,trough_h_m=ht,amplitude_m=hp-ht))
    return rows


def window_mean(x,h,lo,hi):
    if lo<x[0] or hi>x[-1] or hi<=lo:return None
    xx=np.r_[lo,x[(x>lo)&(x<hi)],hi];hh=np.interp(xx,x,h)
    return float(np.trapezoid(hh,xx)/(hi-lo))


def summarize(x,h,c,jump,method):
    x=np.asarray(x);h=np.asarray(h);xj=jump['x_m'];levels={}
    for fraction in [.1,.5,.9]:
        levels[str(fraction)]=crossings(x,h,jump['y1_m']+fraction*(jump['y2_m']-jump['y1_m']))
    unique=lambda k: levels[k][0] if len(levels[k])==1 else None
    x10,x50,x90=[unique(k) for k in ['0.1','0.5','0.9']]
    lo=xj;hi=min(xj+8,c['length_m']-1)
    rows=extrema(x,h,lo,hi) if method=='b' else []
    pairs=list(zip(rows[1:],rows[2:]))
    wavelengths=[b['peak_x_m']-a['peak_x_m'] for a,b in pairs]
    decays=[(b['peak_x_m']-a['peak_x_m'])/np.log(a['amplitude_m']/b['amplitude_m'])
            for a,b in pairs if a['amplitude_m']>b['amplitude_m']]
    # A single pair is not evidence for an exponential tail.
    decay=float(np.median(decays)) if len(rows)>=4 and len(decays)==len(pairs) else None
    return dict(SS_xJ_m=xj,SS_h1_m=jump['y1_m'],SS_h2_m=jump['y2_m'],
                x50_unique_m=x50,x10_unique_m=x10,x90_unique_m=x90,all_upcrossings_m=levels,
                first_x50_supplementary_m=levels['0.5'][0] if levels['0.5'] else None,
                rise_width_unique_m=x90-x10 if x10 is not None and x90 is not None else None,
                upstream_window_m=[xj-3,xj-2],downstream_window_m=[xj+5,xj+6],
                upstream_mean_h_m=window_mean(x,h,xj-3,xj-2),downstream_mean_h_m=window_mean(x,h,xj+5,xj+6),
                wave_window_m=[lo,hi],extrema=rows,amplitude_floor_m=1e-5,
                first_peak_h_m=rows[0]['peak_h_m'] if rows else None,
                first_peak_x_m=rows[0]['peak_x_m'] if rows else None,
                tail_wavelength_m=float(np.median(wavelengths)) if wavelengths else None,
                tail_amplitude_efold_m=decay,wavelength_samples_m=wavelengths,
                note='N/A is null. First crossing is supplementary. h peaks, not eta peaks. No physical roller or breaking validation.')


def plot_compare(folders,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(12,4.4),layout='constrained')
    case=None;xj=None
    for folder in map(Path,folders):
        m=json.loads((folder/'metadata.json').read_text())
        if m['status']!='passed_integrity':raise ValueError(f'Run has not passed integrity: {folder}')
        if case is None:case=m['case']
        elif m['case']!=case:raise ValueError('Use matching physical cases; plot different cases separately.')
        a=np.genfromtxt(folder/'profile.csv',delimiter=',',names=True,dtype=None,encoding='utf8')
        n=m['numerics'];label=m['method'].upper()+(' dx='+str(n['dx_requested_m']) if m['method']=='ss' else f" N={n['N']}")
        if m['method']=='b':label+=f" B={n['B']} lambda={n['lambda_rusanov']:g}"
        if m['method']!='ss':label+=f" CFL={n['CFL']:g}"
        xj=m['summary']['SS_xJ_m']
        for ax in axes:ax.plot(a['x_m'],a['eta_m'],label=label,lw=1.25)
    for ax in axes:
        ax.plot(a['x_m'],a['z_m'],color='#6c6c6c',lw=1,label='Bed')
        ax.set(xlabel='x (m)',ylabel='Water-surface elevation z + h (m)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    axes[0].set(xlim=(0,case['length_m']),title=f"{case['id']} — full channel")
    axes[1].set(xlim=(max(0,xj-1),min(case['length_m'],xj+5)),title='Jump and wave detail (no horizontal shift)')
    fig.savefig(output/'comparison.png',dpi=180);fig.savefig(output/'comparison.pdf');plt.close(fig)
    return output/'comparison.png'
