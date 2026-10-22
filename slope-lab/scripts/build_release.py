"""Make a fresh source-only, portable ZIP. Local tools/runs never enter it."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'.tools','.venv','runs','__pycache__','.ipynb_checkpoints','.git','.DS_Store','CHECKSUMS.json'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--version',default='v1.3');a=ap.parse_args();out=a.output.resolve()
    if not re.fullmatch(r'v[0-9]+(?:\.[0-9]+)*',a.version):raise ValueError('Use a numeric version such as v1.1.')
    if out==ROOT or ROOT in out.parents:raise ValueError('Release output must be outside the source kit.')
    out.mkdir(parents=True,exist_ok=False);target=out/'slope-lab';target.mkdir()
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if any(s in EXCLUDE for s in rel.parts) or path.is_symlink() or not path.is_file():continue
        dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dst)
    hashes={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file()}
    (target/'CHECKSUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
    archive=out/('slope-lab-'+a.version+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(target.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(out))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (out/'zip-sha256.txt').write_text(digest+'  '+archive.name+'\n')
    print(len(hashes),'files;',archive.stat().st_size,'bytes;',archive)


if __name__=='__main__':main()
