"""Paths, tool locations and global limits for the VSL / harmonisation DRL lab.

All limits here mirror CLAUDE.md (author decisions 2026-10-01).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_BIN = Path("/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin")
SUMO_BIN = str(VENV_BIN / "sumo")
NETCONVERT_BIN = str(VENV_BIN / "netconvert")
PYTHON_BIN = str(VENV_BIN / "python")

# Raw runs live on ext4, never in the repo.
RUNS_ROOT = Path(os.environ.get("VSL_LAB_RUNS", "/home/catalin/work/phd/vsl_lab_runs"))
NET_CACHE = RUNS_ROOT / "_netcache"

# Committed, small artefacts.
LEDGER_PATH = REPO_ROOT / "vsl_lab" / "runs" / "ledger.csv"

# Compute limits (CLAUDE.md, 2026-10-01).
MAX_WORKERS = 100
TEMP_HARD_C = 90.0      # never exceed
TEMP_PAUSE_C = 88.0     # pause lowest-priority jobs at/above this
TEMP_RESUME_C = 82.0    # resume below this
SIM_START_MAX_LOAD = 0.15  # fraction of logical CPUs (sim-start gate fallback)

# Thermal finding (2026-10-01, vsl_lab/ops/ecore_probe.py): ONE simulation on a P-core (5.4-5.6 GHz turbo)
# already holds the package at mean 90.3 C (72 % of samples >= 90 C) in the 'performance' profile, so
# throttling the worker count alone cannot meet < 90 C. Pinned to the 16 E-cores (CPUs 16-31, 4.0 GHz):
# 1 job mean 64 C, 8 jobs mean 73 C (max 78), 16 jobs mean 86 C (max 90). All lab workers are therefore
# pinned to E-cores (our own process affinity; no system setting is changed) and N_MAX_DEFAULT = 12.
E_CORES = tuple(range(16, 32))
N_MAX_DEFAULT = 12
TEMP_SMOOTH_S = 10.0       # thermal decisions use the mean over this window (the sensor spikes per sample)


def clean_sumo_env() -> dict:
    """Environment for child processes: no SUMO_HOME leak, single-threaded BLAS."""
    env = dict(os.environ)
    env.pop("SUMO_HOME", None)
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env
