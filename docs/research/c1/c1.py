"""C1 (docs/research/protocols/c1_screen.md on v5b1, V521): seed stages, job files, the smoke and the runner.

Runs reuse Plan B's runner (run6.execute): each run in its own process pool, up to 3 attempts per seed, identity fields on every row,
meta.json refusing a resume at other jobs or code, a clean detached tree. Every C1 row also carries its wall time (`wall_s`). Every
job names its stage, and its seeds must lie inside that stage's range (§8).

usage: c1.py plan STAGE --out JOBS.json [--cell E30|E30s] [--n N]
       c1.py run --jobs JOBS.json --out DIR [--workers N]
       c1.py smoke --jobs JOBS.json --out DIR [--workers N]"""
import argparse
import copy
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "planb"))
sys.path.insert(0, str(HERE.parent / "v505"))
import pb  # noqa: E402
import run6  # noqa: E402
import v5  # noqa: E402

STAGES = {     # §8, inclusive ranges
    "c1_smoke": (7_489_000, 7_489_000), "c1_rate": (7_489_001, 7_489_010), "c1_ident": (7_480_400, 7_480_402),
    "c1_checks": (7_489_020, 7_489_079), "c1_gate": (7_489_080, 7_489_119), "c1_fallback": (7_489_120, 7_489_159),
    "c1_pilot": (7_490_000, 7_490_059), "c1_screen": (7_490_060, 7_491_919)}
PILOT_N = 60
LADDER_N = (240, 480, 960, 1920)     # §5
SCREEN0 = STAGES["c1_pilot"][0]
RULES = ("3E-C_TRUCK", "p333", "nc")     # §3
LENGTHS = (450.0, 600.0)     # §6 (a): nominal accel2_len; lane 4a_0 is 295, 445 and 595 m
SHARES = (0.3, 0.7)     # §6 (b)
EV = {"kind": "slowdown_draw", "edge": "2", "onset": [450.0, 800.0], "dur": [240.0, 420.0], "taper": 20.0, "salt": 505_001, "limit_kmh": 30.0}
EVENTS = {"E30": EV, "E30s": {**EV, "dur": [120.0, 240.0]}}     # §2: the cell, and its fallback E30-short
TWIN = v5.TWIN
SPLIT_KEYS = ("c1_t0", "wall_s")     # a split run's own output, skipped when it meets its unsplit twin


def split_key(k: str) -> bool:
    return k in SPLIT_KEYS or k.startswith(("b45_step_g_", "fuel_g_"))


def seeds(stage: str, lo: int | None = None, hi: int | None = None) -> list:
    a, b = STAGES[stage]
    lo, hi = a if lo is None else lo, b if hi is None else hi
    if not (a <= lo <= hi <= b):
        raise SystemExit(f"seeds {lo}-{hi} outside stage {stage} {a}-{b} (c1_screen.md §8)")
    return list(range(lo, hi + 1))


def arm_cfg(stored: dict, st: Path | None, event: dict | None = None, **extra) -> dict:
    """A stored S6 S arm with C1's keys: the event (None = S), the by-group keys, the pack's side-file folder, and any plant field."""
    c = pb.with_cond(stored, "S", copy.deepcopy(event) if event else None)
    c["split"] = True
    if st is not None:
        c["measure"] = str(st)
    return c | extra


