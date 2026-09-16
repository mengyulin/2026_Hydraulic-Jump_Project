#!/usr/bin/env bash
# Manual CI check on an ephemeral Windows GitHub runner, not a student script.
set -euo pipefail
[[ $(id -u) == 0 && $(uname -r) == *microsoft* ]] || { echo 'Requires root inside the ephemeral WSL runner.'; exit 2; }
workspace=$1
report_dir="$workspace/wsl-report"
mkdir -p "$report_dir"
kit=/home/hjstudent/gc1991-lab
finish() {
  if [[ -f "$kit/.tools/build.log" ]]; then cp "$kit/.tools/build.log" "$report_dir/basilisk-build.log"; fi
}
trap finish EXIT
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential gawk python3 python3-venv unzip
useradd -m -s /bin/bash hjstudent
unzip -q "$workspace/downloads/gc1991-lab-v1.zip" -d /home/hjstudent
chown -R hjstudent:hjstudent /home/hjstudent/gc1991-lab
python3 - "$kit" "$workspace/downloads/gc1991-lab-v1.zip" "$report_dir" <<'PY'
from pathlib import Path
import hashlib,json,sys
kit,archive,out=map(Path,sys.argv[1:])
manifest=json.loads((kit/'CHECKSUMS.json').read_text())
for name,digest in manifest.items():
    assert hashlib.sha256((kit/name).read_bytes()).hexdigest()==digest,name
(out/'input.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'verified_files':len(manifest)},indent=2)+'\n')
PY
runuser -u hjstudent -- bash -c 'cd /home/hjstudent/gc1991-lab && bash setup.sh && .venv/bin/python lab.py all' 2>&1 | tee "$report_dir/installation-and-solvers.log"
# Run the same launcher as students, inspect the actual authenticated API,
# and access it from Windows PowerShell while the WSL server is alive.
cat > /home/hjstudent/check_jupyter.py <<'PY'
from pathlib import Path
import json,os,platform,shutil,signal,subprocess,time,urllib.request
kit=Path('/home/hjstudent/gc1991-lab')
result={'platform':platform.platform(),'ubuntu_release':Path('/etc/os-release').read_text(),'python':platform.python_version()}
log=(kit/'.tools/ci-jupyter.log').open('w')
server=subprocess.Popen(['bash','start_lab.sh'],cwd=kit,stdout=log,stderr=log,start_new_session=True)
try:
    for attempt in range(90):
        if server.poll() is not None:
            raise RuntimeError('Jupyter exited before it was ready; see local CI runtime log.')
        files=list((kit/'.tools/jupyter-runtime').glob('jpserver-*.json'))
        if files:
            try:
                info=json.loads(files[0].read_text())
                url=f"http://127.0.0.1:{info['port']}/api/kernelspecs?token={info['token']}"
                with urllib.request.urlopen(url,timeout=2) as response:
                    specs=json.load(response)
                if 'gc1991-lab' not in specs['kernelspecs']:
                    raise RuntimeError('GC1991 Lab kernel missing.')
                break
            except (OSError,ValueError):
                pass
        time.sleep(1)
    else:
        raise RuntimeError('Jupyter did not become ready within 90 seconds.')
    notebook_url=f"http://127.0.0.1:{info['port']}/api/contents/student_lab.ipynb?token={info['token']}"
    with urllib.request.urlopen(notebook_url,timeout=5) as response:
        notebook=json.load(response)
    assert notebook['type']=='notebook'
    assert notebook['content']['metadata']['kernelspec']['name']=='gc1991-lab'
    powershell=shutil.which('powershell.exe')
    if not powershell:
        raise RuntimeError('Windows PowerShell interop unavailable.')
    # Do not print the token URL or server log in the public CI output.
    command="$ErrorActionPreference='Stop'; $r=Invoke-WebRequest -UseBasicParsing -Uri '"+url+"'; if($r.StatusCode -ne 200){exit 1}"
    request=subprocess.run([powershell,'-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=40)
    if request.returncode:
        raise RuntimeError('Windows-to-WSL localhost request failed.')
    result['jupyter']={'linux_api':True,'windows_localhost':True,'notebook':True,'kernel':'gc1991-lab'}
    result['runs']=[json.loads(p.read_text()) for p in sorted((kit/'runs').glob('*/metadata.json'))]
    assert len(result['runs'])==3
    (kit/'.tools/wsl-check-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: Jupyter API, GC1991 Lab kernel, notebook and Windows localhost access.')
finally:
    if server.poll() is None:
        os.killpg(server.pid,signal.SIGTERM)
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(server.pid,signal.SIGKILL)
            server.wait()
    log.close()
PY
chown hjstudent:hjstudent /home/hjstudent/check_jupyter.py
runuser -u hjstudent -- "$kit/.venv/bin/python" /home/hjstudent/check_jupyter.py
cp "$kit/.tools/wsl-check-result.json" "$report_dir/result.json"
cp "$kit/.tools/python-packages.txt" "$report_dir/python-packages.txt"
echo 'PASS: fresh teaching ZIP, unprivileged setup, three solvers and Jupyter on WSL 2.'
