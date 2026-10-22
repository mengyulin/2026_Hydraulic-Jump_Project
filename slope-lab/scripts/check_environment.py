"""Check this kit's runtime; distinguish WSL from other working platforms.

No solver integration or HEC execution is claimed. Run after setup.sh.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def inspect():
    cache = ROOT / '.tools/matplotlib'
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', str(cache))
    release = platform.release()
    is_wsl = platform.system() == 'Linux' and 'microsoft' in release.lower()
    result = dict(platform=platform.platform(), machine=platform.machine(),
                  python=sys.version, python_prefix=sys.prefix, kit=str(ROOT),
                  is_wsl=is_wsl, wsl_distro=os.environ.get('WSL_DISTRO_NAME'),
                  packages={}, tools={}, checks={}, errors=[],
                  scope='Environment and shared-library loading only; no P0 integration or HEC execution.',
                  P0_executed=False, HEC_engine_executed=False)
    checks = result['checks']
    checks['supported_system'] = platform.system() in ('Linux', 'Darwin')
    checks['python_310_or_newer'] = sys.version_info >= (3, 10)
    checks['kit_virtualenv'] = Path(sys.prefix).resolve() == (ROOT / '.venv').resolve()
    checks['simple_build_path'] = str(ROOT).isascii() and not any(c.isspace() for c in str(ROOT))
    for command in ('cc', 'make', 'awk', 'ar', 'unzip'):
        result['tools'][command] = shutil.which(command)
    checks['system_tools'] = all(result['tools'].values())
    for name in ('numpy', 'scipy', 'matplotlib', 'jupyterlab', 'nbclient', 'ipykernel'):
        try:
            importlib.import_module(name)
            result['packages'][name] = importlib.metadata.version(name)
        except Exception as exc:
            result['errors'].append(f'{name}: {type(exc).__name__}: {exc}')
    checks['packages_importable'] = len(result['packages']) == 6
    try:
        from packaging.requirements import Requirement
        checks['dependency_versions'] = all(
            importlib.metadata.version((req := Requirement(line)).name) in req.specifier
            for line in (ROOT / 'requirements.txt').read_text().splitlines()
            if line.strip() and not line.startswith('#'))
        meta = json.loads((ROOT / 'vendor/basilisk-source.json').read_text())
        result['basilisk_sha256'] = hashlib.sha256((ROOT / 'vendor' / meta['archive_file']).read_bytes()).hexdigest()
        checks['pinned_basilisk_source'] = result['basilisk_sha256'] == meta['sha256']
        kernel = ROOT / '.venv/share/jupyter/kernels/slope-lab/kernel.json'
        spec = json.loads(kernel.read_text())
        # Compare paths lexically: resolving Python symlinks would hide a wrong venv.
        checks['notebook_kernel'] = Path(spec['argv'][0]).absolute() == (ROOT / '.venv/bin/python').absolute()
    except Exception as exc:
        result['errors'].append(f'Installation metadata: {type(exc).__name__}: {exc}')
    if all(checks.values()) and not result['errors']:
        try:
            import lab
            folder, extension = lab.build()
            library = folder / ('bridge' + extension)
            ctypes.CDLL(str(library))
            checks['B_library_loads'] = True
            result['library_suffix'] = extension
            result['binary_sha256'] = json.loads((folder / 'build.json').read_text())['binary_sha256']
        except Exception as exc:
            checks['B_library_loads'] = False
            result['errors'].append(f'Compiled solvers: {type(exc).__name__}: {exc}')
    result['environment_passed'] = all(checks.values()) and not result['errors'] and checks.get('B_library_loads', False)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-wsl', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inspect()
    result['require_wsl'] = args.require_wsl
    result['passed'] = result['environment_passed'] and (result['is_wsl'] or not args.require_wsl)
    if args.require_wsl and not result['is_wsl']:
        result['errors'].append('This is not WSL. Run from the existing Ubuntu on Windows; do not count macOS/Linux as WSL acceptance.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Environment checks passed.' if result['passed'] else 'Environment checks failed.')
    print('is_wsl:', result['is_wsl'], '| evidence:', args.output)
    for error in result['errors']:
        print(error, file=sys.stderr)
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
