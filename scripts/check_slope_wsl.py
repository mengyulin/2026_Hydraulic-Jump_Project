"""Real Windows/WSL acceptance. No synthetic HEC results count as engine output.

Run by check_slope_wsl.sh. Preserve evidence even on a failed stage.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

ARCHIVES = {
    'gc1991-lab-v1.zip': '870dd75d333641555c92f5f69e84cb95db713430d62bda871c05fb6cf2cac6fc',
    'slope-lab-v1.3.zip': 'ebe3e6f52893f3606f6df45cc78c442efc92deaee29a732e6a4b386179b81e80',
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        # Only non-secret commands use this helper; Jupyter tokens stay in powershell().
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        result.check_returncode()
    return result.stdout


def powershell(script):
    # Capture rather than echo commands/results: authenticated URLs contain tokens.
    executable = shutil.which('powershell.exe')
    if not executable:
        raise RuntimeError('Windows PowerShell interoperability unavailable.')
    result = subprocess.run([executable, '-NoProfile', '-NonInteractive', '-Command',
                             "$ErrorActionPreference='Stop'; " + script],
                            capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError('Windows PowerShell acceptance step failed (command/log withheld to protect Jupyter token).')
    return result.stdout.decode('utf-8-sig').strip()


def psquote(value):
    return "'" + str(value).replace("'", "''") + "'"


def sealed(kit):
    manifest = read(kit / 'CHECKSUMS.json')
    for name, digest in manifest.items():
        assert sha(kit / name) == digest, name
    return manifest


def snapshot_gc(kit):
    files = list(read(kit / 'CHECKSUMS.json')) + ['CHECKSUMS.json', '.tools/python-packages.txt',
            '.venv/share/jupyter/kernels/gc1991-lab/kernel.json']
    files += [str(p.relative_to(kit)) for p in (kit / 'runs').rglob('*') if p.is_file()]
    return {name: sha(kit / name) for name in sorted(files)}


def jupyter(kit, notebook, kernel):
    private_log = kit / '.tools/acceptance-jupyter-private.log'
    with private_log.open('w') as log:
        process = subprocess.Popen(['bash', 'start_lab.sh', notebook], cwd=kit,
                                   stdout=log, stderr=log, start_new_session=True)
        try:
            for _ in range(120):
                if process.poll() is not None:
                    raise RuntimeError('Jupyter exited during startup.')
                path = kit / f'.tools/jupyter-runtime/jpserver-{process.pid}.json'
                try:
                    server = read(path)
                    base = f"http://127.0.0.1:{server['port']}"
                    def get(route):
                        request = urllib.request.Request(base + route, headers={'Authorization': 'token ' + server['token']})
                        with urllib.request.urlopen(request, timeout=5) as response:
                            return json.load(response)
                    specs = get('/api/kernelspecs')
                    break
                except (OSError, ValueError):
                    time.sleep(1)
            else:
                raise RuntimeError('Jupyter readiness timeout.')
            assert kernel in specs['kernelspecs']
            assert Path(specs['kernelspecs'][kernel]['spec']['argv'][0]) == kit / '.venv/bin/python'
            content = get('/api/contents/' + notebook)
            assert content['type'] == 'notebook'
            assert content['content']['metadata']['kernelspec']['name'] == kernel
            # Actual Windows requests, across the Windows-to-WSL localhost bridge.
            for route in ['/api/kernelspecs', '/api/contents/' + notebook, '/lab/tree/' + notebook]:
                powershell("$r=Invoke-WebRequest -UseBasicParsing -Uri " + psquote(base + route) +
                           " -Headers @{Authorization=" + psquote('token ' + server['token']) +
                           "}; if($r.StatusCode -ne 200){throw 'HTTP check failed'}")
            return dict(notebook=notebook, kernel=kernel, linux_api=True,
                        windows_localhost_api=True, windows_lab_page_http200=True,
                        interactive_browser_clicks_tested=False)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            # Do not place Jupyter logs/tokens in public artifacts.
            private_log.unlink(missing_ok=True)


def exchange(work):
    """Copy real HEC inputs through Windows and back; do NOT invent HEC outputs."""
    source = work / 'HEC_projects'
    before = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    windows_source = run(['wslpath', '-w', str(source)]).strip()
    returned = work / 'HEC_windows_roundtrip'
    windows_returned = run(['wslpath', '-w', str(returned)]).strip()
    script = ("$d=Join-Path $env:TEMP ('HJ-P0-' + [guid]::NewGuid().ToString()); "
              "New-Item -ItemType Directory -Path $d | Out-Null; "
              "Copy-Item -LiteralPath " + psquote(windows_source) + " -Destination $d -Recurse; "
              "$project=Join-Path $d 'HEC_projects'; "
              "foreach($spacing in @('dx0p5','dx0p25','dx0p125')) { "
              "foreach($ext in @('prj','g01','f01','p01')) { "
              "if(!(Test-Path -LiteralPath (Join-Path $project ($spacing + '/P0.' + $ext)))) { throw 'Missing HEC input' } } }; "
              "Copy-Item -LiteralPath $project -Destination " + psquote(windows_returned) + " -Recurse; "
              "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
              "@{windows_temporary_directory=$d; hec_engine_executed=$false} | ConvertTo-Json -Compress")
    result = json.loads(powershell(script))
    after = {p.relative_to(returned).as_posix(): sha(p) for p in returned.rglob('*') if p.is_file()}
    assert before == after
    assert before == {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    result.update(files=len(before), hashes_equal=True, original_inputs_preserved=True,
                  scope='Real Windows file copy of HEC inputs only; HEC-RAS 6.6 Compute and exports remain untested.')
    return result


def verify(home):
    assert os.getuid() != 0
    assert platform.system() == 'Linux' and 'microsoft' in platform.release().lower()
    gc, kit, out = home / 'gc1991-lab', home / 'slope-lab', home / 'evidence'
    result = dict(passed=False, platform=platform.platform(), machine=platform.machine(),
                  python=sys.version, uid=os.getuid(), ubuntu_release=Path('/etc/os-release').read_text(),
                  HEC_engine_verified=False, interactive_Windows_browser_tested=False)
    save(out / 'result.json', result)
    before = read(out / 'gc1991-before.json')
    assert snapshot_gc(gc) == before
    result['GC1991_unchanged_after_slope_setup'] = True
    save(out / 'result.json', result)
    for key, part in [('MPLCONFIGDIR', 'matplotlib'), ('IPYTHONDIR', 'ipython'),
                      ('JUPYTER_CONFIG_DIR', 'jupyter-config'), ('JUPYTER_RUNTIME_DIR', 'jupyter-runtime')]:
        path = kit / '.tools' / part
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    run([sys.executable, 'scripts/check_environment.py', '--require-wsl', '--output', str(out / 'environment.json')], kit)
    result['environment'] = read(out / 'environment.json')
    save(out / 'result.json', result)
    run([sys.executable, 'scripts/verify_p0.py', '--output', str(out / 'P0_reproduction')], kit)
    result['P0'] = read(out / 'P0_reproduction/acceptance.json')
    save(out / 'result.json', result)
    import nbformat
    from nbclient import NotebookClient
    records = []
    for name in ['p0_group_a.ipynb', 'p0_group_b.ipynb']:
        started = time.monotonic()
        nb = nbformat.read(kit / name, as_version=4)
        try:
            NotebookClient(nb, timeout=1200, kernel_name='slope-lab', resources={'metadata': {'path': str(kit)}}).execute()
        finally:
            nbformat.write(nb, out / name)
        cells = [c for c in nb.cells if c.cell_type == 'code']
        assert all(c.execution_count is not None and not any(o.output_type == 'error' for o in c.outputs) for c in cells)
        records.append(dict(notebook=name, passed=True, code_cells=len(cells), seconds=time.monotonic() - started))
        save(out / 'notebooks.json', records)
        print('PASS: executed', name, flush=True)
    a, = (kit / 'runs').glob('P0_A_*')
    b, = (kit / 'runs').glob('P0_B_*')
    assert all(row['passed'] for row in read(a / 'reproduction.json'))
    assert read(b / 'HEC_comparisons.json') == []  # Missing real HEC results must stay pending.
    for work in (a, b):
        shutil.copytree(work, out / work.name)
    result['notebooks'] = records
    result['HEC_file_roundtrip'] = exchange(b)
    save(out / 'result.json', result)
    result['launchers'] = [jupyter(kit, name, 'slope-lab') for name in ['p0_group_a.ipynb', 'p0_group_b.ipynb']]
    save(out / 'result.json', result)
    # Check the old launcher and rerun old calculations AFTER the slope package.
    assert snapshot_gc(gc) == before
    result['GC1991_launcher_after_slope'] = jupyter(gc, 'student_lab.ipynb', 'gc1991-lab')
    previous = set((gc / 'runs').iterdir())
    run([str(gc / '.venv/bin/python'), 'lab.py', 'all'], gc)
    for name, digest in before.items():
        assert sha(gc / name) == digest, name
    fresh = sorted(set((gc / 'runs').iterdir()) - previous)
    assert len(fresh) == 3
    result['GC1991_rerun_after_slope'] = [read(p / 'metadata.json') for p in fresh]
    result['GC1991_original_files_results_and_packages_preserved'] = True
    sealed(kit)
    result['kit_inputs_preserved'] = True
    result['passed'] = True
    save(out / 'result.json', result)
    print('PASS: unchanged GC1991, real P0 calculations, launchers, Windows HTTP and HEC input round-trip.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['--seal', '--before', '--verify'])
    parser.add_argument('paths', nargs='+', type=Path)
    # Positional mode deliberately parsed after --, keeping all stages explicit.
    args = parser.parse_args(['--', *sys.argv[1:]])
    if args.mode == '--seal':
        workspace, home = args.paths
        record = {}
        for name, digest in ARCHIVES.items():
            assert sha(workspace / 'downloads' / name) == digest, name
            kit = home / ('gc1991-lab' if name.startswith('gc') else 'slope-lab')
            record[name] = dict(sha256=digest, sealed_files=len(sealed(kit)))
        save(home / 'evidence/input.json', record)
    elif args.mode == '--before':
        home, = args.paths
        kit = home / 'gc1991-lab'
        assert len(list((kit / 'runs').glob('*/metadata.json'))) == 3
        save(home / 'evidence/gc1991-before.json', snapshot_gc(kit))
        save(home / 'evidence/gc1991-initial-runs.json', [read(p) for p in sorted((kit / 'runs').glob('*/metadata.json'))])
    else:
        home, = args.paths
        verify(home)


if __name__ == '__main__':
    main()
