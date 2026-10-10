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


def _git_rc(*a) -> int:
    return subprocess.run(["git", "-C", str(C.REPO), *a], capture_output=True, text=True).returncode


def fix_rerun_ok(f: dict, seed: int, head: str) -> bool:
    """§B11.2 re-run accepted for a seed: the committed fix record names it, its fix commit is an ancestor of HEAD
    (or HEAD), and vsl_lab has no change after the fix commit except the append-only ledger."""
    fc = f.get("fix_commit")
    if f.get("rerun_seed") != seed or not fc:
        return False
    if _git_rc("merge-base", "--is-ancestor", fc, head) != 0:
        return False
    return _git_rc("diff", "--quiet", fc, head, "--", "vsl_lab", f":(exclude){V5.LEDGER_REL}") == 0


def _git(*a) -> str:
    return subprocess.run(["git", "-C", str(C.REPO), *a], capture_output=True, text=True).stdout.strip()


LOCKF = "gate_start.lock.json"
START_VARIANT = "metanet_v5_gate_start"


def ledger_starts() -> dict:
    """Gate start records already in the ledger: seed -> {"code", "freeze_blob"} (last row per seed)."""
    import csv
    from vsl_lab.config import LEDGER_PATH
    out = {}
    if not LEDGER_PATH.exists():
        return out
    with open(LEDGER_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("variant") == START_VARIANT:
                r = json.loads(row["result"])
                out[str(r["seed"])] = {"code": r["code"], "freeze_blob": r["freeze_blob"]}
    return out


def check(seed: int | None) -> tuple:
    """Impure wrapper: committed code (v4 §A6 (6) with v5 names), tracked and unchanged record, audit committed,
    first record, start records (ledger = source of truth; the raw-dir lock must agree with it), hashes."""
    from vsl_lab.jobs import metanet_gate as G
    code = V5.code_commit()                                    # raises if vsl_lab (ledger excepted) is dirty
    rel = str(FREEZE5.relative_to(C.REPO))
    if not _git("ls-files", rel) or _git("status", "--porcelain", "--", rel):
        raise SystemExit("v5 freeze record missing, untracked or modified against HEAD")
    rec = json.loads(FREEZE5.read_text())
    audit = bool(_git("ls-files", str(AUDIT5.relative_to(C.REPO)))) and not _git("status", "--porcelain", "--",
                                                                               str(AUDIT5.relative_to(C.REPO)))
    commits = _git("log", "--format=%H", "--", rel).split()
    first = len(commits) == 1
    fixes = []                                                  # committed and unchanged fix records only
    for p in (sorted(FIXES5.glob("*.json")) if FIXES5.exists() else []):
        r_ = str(p.relative_to(C.REPO))
        if _git("ls-files", r_) and not _git("status", "--porcelain", "--", r_):
            fixes.append(json.loads(p.read_text()))
    names = any(f.get("freeze_record_commit") == (commits[0] if commits else None) for f in fixes)
    led = ledger_starts()
    lockf = V5.RUNS5 / LOCKF
    flock = json.loads(lockf.read_text()) if lockf.exists() else {}
    for sd in set(led) | set(flock):                            # both directions: a lock entry with no ledger row
        if flock.get(sd) != led.get(sd):                        # (ledger reverted) is refused as well
            raise SystemExit(f"start record of seed {sd}: ledger and raw-dir lock disagree (missing or changed)")
    now = {"code": code, "freeze_blob": _git("hash-object", str(FREEZE5))}
    s_ = rec["nominal"] if seed is None else seed
    rerun = any(fix_rerun_ok(f, s_, now["code"]) for f in fixes)
    seed = guard(rec, seed, audit, first, names, led or None, now, rerun)
    return seed, rec, led, now


def start_record(seed: int, lock: dict | None, now: dict, stage: str = "") -> None:
    """Written before any validation input is read: a ledger row first (the source of truth), then the raw-dir lock."""
    from vsl_lab.ops import ledger
    ledger.append("DP", "metanet-v5-gate", "S", START_VARIANT, {"seed": seed, "stage": stage}, str(seed), 0, {},
                  {"seed": seed, "stage": stage, **now}, notes=str(V5.RUNS5 / LOCKF))
    lockf = V5.RUNS5 / LOCKF
    lk = json.loads(lockf.read_text()) if lockf.exists() else {}
    lk[str(seed)] = now
    V5.RUNS5.mkdir(parents=True, exist_ok=True)
    lockf.write_text(json.dumps(lk, indent=1))


def _enter(seed: int | None, stage: str, need_val: bool = True) -> tuple:
    """Guard, then input check (no lock is left if inputs are missing), then the start record."""
    seed, rec, led, now = check(seed)
    if need_val and not (V5.RUNS5 / "val_data.npz").exists():
        raise SystemExit("val_data.npz missing in the v5 raw dir: run the v5 'prep' stage first")
    start_record(seed, led, now, stage)
    return seed, rec


SEED_BOOT5 = 7192300


def deterministic(seed: int | None = None) -> dict:
    """§B8 step 7: guard, start record (before any validation input is read), then the gate's deterministic rows
    unchanged on the validation days, for the nominal plant or a member; outputs in the v5 raw directory only."""
    from vsl_lab.jobs import metanet_gate as G
    seed, rec = _enter(seed, "deterministic")
    params = rec["frozen_params"] if seed == rec["nominal"] else rec["member_params"][str(seed)]
    sh = rec["stops"]["step-halving"] == "PASS" if seed == rec["nominal"] else \
        rec["member_checks"][str(seed)]["stephalving"]
    facts = json.loads(C.FACTS.read_text())
    nl = G.nulls()
    saved = G.RUNS
    G.RUNS = V5.RUNS5
    try:
        res = G.deterministic(seed, ctx={"seed": seed, "p": params, "data": G.load_val(), "f11": facts["F11"],
                                         "nulls_for": lambda i: nl, "stephalving_PASS": sh,
                                         "boot_seed": SEED_BOOT5, "write": True})
    finally:
        G.RUNS = saved
    return res


SEED_DRAW5 = 7192301


class bindings:
    """Temporarily point the gate's module-level hooks at the v5 record (plant, freeze view, seeds, raw dir)."""

    def __init__(self, rec: dict):
        self.rec = rec

    def __enter__(self):
        from vsl_lab.jobs import metanet_gate as G
        self.G, rec = G, self.rec
        self.saved = {k: getattr(G, k) for k in ("plant", "freeze", "SEED_DRAW", "SEED_BOOT", "RUNS")}
        mem = rec.get("members", [])

        def plant(seed):
            seed = rec["nominal"] if seed is None else seed
            if seed == rec["nominal"]:
                return seed, dict(rec["frozen_params"])
            if seed in mem:
                return seed, dict(rec["member_params"][str(seed)])
            raise SystemExit(f"seed {seed} is neither the nominal plant nor a member (§B6)")
        view = {"capacity_factors": rec["capacity_factors"], "nominal_seed": rec["nominal"], "route": rec["route"],
                "diagnostics": {"benchmarks": rec["benchmarks"]}, "structure": "base",
                "stephalving": {"PASS": rec["stops"]["step-halving"] == "PASS"},
                "ensemble_candidates": {"candidates": [{"seed": m, "stephalving_PASS": True} for m in mem]}}
        G.plant, G.freeze = plant, (lambda: view)
        G.SEED_DRAW, G.SEED_BOOT, G.RUNS = SEED_DRAW5, SEED_BOOT5, V5.RUNS5
        return G

    def __exit__(self, *a):
        for k, v in self.saved.items():
            setattr(self.G, k, v)


def stochastic(stage: str, seed: int | None = None, day_index: int | None = None):
    """draws-plan | draws (one day) | rows: the gate's stochastic rows unchanged, under the v5 bindings."""
    if stage == "draws":                                        # one day inside draws-run: no new start record,
        seed, rec, led, now = check(seed)                       # but the batch's record must exist at these hashes
        if led.get(str(seed)) != now:
            raise SystemExit("no start record for this seed at these hashes: run 'draws-run'")
    else:
        seed, rec = _enter(seed, stage)
    with bindings(rec) as G:
        if stage == "draws-plan":
            return G.draws_plan(seed)
        if stage == "draws":
            return G.draws_day(day_index, seed)
        return G.stochastic(seed)


def verdict() -> dict:
    """§B11: the nominal plant alone decides; deterministic-only = FAIL; no F1."""
    rec = json.loads(FREEZE5.read_text())
    s = rec["nominal"]
    det = json.loads((V5.RUNS5 / f"gate_det_{s}.json").read_text())
    if not det["deterministic_PASS"]:
        return {"outcome": "FAIL (deterministic rows; route stop → E)", "failed": det["failed"]}
    sto = json.loads((V5.RUNS5 / f"gate_sto_{s}.json").read_text())
    spread = rec["capacity_factors"]["nominal"].get("spread_used")
    if not sto.get("stochastic_PASS"):
        return {"outcome": "FAIL (stochastic rows; route stop → E)", "failed": sto.get("failed")}
    return {"outcome": "PASS" if spread == "KM" else "PASS, substitute spread"}


def prep(seed: int | None = None) -> str:
    """Validation inputs and targets (no model) into the v5 raw dir, after the guard and a start record."""
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.ops import ledger
    seed, rec = _enter(seed, "prep", need_val=False)
    out = C.build_data(G.val_days(), V5.RUNS5 / "val_data.npz", exit_flows=True)
    ledger.append("DP", "metanet-v5-gate", "S", "metanet_v5_gate_prep", {"seed": seed}, "none", 0, {},
                  {"file": str(out)}, notes="validation inputs; no model run")
    return str(out)


def draws_run(seed: int | None, gate_ok: bool) -> dict:
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.ops.scheduler import Job, run_batch
    seed, rec = _enter(seed, "draws-run")
    jobs = [Job(jid=f"draw5_{seed}_{i:03d}", argv=["vsl_lab.jobs.metanet_v5_gate", "draws", "--day-index", str(i),
                                                  "--plant", str(seed)]) for i in range(len(G.val_days()))]
    rep = run_batch(jobs, V5.RUNS5 / f"batch_draws5_{seed}", max_workers=32, gate_ok=gate_ok)
    return {"n": rep.n_jobs, "ok": rep.n_ok, "failed": rep.n_failed_proc}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["prep", "deterministic", "draws-plan", "draws", "draws-run", "stochastic",
                                     "verdict"])
    ap.add_argument("--plant", type=int, default=None)
    ap.add_argument("--day-index", type=int, default=0)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "prep":
        print(prep(a.plant))
    elif a.what == "deterministic":
        r = deterministic(a.plant)
        print(json.dumps({"plant": r["plant_seed"], "failed": r["failed"], "PASS": r["deterministic_PASS"]}))
    elif a.what in ("draws-plan", "draws", "stochastic"):
        r = stochastic(a.what if a.what != "stochastic" else "rows", a.plant, a.day_index)
        print(json.dumps(r, default=float)[:2000])
    elif a.what == "draws-run":
        print(json.dumps(draws_run(a.plant, a.gate_ok)))
    elif a.what == "verdict":
        print(json.dumps(verdict()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
