#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  printf '%s\n' 'First run: bash setup.sh' >&2
  exit 1
fi
printf '%s\n' 'Open the localhost token URL below in your browser; select the GC1991 Lab kernel.'
export JUPYTER_RUNTIME_DIR="$PWD/.tools/jupyter-runtime"
export JUPYTER_CONFIG_DIR="$PWD/.tools/jupyter-config"
export IPYTHONDIR="$PWD/.tools/ipython"
export MPLCONFIGDIR="$PWD/.tools/matplotlib"
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_CONFIG_DIR" "$IPYTHONDIR" "$MPLCONFIGDIR"
exec .venv/bin/python -m jupyterlab --no-browser --ip=127.0.0.1 student_lab.ipynb
