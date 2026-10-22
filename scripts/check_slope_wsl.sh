#!/usr/bin/env bash
# Acceptance harness for an ephemeral Windows/WSL runner, NOT a student installer.
set -euo pipefail
[[ $(id -u) == 0 && $(uname -r) == *microsoft* ]] || { echo 'Requires root in an ephemeral WSL runner.'; exit 2; }
workspace=$1
report="$workspace/slope-wsl-report"
student_home=/home/hjslope
mkdir -p "$report"
finish() {
  for kit in gc1991-lab slope-lab; do
    for name in build.log python-packages.txt installation.json; do
      if [[ -f "$student_home/$kit/.tools/$name" ]]; then
        cp "$student_home/$kit/.tools/$name" "$report/$kit-$name"
      fi
    done
  done
  if [[ -d "$student_home/evidence" ]]; then cp -R "$student_home/evidence/." "$report/"; fi
}
trap finish EXIT
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential gawk python3 python3-venv unzip
# Never reuse a pre-existing home or installation.
[[ ! -e "$student_home" ]] || { echo 'Refusing to modify an existing student home.'; exit 2; }
useradd -m -s /bin/bash hjslope
mkdir "$student_home/evidence"
unzip -q "$workspace/downloads/gc1991-lab-v1.zip" -d "$student_home"
unzip -q "$workspace/downloads/slope-lab-v1.3.zip" -d "$student_home"
cp "$workspace/scripts/check_slope_wsl.py" "$student_home/"
python3 "$student_home/check_slope_wsl.py" --seal "$workspace" "$student_home"
chown -R hjslope:hjslope "$student_home"
# Same distro, same ordinary user, two independent project-local environments.
runuser -u hjslope -- bash -c 'cd /home/hjslope/gc1991-lab && bash setup.sh && .venv/bin/python lab.py all' 2>&1 | tee "$report/01-gc1991-install-and-run.log"
runuser -u hjslope -- /home/hjslope/gc1991-lab/.venv/bin/python "$student_home/check_slope_wsl.py" --before "$student_home"
runuser -u hjslope -- bash -c 'cd /home/hjslope/slope-lab && bash setup.sh' 2>&1 | tee "$report/02-slope-install.log"
runuser -u hjslope -- /home/hjslope/slope-lab/.venv/bin/python "$student_home/check_slope_wsl.py" --verify "$student_home" 2>&1 | tee "$report/03-p0-and-interop.log"
echo 'PASS: same WSL environment, GC1991 preserved, both P0 Python workflows and Windows interoperability.'
