"""HEC-RAS 6.6 steady mixed-flow projects and checked result exchange.

Native file syntax follows official legacy mixed-flow examples. Generating
and round-trip checking these text files is not an HEC-RAS engine acceptance.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from case_tools import resolve,sections,ss


def fixed8(v):
    # HEC's flow and station/elevation arrays use eight-character fields.
    for decimals in range(10,-1,-1):
        text=f'{v:.{decimals}f}'
        if text.startswith('0.'):text=text[1:]
        if text.startswith('-0.'):text='-'+text[2:]
        if len(text)<=8:return text.rjust(8)
    raise ValueError(f'Number cannot fit the HEC-RAS fixed-width field: {v}')


def write_native(path,lines):
    Path(path).write_bytes(('\r\n'.join(lines)+'\r\n').encode('ascii'))


def export_project(case,output):
    c=resolve(case);out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    records=[]
    for dx in [.5,.25,.125]:
        folder=out/('dx'+str(dx).replace('.','p'));folder.mkdir()
        base=folder/c['id'];river='SlopeChannel';reach='Main'
        coords=sections(c,dx);q_written=float(fixed8(c['Q_m3s']))
        geometry=['Geom Title='+c['id']+f' dx={dx:g}m', 'Program Version=6.60',
                  f"Viewing Rectangle= -1 , 1 , {c['length_m']+1:g} , -1",'',
                  f'River Reach={river:<16},{reach:<16}','Reach XY= 2',
                  f"{0:16g}{c['length_m']:16g}{0:16g}{0:16g}",'Rch Text X Y=0,15','Reverse River Text= 0','']
        rounded=[]
        for i,(x,z) in enumerate(coords):
            length=coords[i+1][0]-x if i+1<len(coords) else 0.
            vals=[0.,z+2.,0.,z,c['width_m'],z,c['width_m'],z+2.]
            field=''.join(fixed8(v) for v in vals);zw=float(field[24:32])
            rounded.append([x,zw])
            geometry += [f"Type RM Length L Ch R = 1 ,{c['length_m']-x:g},{length:g},{length:g},{length:g}",
                         'BEGIN DESCRIPTION:',f'x={x:g} m downstream; analytic cosine slope; vertical rectangle.',
                         'END DESCRIPTION:','#Sta/Elev= 4',field,'#Mann= 3 ,0,0',
                         ''.join(fixed8(v) for v in [0,c['n'],0,0,c['n'],0,c['width_m'],c['n'],0]),
                         f"Bank Sta=0,{c['width_m']:g}",'XS Rating Curve= 0 ,0',
                         'XS HTab Horizontal Distribution= 5 , 5 , 5','Exp/Cntr=0,0','']
        geometry+=['Use User Specified Reach Order=0','GIS Ratio Cuts To Invert=-1','GIS Limit At Bridges=0','Composite Channel Slope=5']
        write_native(base.with_suffix('.g01'),geometry)
        write_native(base.with_suffix('.f01'),[
            'Flow Title='+c['id']+' fixed discharge and tailwater','Program Version=6.60','Number of Profiles= 1',
            'Profile Names='+c['id'],f"River Rch & RM={river},{reach:<16},{c['length_m']:g}",fixed8(c['Q_m3s']),
            f'Boundary for River Rch & Prof#={river},{reach:<16}, 1','Up Type= 3',f"Up Slope={c['S1']:.17g}",
            'Dn Type= 1',f"Dn Known WS={c['z_out_m']+c['hout_m']:.17g}"])
        write_native(base.with_suffix('.p01'),[
            f"Plan Title={c['id']} Mixed dx{dx:g}",'Short Identifier='+c['id']+'Mixed','Geom File=g01','Flow File=f01',
            'Multiple Comp Mode','Mixed Flow','Starting Rch & RM=            ,        ',
            'Ending Rch & RM=            ,        ','K Sum by GR= 0','Std Step Tol= .00001','Critical Tol= .00001',
            'Num of Std Step Trials= 100','Max Error Tol= .0001','Flow Tol Ratio= .000001','Log Output Level= 5',
            'Friction Slope Method= 2','Calc Critical at every XS','Parabolic Critical Depth'])
        write_native(base.with_suffix('.prj'),[
            f"Proj Title={c['id']} slope-channel teaching dx{dx:g}",'Current Plan=p01','Default Exp/Contr=0,0','SI Units',
            'Geom File=g01','Flow File=f01','Plan File=p01','Y Axis Title=Elevation (m)',
            'X Axis Title(PF)=Main Channel Distance (m)','X Axis Title(XS)=Station (m)',
            'BEGIN DESCRIPTION:','HEC-RAS 6.6; steady mixed; arithmetic friction slope; Cc=Ce=0.',
            'Native execution must be verified on HEC-RAS 6.6.','END DESCRIPTION:'])
        # Paired SS uses the actual rounded fields read back from the written
        # format, rather than silently comparing unequal numeric inputs.
        sc=dict(id=c['id'],Q_m3s=q_written,width_m=c['width_m'],n=c['n'],bed=rounded,
                upstream=dict(type='normal_depth',slope=c['S1']),downstream=dict(type='depth',depth_m=c['hout_m']),
                losses=dict(contraction=0.,expansion=0.))
        result=ss.solve(sc,dx*(1+1e-9));j=result['summary']['jumps'][0]
        with (folder/'sections.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['river_station','x_m','z_analytic_m','z_written_m','Q_written_m3_s'])
            w.writerows((c['length_m']-x,x,z,zw,q_written) for (x,z),(_,zw) in zip(coords,rounded))
        with (folder/'paired_ss.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['river_station','x_m','z_m','h_m','eta_m','Fr'])
            for x,z in rounded:
                trace=result['upstream_trace'] if x<j['x_m'] else result['downstream_trace']
                h=ss.sample(trace['rows'],x)
                if h is None:raise ValueError('Incomplete paired SS branch.')
                fr=q_written/c['width_m']/math.sqrt(c['g_m_s2']*h**3)
                w.writerow([c['length_m']-x,x,z,h,z+h,fr])
        (folder/'paired_ss_summary.json').write_text(json.dumps(result['summary'],indent=2)+'\n')
        config=dict(case=c,dx_m=dx,section_count=len(coords),Q_written_m3s=q_written,
                    Q_rounding_m3s=q_written-c['Q_m3s'],max_bed_rounding_m=max(abs(z-zr) for (_,z),(_,zr) in zip(coords,rounded)),
                    intended_HEC_RAS_version='6.6',friction_slope_method='Average Friction Slope (code2)',
                    native_engine_verified=False,SS_jump_m=j['x_m'],
                    expected_areas='A=0.46h; R=0.46h/(0.46+2h); vertical sidewalls; no overbank flow.')
        (folder/'expected.json').write_text(json.dumps(config,indent=2)+'\n')
        check=check_project(base.with_suffix('.prj'))
        records.append(check)
    (out/'static_checks.json').write_text(json.dumps(records,indent=2)+'\n')
    return out


def check_project(project):
    project=Path(project);base=project.with_suffix('');expected=json.loads((project.parent/'expected.json').read_text())
    p=project.read_text();g=base.with_suffix('.g01').read_text();f=base.with_suffix('.f01').read_text();plan=base.with_suffix('.p01').read_text()
    assert 'SI Units' in p and 'Mixed Flow' in plan and 'Friction Slope Method= 2' in plan
    assert 'Dn Type= 1' in f and 'Up Type= 3' in f
    count=g.count('Type RM Length L Ch R =');assert count==expected['section_count']
    assert g.count('Exp/Cntr=0,0')==count and g.count('#Sta/Elev= 4')==count
    lines=g.splitlines();bed=[];stations=[]
    for i,line in enumerate(lines):
        if line.startswith('Type RM Length L Ch R ='):stations.append(float(line.split('=')[1].split(',')[1]))
        if line=='#Sta/Elev= 4':
            block=lines[i+1];assert len(block)==64
            vals=[float(block[k:k+8]) for k in range(0,64,8)]
            assert vals[0]==vals[2]==0 and vals[4]==vals[6]==.46 and vals[3]==vals[5]
            assert vals[1]>vals[3] and vals[7]>vals[5];bed.append(vals[3])
    assert all(a>b for a,b in zip(stations,stations[1:]))
    with (project.parent/'sections.csv').open() as fh:rows=list(csv.DictReader(fh))
    assert all(abs(float(r['z_written_m'])-z)<1e-12 for r,z in zip(rows,bed))
    flowlines=f.splitlines();i=next(i for i,s in enumerate(flowlines) if s.startswith('River Rch & RM='))
    assert len(flowlines[i+1])==8 and float(flowlines[i+1])==expected['Q_written_m3s']
    assert float(next(s.split('=')[1] for s in flowlines if s.startswith('Dn Known WS=')))==expected['case']['z_out_m']+expected['case']['hout_m']
    return dict(project=project.name,dx_m=expected['dx_m'],sections=count,static_check_passed=True,
                native_engine_verified=False,input_sha256={suffix:hashlib.sha256(base.with_suffix(suffix).read_bytes()).hexdigest() for suffix in ['.prj','.p01','.f01','.g01']})


def compare_export(project_folder,csv_path,output):
    """Use the supplied normalized CSV template, not undocumented column IDs."""
    import numpy as np
    folder=Path(project_folder);out=Path(output);out.mkdir(parents=True,exist_ok=False)
    expected=json.loads((folder/'expected.json').read_text());c=expected['case']
    with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    required=['river_station','water_surface_m','Fr','Q_m3_s']
    if not rows or any(k not in rows[0] for k in required):raise ValueError('Use templates/hec_profile.csv with SI values.')
    a=np.array([[float(r[k]) for k in required] for r in rows]);a=a[np.argsort(-a[:,0])]
    if not np.isfinite(a).all() or len(np.unique(a[:,0]))!=len(a):raise ValueError('Nonfinite or duplicate sections.')
    pair=np.genfromtxt(folder/'paired_ss.csv',delimiter=',',names=True)
    if len(a)!=len(pair) or not np.allclose(a[:,0],pair['river_station'],rtol=0,atol=1e-8):raise ValueError('Missing/different HEC sections.')
    if np.max(abs(a[:,3]-expected['Q_written_m3s']))>1e-7:raise ValueError('HEC flow differs from the intended case.')
    x=c['length_m']-a[:,0];h=a[:,1]-pair['z_m']
    if np.any(h<=0):raise ValueError('Nonpositive depth; check units and datum.')
    expected_fr=a[:,3]/c['width_m']/np.sqrt(c['g_m_s2']*h**3)
    if np.max(abs(a[:,2]-expected_fr))>.03:raise ValueError('Fr inconsistent with the supplied rectangular-channel water surface and Q.')
    brackets=[[float(x[i]),float(x[i+1])] for i in range(len(x)-1) if a[i,2]>1 and a[i+1,2]<1]
    result=dict(case_id=c['id'],dx_m=expected['dx_m'],jump_brackets_m=brackets,
                SS_xJ_m=expected['SS_jump_m'],eta_RMSE_m=float(np.sqrt(np.mean((a[:,1]-pair['eta_m'])**2))),
                eta_Linf_m=float(np.max(abs(a[:,1]-pair['eta_m']))),
                source_sha256=hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
                note='User-supplied HEC output; preserve original project/compute messages to authenticate engine/version. RMSE is model difference, not experimental error.')
    (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    with (out/'comparison.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['x_m','z_m','eta_hec_m','eta_ss_m','difference_m','Fr_hec'])
        w.writerows(zip(x,pair['z_m'],a[:,1],pair['eta_m'],a[:,1]-pair['eta_m'],a[:,2]))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    ax.plot(x,pair['eta_m'],label='Python SS (same written inputs)');ax.plot(x,a[:,1],'o-',ms=2,label='HEC-RAS supplied output')
    ax.set(xlabel='x (m)',ylabel='Water-surface elevation (m)',title=c['id']);ax.legend();ax.grid(alpha=.2)
    fig.savefig(out/'comparison.png',dpi=170);plt.close(fig)
    return result
