"""Build the bundled, checksum-pinned Basilisk source without changing PATH."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def install():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or newer is required.")
    if platform.system() not in ("Linux", "Darwin"):
        raise RuntimeError("Windows: open Ubuntu (WSL 2) and run setup there.")
    # Upstream make/qcc use paths in generated compiler flags.
    if not str(ROOT).isascii() or any(c.isspace() for c in str(ROOT)):
        raise RuntimeError("Extract this kit into a simple path, e.g. ~/hj-lab (ASCII, no spaces).")
    for command in ("cc", "make", "awk", "ar"):
        if not shutil.which(command):
            raise RuntimeError(f"Missing {command}. Follow docs/troubleshooting.md installation steps.")
    meta = json.loads((ROOT / "vendor/basilisk-source.json").read_text())
    archive = ROOT / "vendor" / meta["archive_file"]
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != meta["sha256"]:
        raise RuntimeError("Basilisk archive checksum mismatch; obtain a fresh teaching package.")
    target = ROOT / ".tools" / (digest[:16] + "-" + platform.system() + "-" + platform.machine())
    src = target / "basilisk/src"
    stamp = ROOT / ".tools/installation.json"
    identity = {"source_sha256": digest, "qcc": str(src / "qcc"),
                "platform": platform.platform(), "kit_directory": str(ROOT)}
    if stamp.exists() and json.loads(stamp.read_text()).get("identity") == identity and (src / "qcc").is_file():
        print("Basilisk is already built for this folder.")
        return
    # Only this generated tool directory is rebuilt. Case results live elsewhere.
    # qcc and its object files embed paths, so moving a kit needs a clean build.
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    # This pinned official archive contains regular files/directories, no links.
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise RuntimeError(f"Unexpected archive entry: {member.name}")
        # Explicitly checked above; works on Python 3.10 as well as newer versions.
        tar.extractall(target, members=members)
    shutil.copyfile(src / ("config.osx" if platform.system() == "Darwin" else "config.gcc"), src / "config")
    env = os.environ.copy()
    env["BASILISK"] = str(src)
    # Do not inherit another Basilisk installation's compiler overrides.
    for key in ("CC99", "CPP99", "CFLAGS", "LDFLAGS", "CC"):
        env.pop(key, None)
    log_path = ROOT / ".tools/build.log"
    commands = [["make", "-C", "darcsit", "literate-c"], ["make", "ast"], ["make", "qcc"]]
    with log_path.open("w") as log:
        for command in commands:
            print("Building Basilisk:", " ".join(command), flush=True)
            log.write("\n" + " ".join(command) + "\n")
            log.flush()
            subprocess.run(command, cwd=src, env=env, stdout=log, stderr=log, check=True)
    stamp.write_text(json.dumps({"identity": identity,
                                "compiler": subprocess.check_output(["cc", "--version"], text=True),
                                "build_commands": commands}, indent=2) + "\n")
    print("Basilisk installed. Build log:", log_path)


if __name__ == "__main__":
    try:
        install()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Setup failed: {error}\nSee .tools/build.log and docs/troubleshooting.md.", file=sys.stderr)
        sys.exit(1)
