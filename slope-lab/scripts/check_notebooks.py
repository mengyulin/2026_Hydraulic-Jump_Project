"""Execute the two actual student notebooks; HEC import remains pending real CSV."""
from pathlib import Path
import argparse
import json
import os
import time
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    for key,part in [('JUPYTER_RUNTIME_DIR','jupyter-runtime'),('JUPYTER_CONFIG_DIR','jupyter-config'),
                     ('IPYTHONDIR','ipython'),('MPLCONFIGDIR','matplotlib')]:
        p=ROOT/'.tools'/part;p.mkdir(parents=True,exist_ok=True);os.environ[key]=str(p)
    records=[]
    for name in ['student_lab.ipynb','group_b.ipynb']:
        start=time.monotonic();nb=nbformat.read(ROOT/name,as_version=4)
        NotebookClient(nb,timeout=600,kernel_name='slope-lab',resources={'metadata':{'path':str(ROOT)}}).execute()
        nbformat.write(nb,a.output/name)
        records.append(dict(notebook=name,executed_code_cells=sum(c.cell_type=='code' for c in nb.cells),
                            passed=True,wall_seconds=time.monotonic()-start,HEC_engine_executed=False))
        (a.output/'notebook_checks.json').write_text(json.dumps(records,indent=2)+'\n')
        print(name,'executed successfully',flush=True)


if __name__=='__main__':main()
