param([string]$Notebook = 'group_b.ipynb')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path .\.venv\Scripts\python.exe)) { throw 'Run .\setup_group_b.ps1 first.' }
$env:JUPYTER_RUNTIME_DIR = Join-Path $PSScriptRoot '.tools\jupyter-runtime'
$env:JUPYTER_CONFIG_DIR = Join-Path $PSScriptRoot '.tools\jupyter-config'
$env:IPYTHONDIR = Join-Path $PSScriptRoot '.tools\ipython'
$env:MPLCONFIGDIR = Join-Path $PSScriptRoot '.tools\matplotlib'
if ($Notebook -notin @('p0_group_b.ipynb', 'group_b.ipynb')) { throw 'Choose p0_group_b.ipynb or group_b.ipynb.' }
New-Item -ItemType Directory -Force -Path $env:JUPYTER_RUNTIME_DIR,$env:JUPYTER_CONFIG_DIR,$env:IPYTHONDIR,$env:MPLCONFIGDIR | Out-Null
& .\.venv\Scripts\python.exe -m jupyterlab --no-browser --ip=127.0.0.1 $Notebook
