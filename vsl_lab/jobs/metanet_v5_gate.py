"""METANET v5 plant gate wrapper (protocol v5 §B6, §B8 gate guard, §B11): the v4/v3 gate rows unchanged, judged on
the v5 freeze record's nominal plant and members only, single look.

python -m vsl_lab.jobs.metanet_v5_gate deterministic [--plant SEED]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_v5_calibrate as V5

FREEZE5 = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v5_calibration.json"
AUDIT5 = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v5_freeze_audit.json"
FIXES5 = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v5_fixes"
PROTOCOL = V5.PROTOCOL


# ---------------------------------------------------------------- members (§B6)
def candidates(restarts: list, nominal_seed: int, ki: list) -> list:
    """Restarts with J5 ≤ 1.02·J5_best (nominal excluded), farthest first from the nominal in the normalised
    coordinates ki (τ, ν, κ, δ_m, φ)."""
    nom = next(r for r in restarts if r["seed"] == nominal_seed)
    best = nom["best_J5"]
    xn = np.array(nom["best_x"])[ki]
    near = [r for r in restarts if r["seed"] != nominal_seed and r["admissible"] and r["best_J5"] <= 1.02 * best]
    return sorted(({"seed": r["seed"], "J5": r["best_J5"],
                    "distance": float(np.linalg.norm(np.array(r["best_x"])[ki] - xn))} for r in near),
                  key=lambda c: (-c["distance"], c["seed"]))


def members(cands: list, checks: dict) -> dict:
    """checks: seed -> {"stephalving", "P11", "screen", "F_hat"} booleans (calibration days). Grids only for the
    first 2 candidates passing checks 1-3; members = those passing 1-4 (≤ 2); never replaced."""
    gridded, mem = [], []
    for c in cands:
        ch = checks.get(c["seed"], {})
        if len(gridded) < 2 and ch.get("stephalving") and ch.get("P11") and ch.get("screen"):
            gridded.append(c["seed"])
            if ch.get("F_hat"):
                mem.append(c["seed"])
    return {"gridded": gridded, "members": mem}


# ---------------------------------------------------------------- guard (§B8, test 36)
def guard(rec: dict, seed: int | None, audit_committed: bool, first_record: bool, fix_names_record: bool,
          lock: dict | None, now: dict, fix_rerun_for_seed: bool) -> int:
    """Pure gate guard. Returns the seed to judge; raises SystemExit with the reason otherwise."""
    if rec.get("protocol") != PROTOCOL or rec.get("stage") != "freeze":
        raise SystemExit("freeze record does not name protocol v5 at stage freeze")
    if str(rec.get("route", "")).startswith("STOP"):
        raise SystemExit(f"route is '{rec['route']}': the gate must not run")
    if not audit_committed:
        raise SystemExit("the freeze-audit record is not committed (§B11.2): the gate must not run")
    if not first_record and not fix_names_record:
        raise SystemExit("not the first committed v5 freeze record, and no §B11.2 fix record names it")
    seed = rec["nominal"] if seed is None else seed
    if seed != rec["nominal"] and seed not in rec.get("members", []):
        raise SystemExit(f"seed {seed} is neither the nominal plant nor a member (§B6)")
    if lock is not None and lock.get(str(seed)) is not None:
        old = lock[str(seed)]
        if (old["code"], old["freeze_blob"]) != (now["code"], now["freeze_blob"]) and not fix_rerun_for_seed:
            raise SystemExit(f"seed {seed} has a start record with other hashes and no §B11.2 fix re-run record")
    return seed


def _git(*a) -> str:
    return subprocess.run(["git", "-C", str(C.REPO), *a], capture_output=True, text=True).stdout.strip()


def check(seed: int | None) -> tuple:
    """Impure wrapper: tracked and unchanged record, audit committed, first record, locks, hashes."""
    rel = str(FREEZE5.relative_to(C.REPO))
    if not _git("ls-files", rel) or _git("status", "--porcelain", "--", rel):
        raise SystemExit("v5 freeze record missing, untracked or modified against HEAD")
    rec = json.loads(FREEZE5.read_text())
    audit = bool(_git("ls-files", str(AUDIT5.relative_to(C.REPO)))) and not _git("status", "--porcelain", "--",
                                                                               str(AUDIT5.relative_to(C.REPO)))
    commits = _git("log", "--format=%H", "--", rel).split()
    first = len(commits) == 1
    fixes = [json.loads(p.read_text()) for p in sorted(FIXES5.glob("*.json"))] if FIXES5.exists() else []
    names = any(f.get("freeze_record_commit") == (commits[0] if commits else None) for f in fixes)
    lockf = V5.RUNS5 / "gate_start.lock.json"
    lock = json.loads(lockf.read_text()) if lockf.exists() else None
    now = {"code": _git("rev-parse", "HEAD"), "freeze_blob": _git("hash-object", str(FREEZE5))}
    s = rec["nominal"] if seed is None else seed
    rerun = any(f.get("rerun_seed") == s and f.get("fix_commit") == now["code"] for f in fixes)
    seed = guard(rec, seed, audit, first, names, lock, now, rerun)
    return seed, rec, lock, now


def start_record(seed: int, lock: dict | None, now: dict) -> None:
    """Written before any validation input is read: per seed, the code commit and the freeze record's blob hash."""
    lockf = V5.RUNS5 / "gate_start.lock.json"
    lock = dict(lock or {})
    lock[str(seed)] = now
    lockf.write_text(json.dumps(lock, indent=1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["deterministic"])
    ap.add_argument("--plant", type=int, default=None)
    a = ap.parse_args(argv)
    raise SystemExit("the v5 gate runs only after the freeze record and the freeze audit are committed (§B8 step 7);"
                     " wiring to metanet_gate.deterministic is completed with the freeze job")


if __name__ == "__main__":
    sys.exit(main())
