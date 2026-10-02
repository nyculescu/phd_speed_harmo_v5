"""Append-only run ledger (roadmap §0 rule 1). One row per batch or training run, including failures."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import subprocess

from vsl_lab.config import LEDGER_PATH, REPO_ROOT

FIELDS = ["ts", "branch", "commit", "track", "phase", "run_class", "variant", "config_hash", "seeds",
          "n_runs", "health_pass", "health_warn", "health_fail", "result", "notes"]


def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def config_hash(cfg: dict) -> str:
    return hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:10]


def append(track: str, phase: str, run_class: str, variant: str, cfg: dict, seeds: str, n_runs: int,
           health: dict, result: dict | str, notes: str = "") -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    new = not LEDGER_PATH.exists()
    dirty = "+dirty" if _git("status", "--porcelain") else ""
    row = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"), "branch": _git("branch", "--show-current"),
        "commit": _git("rev-parse", "--short", "HEAD") + dirty, "track": track, "phase": phase,
        "run_class": run_class, "variant": variant, "config_hash": config_hash(cfg), "seeds": seeds,
        "n_runs": n_runs, "health_pass": health.get("PASS", 0), "health_warn": health.get("WARN", 0),
        "health_fail": health.get("FAIL", 0),
        "result": result if isinstance(result, str) else json.dumps(result, sort_keys=True), "notes": notes,
    }
    with open(LEDGER_PATH, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
