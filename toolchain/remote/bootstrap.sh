#!/bin/bash
# Runs on the rented machine: system packages, Python 3.14, the locked venv, then the acceptance checks. Safe to re-run.
# usage: bootstrap.sh CODE_DIR
set -euo pipefail
C=${1:?usage: bootstrap.sh CODE_DIR}
P=/home/catalin/work/phd
T=$P/phd_speed_harmo_v5b1_toolchain
export DEBIAN_FRONTEND=noninteractive
SUDO=; [ "$(id -u)" = 0 ] || SUDO=sudo
export PATH=$HOME/.local/bin:$PATH
# A template's on-start build (onstart.sh) may still be running; what it finished is reused below.
for i in $(seq 120); do [ -e $P/.onstart_running ] && kill -0 "$(cat $P/.onstart_running)" 2>/dev/null || break; [ "$i" = 1 ] && echo "waiting for the on-start build"; sleep 10; done

$SUDO apt-get update -qq
$SUDO apt-get install -y -qq --no-install-recommends ca-certificates curl tmux rsync procps >/dev/null
# The code hard-codes the laptop's paths (venv, runs), so the same layout is made here.
$SUDO mkdir -p $T $P/v5b1_runs/jobs
[ "$(id -u)" = 0 ] || $SUDO chown -R "$(id -un)" /home/catalin

if $SUDO apt-get install -y -qq python3.14 python3.14-venv >/dev/null 2>&1; then
  PYB=/usr/bin/python3.14
else
  # Ubuntu before 26.04 has no python3.14 package; uv fetches a standalone CPython build.
  command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
  uv python install 3.14.4 || uv python install 3.14
  PYB=$(uv python find 3.14)
fi
[ -x $T/venv/bin/python ] || $PYB -m venv $T/venv
$T/venv/bin/python -m pip install -q -r "$C/toolchain/requirements_lock.txt" --extra-index-url https://download.pytorch.org/whl/cpu

cat > $T/env.sh <<'EOF'
unset SUMO_HOME
export OMP_NUM_THREADS=1
export PATH=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin:$PATH
EOF

. $T/env.sh
cd -P "$C"
export PYTHONPATH=$PWD
$T/venv/bin/python -c "import os, sys, torch, numpy, libsumo; print('python', sys.version.split()[0], 'torch', torch.__version__, 'numpy', numpy.__version__, 'threads', os.cpu_count())"
$T/venv/bin/netconvert --version | head -1
$T/venv/bin/python -m pytest -q tests/test_round1.py
# Rows stored on the laptop must reproduce on every key; a difference means this CPU or build gives other numbers.
$T/venv/bin/python docs/research/round1/checks1.py rows "$P/v5b1_runs/accept_$(hostname)"
$T/venv/bin/python toolchain/remote/fingerprint.py "$P/v5b1_runs/accept_$(hostname)" --check toolchain/remote/fingerprint.ref
echo "ACCEPT PASS: $(nproc) threads, code $(basename "$C")"
