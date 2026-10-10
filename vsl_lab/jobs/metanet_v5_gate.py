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
import time
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


def _full_sha(x) -> bool:
    """A fix record must name a fixed commit (a full SHA), never a symbolic ref such as HEAD or a branch."""
    if not isinstance(x, str) or len(x) != 40:
        return False
    r = subprocess.run(["git", "-C", str(C.REPO), "rev-parse", "--verify", "--quiet", x + "^{commit}"],
                       capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == x


def fix_record_valid(f: dict) -> bool:
    """§B11.2 record: a full-SHA fix commit that changed the v5 code paths, and a failing-before test named and
    present at that commit."""
    fc, t = f.get("fix_commit"), f.get("failing_before_test")
    if not _full_sha(fc) or not t or _git_rc("cat-file", "-e", f"{fc}:{t}") != 0:
        return False
    return _git_rc("diff", "--quiet", f"{fc}~1", fc, "--", *V5.CODE_PATHS) != 0


def fix_rerun_ok(f: dict, seed: int, identity: str, old_code: str | None = None) -> bool:
    """§B11.2 re-run accepted for a seed: a valid committed fix record names the seed (rerun_seed: int or list); the
    fix commit postdates the seed's old start record (old code is its ancestor), is itself an ancestor of the
    current code identity, and no v5 code path changed after it."""
    seeds = f.get("rerun_seed")
    seeds = seeds if isinstance(seeds, list) else [seeds]
    if seed not in seeds or not fix_record_valid(f):
        return False
    fc = f["fix_commit"]
    if old_code and _git_rc("merge-base", "--is-ancestor", old_code, fc) != 0:
        return False
    if _git_rc("merge-base", "--is-ancestor", fc, identity) != 0:
        return False
    return _git_rc("diff", "--quiet", fc, identity, "--", *V5.CODE_PATHS) == 0


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
    rc = commits[0] if commits else None                        # a later freeze record needs a valid fix record
    names = any(f.get("freeze_record_commit") == rc and fix_record_valid(f)
                and _git_rc("merge-base", "--is-ancestor", f["fix_commit"], rc) == 0 for f in fixes)
    led = ledger_starts()
    lockf = V5.RUNS5 / LOCKF
    flock = json.loads(lockf.read_text()) if lockf.exists() else {}
    s_ = str(rec["nominal"] if seed is None else seed)
    if flock.get(s_) != led.get(s_):                            # both directions, for this seed: a lock entry with
        raise SystemExit(f"start record of seed {s_}: ledger and raw-dir lock disagree (missing or changed)")
    now = {"code": code, "freeze_blob": _git("hash-object", str(FREEZE5))}
    old = (led.get(s_) or {}).get("code")
    rerun = any(fix_rerun_ok(f, int(s_), now["code"], old) for f in fixes)
    seed = guard(rec, seed, audit, first, names, led or None, now, rerun)
    return seed, rec, led, now


def start_record(seed: int, lock: dict | None, now: dict, stage: str = "") -> None:
    """Written before any validation input is read: a ledger row first (the source of truth), then the raw-dir lock."""
    from vsl_lab.ops import ledger
    ledger.append("DP", "metanet-v5-gate", "S", START_VARIANT, {"seed": seed, "stage": stage}, str(seed), 0, {},
                  {"seed": seed, "stage": stage, **now}, notes=str(V5.RUNS5 / LOCKF))
    import fcntl
    import os
    V5.RUNS5.mkdir(parents=True, exist_ok=True)
    lockf = V5.RUNS5 / LOCKF
    with open(V5.RUNS5 / (LOCKF + ".mutex"), "w") as mx:      # serialise the read-modify-write; atomic replace
        fcntl.flock(mx, fcntl.LOCK_EX)
        lk = json.loads(lockf.read_text()) if lockf.exists() else {}
        lk[str(seed)] = now
        tmp = lockf.with_suffix(".tmp")
        tmp.write_text(json.dumps(lk, indent=1))
        os.replace(tmp, lockf)


def _enter(seed: int | None, stage: str, need_val: bool = True) -> tuple:
    """Guard, then input check (no lock is left if inputs are missing), then the start record."""
    seed, rec, led, now = check(seed)
    if need_val and not (V5.RUNS5 / "val_data.npz").exists():
        raise SystemExit("val_data.npz missing in the v5 raw dir: run the v5 'prep' stage first")
    start_record(seed, led, now, stage)
    return seed, rec, now


def _stamp(name: str, now: dict) -> None:
    (V5.RUNS5 / name).write_text(json.dumps(now))


def _stamped(name: str, now: dict) -> bool:
    f = V5.RUNS5 / name
    return f.exists() and json.loads(f.read_text()) == now


SEED_BOOT5 = 7192300


def deterministic(seed: int | None = None) -> dict:
    """§B8 step 7: guard, start record (before any validation input is read), then the gate's deterministic rows
    unchanged on the validation days, for the nominal plant or a member; outputs in the v5 raw directory only."""
    from vsl_lab.jobs import metanet_gate as G
    seed, rec, now_ = _enter(seed, "deterministic")
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
    _stamp(f"gate_det_{seed}.prov.json", now_)               # the output carries its start record's identity
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
        seed, rec, now = _enter(seed, stage)
    if stage != "draws-plan" and not _stamped(f"gate_draws_{seed}.prov.json", now):
        raise SystemExit("the draws plan is missing or was made at other hashes: run 'draws-plan' first")
    if stage == "rows" and not _stamped(f"gate_draws_{seed}.done.json", now):
        raise SystemExit("no complete draws-run at these hashes: run 'draws-run' first")
    with bindings(rec) as G:
        if stage == "draws-plan":
            r = G.draws_plan(seed)
            _stamp(f"gate_draws_{seed}.prov.json", now)
            return r
        if stage == "draws":
            return G.draws_day(day_index, seed)
        r = G.stochastic(seed)
        _stamp(f"gate_sto_{seed}.prov.json", now)
        return r


def verdict() -> dict:
    """§B11: the nominal plant alone decides; deterministic-only = FAIL; no F1."""
    rec = json.loads(FREEZE5.read_text())
    s = rec["nominal"]
    last = ledger_starts().get(str(s))                          # outputs must come from the seed's last start record
    if not (last and _stamped(f"gate_det_{s}.prov.json", last) and _stamped(f"gate_sto_{s}.prov.json", last)):
        raise SystemExit("gate outputs do not carry the nominal plant's current start-record identity")
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
    seed, rec, _ = _enter(seed, "prep", need_val=False)
    out = C.build_data(G.val_days(), V5.RUNS5 / "val_data.npz", exit_flows=True)
    ledger.append("DP", "metanet-v5-gate", "S", "metanet_v5_gate_prep", {"seed": seed}, "none", 0, {},
                  {"file": str(out)}, notes="validation inputs; no model run")
    return str(out)


def draws_run(seed: int | None, gate_ok: bool) -> dict:
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.ops.scheduler import Job, run_batch
    seed, rec, now = _enter(seed, "draws-run")
    if not _stamped(f"gate_draws_{seed}.prov.json", now):
        raise SystemExit("the draws plan is missing or was made at other hashes: run 'draws-plan' first")
    n = len(G.val_days())
    old = sorted(V5.RUNS5.glob(f"gate_draw_{seed}_*.json"))     # earlier per-day outputs are kept, never mixed
    if old:
        arch = V5.RUNS5 / "superseded" / f"draws_{seed}_{int(time.time())}"
        arch.mkdir(parents=True, exist_ok=True)
        for f in old:
            f.rename(arch / f.name)
    (V5.RUNS5 / f"gate_draws_{seed}.done.json").unlink(missing_ok=True)
    jobs = [Job(jid=f"draw5_{seed}_{i:03d}", argv=["vsl_lab.jobs.metanet_v5_gate", "draws", "--day-index", str(i),
                                                  "--plant", str(seed)]) for i in range(n)]
    rep = run_batch(jobs, V5.RUNS5 / f"batch_draws5_{seed}_{int(time.time())}", max_workers=32, gate_ok=gate_ok)
    missing = [i for i in range(n) if not (V5.RUNS5 / f"gate_draw_{seed}_{i:03d}.json").exists()]
    if missing or rep.n_failed_proc:
        raise SystemExit(f"draws-run incomplete: {len(missing)} days missing, {rep.n_failed_proc} failed processes")
    _stamp(f"gate_draws_{seed}.done.json", now)
    return {"n": rep.n_jobs, "ok": rep.n_ok, "failed": rep.n_failed_proc}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["prep", "deterministic", "draws-plan", "draws", "draws-run", "stochastic",
                                     "verdict"])
    ap.add_argument("--plant", type=int, default=None)
    ap.add_argument("--day-index", type=int, default=0)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "draws":                                      # one worker inside draws-run's batch
        print(json.dumps(stochastic("draws", a.plant, a.day_index), default=float)[:2000])
        return 0
    with V5.stage("metanet-v5-gate", f"metanet_v5_gate_{a.what.replace('-', '_')}",
                  {"stage": a.what, "plant": a.plant}) as st:
        if a.what == "prep":
            st.result = {"file": prep(a.plant)}
        elif a.what == "deterministic":
            r = deterministic(a.plant)
            st.result = {"plant": r["plant_seed"], "failed": r["failed"], "PASS": r["deterministic_PASS"]}
        elif a.what in ("draws-plan", "stochastic"):
            r = stochastic(a.what if a.what != "stochastic" else "rows", a.plant, a.day_index)
            st.result = {"stage": a.what, "PASS": r.get("stochastic_PASS") if isinstance(r, dict) else None}
        elif a.what == "draws-run":
            st.result = draws_run(a.plant, a.gate_ok)
        elif a.what == "verdict":
            st.result = verdict()
        print(json.dumps(st.result, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
