param()
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
py -3 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.10+ for Windows first.' }
& .\.venv\Scripts\python.exe -m pip install 'numpy>=2,<3' 'matplotlib>=3.8,<4' 'jupyterlab>=4.2,<5'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& .\.venv\Scripts\python.exe -m ipykernel install --sys-prefix --name slope-lab --display-name 'Slope Channel Lab'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Input/hydraulic/HEC format checks failed.' }
Write-Host 'Group B ready. Run .\start_group_b.ps1. HEC-RAS 6.6 is installed separately.'
