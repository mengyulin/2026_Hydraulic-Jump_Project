"""Instructor check: execute the student notebook in this independent folder."""
from pathlib import Path
import json
import os
import sys
import uuid
import nbformat
from nbclient import NotebookClient

root=Path(__file__).resolve().parents[1]
for key,subdir in [('JUPYTER_RUNTIME_DIR','jupyter-runtime'),('JUPYTER_CONFIG_DIR','jupyter-config'),
                   ('IPYTHONDIR','ipython'),('MPLCONFIGDIR','matplotlib')]:
    directory=root/'.tools'/subdir;directory.mkdir(parents=True,exist_ok=True);os.environ[key]=str(directory)
folder=root/'runs'/('notebook_check_'+uuid.uuid4().hex[:8]);folder.mkdir(parents=True)
notebook=nbformat.read(root/'student_lab.ipynb',as_version=4)
try:
    NotebookClient(notebook,timeout=300,kernel_name='gc1991-lab',resources={'metadata':{'path':str(root)}}).execute()
    nbformat.write(notebook,folder/'executed.ipynb')
    outputs=[o for c in notebook.cells if c.cell_type=='code' for o in c.outputs]
    code_cells=[c for c in notebook.cells if c.cell_type=='code']
    images=sum('image/png' in o.get('data',{}) for o in outputs)
    if any(c.execution_count is None for c in code_cells) or any(o.output_type=='error' for o in outputs) or images<2:
        raise RuntimeError('Notebook execution or plot display is incomplete.')
    summary={'status':'passed','code_cells_executed':len(code_cells),'inline_png_outputs':images,'python':sys.version}
    (folder/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2));print(folder)
except Exception as error:
    nbformat.write(notebook,folder/'failed.ipynb')
    (folder/'result.json').write_text(json.dumps({'status':'failed','error':str(error)},indent=2)+'\n')
    raise
