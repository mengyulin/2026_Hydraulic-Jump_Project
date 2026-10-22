#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export MPLCONFIGDIR="$PWD/.tools/matplotlib"
mkdir -p "$MPLCONFIGDIR"
python3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"'
python3 scripts/setup_basilisk.py
python3 -m venv .venv
PIP_CACHE_DIR="$PWD/.tools/pip-cache" .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ipykernel install --sys-prefix --name slope-lab --display-name "Slope Channel Lab"
.venv/bin/python -m pip freeze > .tools/python-packages.txt
.venv/bin/python lab.py build
MPLBACKEND=Agg .venv/bin/python -m unittest discover -s tests -v
printf '%s\n' 'Installation checks passed.' 'P0 group A: bash start_lab.sh p0_group_a.ipynb' 'P0 group B: bash start_lab.sh p0_group_b.ipynb'
