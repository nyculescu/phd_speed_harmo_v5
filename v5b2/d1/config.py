# Port: claude/vsl-lab-core@2a79e5e vsl_lab/config.py, subset (tool paths, run root, clean child environment);
# paths moved to the v5.B.1 toolchain and run root; the superseded thermal / launch constants are dropped.
"""Paths and tool locations for screen D1 (docs/research/protocols/screen_D1_detector_faults.md)."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_BIN = Path("/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin")
SUMO_BIN = str(VENV_BIN / "sumo")
NETCONVERT_BIN = str(VENV_BIN / "netconvert")
PYTHON_BIN = str(VENV_BIN / "python")

# Raw runs live on ext4, never in the repo.
RUNS_ROOT = Path(os.environ.get("V5B1_RUNS", "/home/catalin/work/phd/v5b1_runs"))
NET_CACHE = RUNS_ROOT / "_netcache"


def clean_sumo_env() -> dict:
    """Environment for child processes: no SUMO_HOME leak, single-threaded BLAS."""
    env = dict(os.environ)
    env.pop("SUMO_HOME", None)
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env
