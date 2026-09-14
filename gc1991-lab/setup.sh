#!/usr/bin/env bash
# Install locally; operating-system prerequisites are described in docs/.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required; see docs/"'
python3 scripts/setup_basilisk.py
python3 -m venv .venv
PIP_CACHE_DIR="$PWD/.tools/pip-cache" .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ipykernel install --sys-prefix --name gc1991-lab --display-name "GC1991 Lab"
.venv/bin/python -m pip freeze > .tools/python-packages.txt
MPLBACKEND=Agg .venv/bin/python -m unittest discover -s tests -v
printf '%s\n' 'Installation checks passed. Next: bash start_lab.sh'