def plan(stage: str, out_dir: Path, cell: str = "E30", n: int | None = None) -> dict:
    """The job file of one stage. Arm names are "<cell>|<arm>": S, SL450, SL600 (accel2_len), SH30, SH70 (share), E30 or E30s."""
    arms = v5.s6_arms()
    st = out_dir / "st"
    S = {r: arms[f"S|{r}"] for r in RULES + pb.V3W}
    lo, hi = STAGES[stage]
    if stage == "c1_ident":     # §10: the stored S6 configs unchanged, so traffic keys can be compared with S6's by value
        jobs = {f"S|{r}": {**{k: v for k, v in S[r].items() if k != "measure"}, "measure": str(st)} for r in RULES + pb.V3W}
    elif stage == "c1_checks":
        jobs = {f"S|{r}": arm_cfg(S[r], st) for r in ("nc", "p333")}
        jobs |= {f"SL{x:g}|{r}": arm_cfg(S[r], st, accel2_len=x) for x in LENGTHS for r in ("nc", "p333")}
        jobs |= {f"SH{round(100 * x)}|{r}": arm_cfg(S[r], st, share=x) for x in SHARES for r in ("nc", "p333")}
    elif stage in ("c1_gate", "c1_fallback"):
        ev = "E30" if stage == "c1_gate" else "E30s"
        jobs = {f"S|{r}": arm_cfg(S[r], st) for r in ("nc", "p333")}
        jobs |= {f"{ev}|{r}": arm_cfg(S[r], st, EVENTS[ev]) for r in ("nc", "p333")}
    elif stage in ("c1_pilot", "c1_screen", "c1_rate"):
        jobs = {f"{cell}|{r}": arm_cfg(S[r], st, EVENTS[cell]) for r in pb.V3W + RULES}
        if stage == "c1_screen":
            if n not in LADDER_N:
                raise SystemExit(f"c1_screen needs --n, one of {LADDER_N} (the pilot's n rule)")
            hi = SCREEN0 + n - 1
    elif stage == "c1_smoke":     # every distinct config once, an unsplit twin of each kind, the E30 T0 trace, 50 % with the share field
        jobs = {}
        for s in ("c1_checks", "c1_gate", "c1_fallback"):
            jobs |= plan(s, out_dir)["arms"]
        jobs |= {n_: c for n_, c in plan("c1_rate", out_dir, "E30")["arms"].items()}
        for n_ in ("S|nc", "S|p333", "E30|p333", "E30|w0u250", "E30|3E-C_TRUCK"):
            plain = {k: v for k, v in jobs[n_].items() if k != "split"}
            jobs[n_ + TWIN] = plain
        jobs["E30|nc~trace"] = jobs["E30|nc"] | {"t0_event": True}
        jobs["E30|nc" + TWIN] = {k: v for k, v in jobs["E30|nc"].items() if k != "split"}
        jobs["S|nc~share50"] = jobs["S|nc"] | {"share": 0.5}
    else:
        raise SystemExit(f"no C1 job for stage {stage}")
    return {"stage": stage, "seed_range": [lo, hi], "q": pb.Q, "cell": cell, "n": n, "arms": jobs}


def timed(a: tuple) -> dict:
    """run6.one with the run's wall time, for common §7's cap and §9's per-run rate of policy and rule runs."""
    t = time.monotonic()
    row = run6.one(a)
    row["wall_s"] = time.monotonic() - t
    return row


def twin_diff(a: dict, b: dict) -> list:
    """Keys that differ between a split (or traced) run and its plain twin, apart from identity fields and the split's own keys."""
    skip = run6.SKIP | {"commit", "m_st_file", "name", "arm", "ctrl_sha256", "files"}
    return [k for k in v5.same_row(a, b, skip) if not split_key(k) and not v5.tracer_key(k)]


def t0_rows(A: dict, arms: dict) -> dict:
    """§10 T0 on the smoke rows: the E30 limit read back; 4a_0's length per accel2_len and edge 3 unchanged; per share and seed the same
    automated vehicles in every arm; the realised share."""
    out = {"event": {}, "length": {}, "share": {}, "bad": []}
    for (n, s), r in A.items():
        if arms[n].get("t0_event"):
            ok = v5.t0_event_ok(r, arms[n])
            out["event"][f"{n} {s}"] = ok
            if not ok["pass"]:
                out["bad"].append(f"T0 event {n} {s}")
    base = {s: r["c1_t0"] for (n, s), r in A.items() if n == "S|nc" and "c1_t0" in r}
    for (n, s), r in A.items():
        t = r.get("c1_t0")
        if t is None or s not in base:
            continue
        L = arms[n].get("accel2_len", 300.0)
        want = base[s]["len_4a_0"] + (L - 300.0)
        out["length"][f"{n} {s}"] = {"len_4a_0": t["len_4a_0"], "plan": want, "len_3_0": t["len_3_0"], "len_4_0": t["len_4_0"]}
        if abs(t["len_4a_0"] - want) > 1.0 or abs(t["len_3_0"] - base[s]["len_3_0"]) > 1e-6 or abs(t["len_4_0"] - base[s]["len_4_0"]) > 1e-6:
            out["bad"].append(f"T0 length {n} {s}")
        sh = arms[n].get("share", 0.5)
        key = f"{sh:g} {s}"
        g = out["share"].setdefault(key, {"alks_sha": set(), "realised": []})
        g["alks_sha"].add(t["alks_sha"])
        g["realised"].append(t["alks_n"] / max(t["veh_n"], 1))
    for key, g in out["share"].items():
        if len(g["alks_sha"]) != 1:
            out["bad"].append(f"T0 share {key}: arms automate different vehicles")
        sh = float(key.split()[0])
        if any(abs(x - sh) > 0.05 for x in g["realised"]):
            out["bad"].append(f"T0 share {key}: realised {g['realised']}")
        g["alks_sha"] = sorted(g["alks_sha"])
    return out


