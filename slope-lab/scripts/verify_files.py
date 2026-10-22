from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'CHECKSUMS.json').read_text())
for name,digest in manifest.items():
    p=ROOT/name
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
        raise RuntimeError('Changed/missing delivered file: '+name)
print('Verified',len(manifest),'delivered files. This is a file-integrity check, not a model validation.')
