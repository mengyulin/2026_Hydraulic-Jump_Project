"""Export a small standalone source distribution; never include local runs/tools."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'.tools','.venv','runs','__pycache__','.ipynb_checkpoints','.git','.DS_Store','CHECKSUMS.json'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    if out==ROOT or ROOT in out.parents:raise ValueError('Choose an output outside the source directory.')
    out.mkdir(parents=True,exist_ok=False)
    target=out/'gc1991-lab';target.mkdir()
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if any(part in EXCLUDE for part in rel.parts) or path.is_symlink() or not path.is_file():continue
        copy=target/rel;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,copy)
    hashes={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file()}
    (target/'CHECKSUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
    archive=out/'gc1991-lab-v1.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(target.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(out))
    (out/'zip-sha256.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    print(f'{len(hashes)} source files + manifest; ZIP {archive.stat().st_size:,} bytes; {out}')

if __name__=='__main__':main()