def smoke(jobs: dict, out: Path, workers: int) -> dict:
    """S5 practice: every arm once, then each distinct config again in its own side-file folder (T3: every row value and side-file array
    equal); each split, traced or share-field run equal to its plain twin on every stored key (V386); T0 (§10)."""
    from read_m2 import npz_equal
    arms = jobs["arms"]
    sd = seeds(jobs["stage"], *jobs["seed_range"])
    run6.check_checkpoints(arms)
    run6.check_files(arms)
    first = {}
    for n, c in arms.items():
        first.setdefault(pb.sha({k: v for k, v in c.items() if k != "measure"}), n)
    rep = {n: arms[n] for n in first.values()}
    inp = {"stage": jobs["stage"], "seed_range": jobs["seed_range"], "smoke": True}
    da = run6.execute(v5.with_measure(arms, out / "a" / "st"), sd, out / "a", workers, inp, fn=timed)
    db = run6.execute(v5.with_measure(rep, out / "b" / "st"), sd, out / "b", workers, inp, fn=timed)
    A = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "a" / "s6_rows.jsonl")}
    B = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "b" / "s6_rows.jsonl")}
    skip = run6.SKIP | {"commit", "m_st_file", "wall_s"}
    missing = sorted(f"{k[0]} {k[1]}" for k in B if k not in A)
    differs = {f"{k[0]} {k[1]}": d for k in B if k in A and (d := v5.same_row(A[k], B[k], skip))}
    side = sorted(f"{k[0]} {k[1]}" for k in B if k in A and A[k].get("m_st_file")
                  and not npz_equal(out / "a" / "st" / A[k]["m_st_file"], out / "b" / "st" / B[k]["m_st_file"]))
    pairs = [(n[: -len(TWIN)], n) for n in arms if n.endswith(TWIN)] + [("E30|nc~trace", "E30|nc" + TWIN), ("S|nc~share50", "S|nc")]
    twins = {}
    for m, n in pairs:
        for s in sd:
            if (m, s) not in A or (n, s) not in A:
                twins[f"{m} {s}"] = ["missing row"]
            elif d := twin_diff(A[(m, s)], A[(n, s)]):
                twins[f"{m} {s}"] = d
    t0 = t0_rows(A, arms)
    from read_c1 import split_sums
    sums = {f"{n} {s}": e for (n, s), r in A.items() if arms[n].get("split") and (e := split_sums(r))}
    res = {"missing_in_a": missing, "replay_differs": differs, "side_files_differ": side, "twin_differs": twins, "t0": t0,
           "split_sums_fail": sums, "drops": [da, db],
           "pass": not missing and not differs and not side and not twins and not t0["bad"] and not sums and not da and not db}
    pb.cma2.write_json(out / "smoke.json", res)
    return res


def run(jobs: dict, out: Path, workers: int) -> dict:
    sd = list(range(jobs["seed_range"][0], jobs["seed_range"][1] + 1))
    seeds(jobs["stage"], *jobs["seed_range"])
    run6.check_checkpoints(jobs["arms"])
    run6.check_files(jobs["arms"])
    return run6.execute(jobs["arms"], sd, out, workers, {"stage": jobs["stage"], "seed_range": jobs["seed_range"], "cell": jobs.get("cell")}, fn=timed)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("plan", "run", "smoke"))
    ap.add_argument("stage", nargs="?")
    ap.add_argument("--jobs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", default="E30", choices=tuple(EVENTS))
    ap.add_argument("--n", type=int)
    ap.add_argument("--workers", type=int, default=31)
    x = ap.parse_args(argv)
    if x.step == "plan":
        out = Path(x.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        j = plan(x.stage, out.parent, x.cell, x.n)
        pb.cma2.write_json(out, j)
        print(j["stage"], len(j["arms"]), "arms, seeds", j["seed_range"])
        return 0
    pb.reserve(x.workers)
    if x.step == "smoke":
        res = smoke(pb.load_json(x.jobs), Path(x.out).resolve(), x.workers)
        print("smoke", "PASS" if res["pass"] else "FAIL", {k: v for k, v in res.items() if k not in ("pass", "t0") and v} | {"t0_bad": res["t0"]["bad"]})
        return 0 if res["pass"] else 1
    drops = run(pb.load_json(x.jobs), Path(x.out).resolve(), x.workers)
    print("rows done;", "crash drops:", drops or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
