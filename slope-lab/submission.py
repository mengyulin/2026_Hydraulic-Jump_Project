"""Bundle selected runs without virtual environments, compilers or binaries."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import zipfile
from case_tools import ROOT


def prepare(student,folders,output):
    if student not in [f'{g}{i}' for g in 'AB' for i in range(1,6)]:raise ValueError('Student code A1..A5 or B1..B5.')
    allowed={'P0',f'P{student[1]}L',f'P{student[1]}H'}
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'figures').mkdir()
    if student[0]=='B':(out/'hec').mkdir()
    for name in ['report.org','run_register.csv','metrics.csv','README_submission.org']:
        shutil.copy2(ROOT/'templates'/name,out/name)
    records=[]
    for folder in map(Path,folders):
        folder=folder.resolve();meta=json.loads((folder/'metadata.json').read_text())
        if meta['case']['id'] not in allowed:raise ValueError('Selected run is not assigned to this student.')
        dest=out/'runs'/folder.name
        if dest.exists():raise ValueError('Duplicate selected run.')
        shutil.copytree(folder,dest,ignore=shutil.ignore_patterns('__pycache__','*.dylib','*.so','*.exe'))
        num=meta['numerics'];s=meta.get('summary',{})
        records.append(dict(student_id=student,case_id=meta['case']['id'],method=meta['method'],run_folder='runs/'+folder.name,
                            N=num['N'] if meta['method']!='ss' else '',dx_m=num['dx_requested_m'] if meta['method']=='ss' else meta['case']['length_m']/num['N'],
                            CFL=num['CFL'],B=num['B'] if meta['method']=='b' else '',lambda_rusanov=num['lambda_rusanov'] if meta['method']=='b' else '',
                            kappa=num['kappa'] if meta['method']=='b' else '',end=num['end'] if meta['method']=='sv' else '',
                            mean_start=num['mean_start'] if meta['method']=='sv' else '',
                            continuation_tau=num['continuation_tau'] if meta['method']=='b' else '',
                            initial=num['initial'],notes='',
                            status=meta['status'],steady_screen=meta.get('steady_screen',''),x50_unique_m=s.get('x50_unique_m'),
                            first_peak_h_m=s.get('first_peak_h_m'),tail_wavelength_m=s.get('tail_wavelength_m'),
                            tail_amplitude_efold_m=s.get('tail_amplitude_efold_m')))
    if records:
        with (out/'run_register.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader()
            w.writerows({k:'N/A' if v is None else v for k,v in r.items()} for r in records)
    present={(r['case_id'],r['method']) for r in records}
    methods=['ss','sv','b'] if student[0]=='A' else ['ss']
    missing=[f'{c}/{m}' for c in sorted(allowed) for m in methods if (c,m) not in present]
    (out/'submission_status.json').write_text(json.dumps(dict(student_id=student,assigned_cases=sorted(allowed),missing_case_methods=missing,
       draft=True,note='Fill report, review numeric controls, add figures and HEC originals/exports (group B). N/A must have a reason; failed runs may be submitted as diagnosed evidence.'),indent=2)+'\n')
    return out


def archive(folder):
    folder=Path(folder).resolve();target=folder.with_suffix('.zip')
    if target.exists():raise FileExistsError('Use a new submission revision name.')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file() and not p.is_symlink() and not any(x in {'.venv','.tools','__pycache__'} for x in p.relative_to(folder).parts):
                z.write(p,p.relative_to(folder.parent))
    return target


if __name__=='__main__':
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare');p.add_argument('student');p.add_argument('folders',nargs='*',type=Path);p.add_argument('--output',type=Path,required=True)
    z=sub.add_parser('zip');z.add_argument('folder',type=Path);a=ap.parse_args()
    print(prepare(a.student,a.folders,a.output) if a.action=='prepare' else archive(a.folder))
