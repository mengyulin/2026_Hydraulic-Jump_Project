"""Verify distributed file integrity without treating runtime outputs as sources."""
import hashlib
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
manifest=root/'CHECKSUMS.json'
if not manifest.exists():
    print('No release manifest: this may be the editable development source.',file=sys.stderr)
    raise SystemExit(1)
entries=json.loads(manifest.read_text());bad=[]
for name,digest in entries.items():
    p=root/name
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:bad.append(name)
if bad:
    print('Missing or changed distributed files: '+'; '.join(bad),file=sys.stderr)
    raise SystemExit(1)
print(f'All {len(entries)} distributed files match. Generated runs and tools are excluded.')
