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

# Compute limits. Thermal guard (author, 2026-10-02; replaces the 90/87/93 guard of 2026-10-01): concern only when
# the 5-minute MEDIAN of the package temperature (coretemp "Package id 0", the sensor btop shows; TjMax = 100 C) is
# >= 99 C. Pause one job per step period at >= 99, resume one per step period below 96 (3 C hysteresis).
MAX_WORKERS = 100
TEMP_PAUSE_C = 99.0     # SLOW (5 min) median >= 99 -> pause one job per step period
TEMP_RESUME_C = 96.0    # SLOW (5 min) median < 96 -> resume one job per step period
TEMP_HARD_C = 101.0     # fast cap effectively off: the CPU throttles itself at TjMax 100 C (kept for sensor anomalies)
MAX_LAUNCH_PER_S = 20.0  # token bucket (2026-10-03: launches are gated by CPU utilisation incl. pending launches)
SIM_START_MAX_LOAD = 0.15  # fraction of logical CPUs (sim-start gate fallback)

# Thermal history (2026-10-01, vsl_lab/ops/ecore_probe.py): under the old < 90 C limit, one P-core simulation already
# held the package at ~90 C, so workers were pinned to the 16 E-cores (CPUs 16-31). With the 99 C median guard
# (author, 2026-10-02: "speed up the research") workers use every hardware thread; the v6 benchmark
# (parallel_sweet_spot_20261001.md) measured 32 workers (one per thread) as the throughput sweet spot for libsumo runs.
E_CORES = tuple(range(16, 32))
WORKER_CPUS = tuple(range(os.cpu_count() or 32))
N_MAX_DEFAULT = 48         # cap; the actual concurrency follows CPU utilisation (TARGET_CPU_UTIL, author 2026-10-03)
TARGET_CPU_UTIL = 0.92     # launch new jobs only while the smoothed system CPU utilisation (/proc/stat) is below this
UTIL_SMOOTH_S = 4.0        # smoothing window of the utilisation signal
TEMP_SMOOTH_S = 10.0       # FAST window (logging; cap effectively off)
TEMP_SLOW_S = 300.0        # SLOW window: 5-minute MEDIAN (author, 2026-10-02)
TEMP_STEP_S = 30.0         # at most one pause or resume per step period on the slow loop


def clean_sumo_env() -> dict:
    """Environment for child processes: no SUMO_HOME leak, single-threaded BLAS."""
    env = dict(os.environ)
    env.pop("SUMO_HOME", None)
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env
