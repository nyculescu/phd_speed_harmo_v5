"""Round 2 measurement pack (V468, report-only): re-runs round 2's test and band runs with v5b2/fleet/measure.py switched on.
The runs are deterministic, so they are the same trajectories that produced the round-2 readings; `smoke` proves it on a sample
(every stored key equal) and checks the pack's own sums. No reading or verdict changes; no new seed is used.

usage: measure2.py smoke OUT WORK WORKERS     sample runs, traced against the stored rows, and the pack's consistency checks
       measure2.py plan OUT WORK              writes the job files and prints the run count; runs nothing
       measure2.py run OUT WORK WORKERS --go  the full measurement (not started without --go and a clean, committed tree)
       measure2.py smoke1 OUT WORK WORKERS    S1's sample runs (new levels, new seeds): they complete and the pack's sums hold
       measure2.py analyse WORK [ROWS]        per-run metrics from measured rows (summary_*.json)
       measure2.py report OUT WORK [ROWS]     ASCII distributions over seeds per arm and cell (policy arms: mean of 5 learners)
OUT is round 2's run folder (val/validation.json, test/, band/ rows); WORK is where the measured rows and side files go.
S1 (V470, report-only) adds v3w at its chosen checkpoints, no control, p333, os1_15_10 and 3E-T at 3,500 and 7,000 veh/h under the
training slowdowns, with the band's configurations, on seeds 7,440,900-919."""
import json
import multiprocessing as mp
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(ROOT), str(HERE), str(HERE.parent / "round1")]

from common1 import load  # noqa: E402
import test2  # noqa: E402
from v5b2.fleet import measure as me  # noqa: E402

SKIP = {"cfg"}     # the only stored key allowed to differ: the measured run's config carries the pack's folder
S1_LEVELS = (3500.0, 7000.0)
S1_SEEDS = list(range(7_440_900, 7_440_920))
S1_RULES = ("B|nc", "B|p333", "B|os1_15_10", "B|3e")
SMOKE1 = [("B|nc", 7000.0), ("B|w0u250", 7000.0), ("B|p333", 3500.0)]
SMOKE = [("test", "X1|nc", 5300.0), ("test", "X1|w0u250", 5300.0), ("test", "X2|t0", 5300.0), ("test", "X2|s0u500", 5300.0),
         ("test", "X2|3ex2", 5300.0), ("band", "B|p333", 6000.0), ("band", "B|d0u500", 5000.0)]


def jobs(out: Path, work: Path) -> dict:
    """phase -> {name: cfg with the pack on}, levels and seeds, exactly as test2 ran them."""
    v = json.load(open(out / "val/validation.json"))
    g, gb = test2.arms(v)
    if set(g) != {"eval"} or set(gb) != {"eval"}:
        raise SystemExit(f"tested arms come from more than one snapshot: {sorted(g)} {sorted(gb)}")
    st = str(work / "st")
    tj = json.load(open(out / "test/job_6c49e7e.json"))
    bj = json.load(open(out / "band/job_6c49e7e.json"))
    for name, cfg in g["eval"].items():
        assert tj["arms"][name] == cfg, name
    for name, cfg in gb["eval"].items():
        assert bj["arms"][name] == cfg, name
    w = {f"B|{n}" for n in __import__("decide2").names("v3w", {int(i): c for i, c in v["chosen"]["v3w"].items()})}
    s1 = {n: c for n, c in gb["eval"].items() if n in S1_RULES or n in w}
    assert len(s1) == 9, sorted(s1)
    return {"test": {"arms": {n: {**c, "measure": st} for n, c in g["eval"].items()}, "levels": tj["levels"], "seeds": tj["seeds"]},
            "band": {"arms": {n: {**c, "measure": st} for n, c in gb["eval"].items()}, "levels": bj["levels"], "seeds": bj["seeds"]},
            "s1": {"arms": {n: {**c, "measure": st} for n, c in s1.items()}, "levels": list(S1_LEVELS), "seeds": S1_SEEDS}}


def _run(a):
    from v5b2.fleet.plant_sweep import run_one
    return run_one(a)


def same(stored: dict, new: dict) -> list:
    """Keys whose values differ, plus stored keys missing from the new row and new non-pack keys absent from the stored one.
    The new row goes through JSON first, as the stored one did (tuples become lists)."""
    new = json.loads(json.dumps(new))
    bad = [k for k in stored if k not in SKIP and stored[k] != new.get(k)]
    bad += [f"+{k}" for k in new if k not in stored and not k.startswith("m_")]
    return bad


def checks(row: dict, field: dict) -> dict:
    """The pack's sums against the plant's own counters, on one run."""
    C = me.CLASSES
    n = sum(row[f"m_n_{c}"] for c in C)
    out = {
        "speed_bins_sum_eq_steps": all(sum(row[f"m_vh_{c}"]) == row[f"m_n_{c}"] == sum(row[f"m_ah_{c}"]) for c in C),
        "dist_eq_dist_step": bool(np.isclose(sum(row[f"m_dist_m_{c}"] for c in C), row["dist_step"], rtol=1e-9)),
        "fuel_eq_fuel_step": bool(np.isclose(sum(row[f"m_fuel_mg_{c}"] for c in C), row["fuel_step"], rtol=1e-9)),
        "event_s_eq_b3_step": bool(np.isclose(sum(row[f"m_event_s_{c}"] for c in C), row["b3_step"], rtol=1e-9, atol=1e-6)),
        "events_ge45_le_b45_steps": sum(np.asarray(row[f"m_peak_{c}"])[3:].sum() for c in C) <= round(row.get("b45_step", 0.0) / 0.1) + 1,
        "st_seconds_le_vs": float(field["n"].sum()) <= row["vs"],
        "st_covers_mainline": float(field["n"].sum()) > 0.5 * row["vs"],
        "m2_out_near_passed": abs(sum(row["m_minute"]["m2_out"]) - row["passed"]) <= max(10, 0.01 * row["passed"]),
        "steps": n,
    }
    if "m_dec_level_s" in row and len(row.get("lv", [])) == 12:     # the pack's level-seconds against the environment's own V2V-on count
        out["level_s_eq_env_lv"] = row["m_dec_level_s"] == np.asarray(row["lv"]).reshape(3, 4).sum(0).tolist()
        out["decisions_present"] = row["m_dec_totals"].get("asked", 0) > 0
    # An ALKS event can cross -9 m/s² more than once (the plant counts each crossing), so the two -9 counts are not compared.
    a9 = sum(np.asarray(row["m_peak_alks"])[7:])     # peaks at -8 or harder: the plant counts -8.99
    out["alks_ge9_event_if_full"] = a9 > 0 or row.get("alks_full_events", 0.0) == 0
    return out


def smoke(out: Path, work: Path, workers: int) -> int:
    J = jobs(out, work)
    stored = {"test": load(*sorted((out / "test").glob("rows_*.jsonl"))), "band": load(*sorted((out / "band").glob("rows_*.jsonl")))}
    rd = str(work / "rd")
    todo = []
    for ph, name, q in SMOKE:
        seed = J[ph]["seeds"][0]
        todo.append((ph, (name, J[ph]["arms"][name], q, seed, rd)))
    rep = {}
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        futs = {ex.submit(_run, a): (ph, a) for ph, a in todo}
        for f in as_completed(futs):
            ph, a = futs[f]
            row = f.result()
            name, _, q, seed, _ = a
            ref = stored[ph][(name, q)][seed]
            field = np.load(work / "st" / row["m_st_file"])
            c = checks(row, {"v": field["v"], "n": field["n"]})
            s = me.summary(row, {"v": field["v"], "n": field["n"]})
            rep[f"{name}|{q:.0f}|{seed}"] = {"differs": same(ref, row), "checks": c, "summary": s}
            (work / "smoke_rows.jsonl").open("a").write(json.dumps(row) + "\n")
            print(name, q, seed, "differs:", rep[f"{name}|{q:.0f}|{seed}"]["differs"][:5], "checks:", {k: v for k, v in c.items() if v is not True}, flush=True)
    ok = all(not r["differs"] and all(v for k, v in r["checks"].items() if k != "steps") for r in rep.values())
    (work / "smoke_report.json").write_text(json.dumps(rep, indent=1, default=float))
    print("SMOKE", "PASS" if ok else "FAIL", f"({len(rep)} runs)", flush=True)
    return 0 if ok else 1


def smoke1(out: Path, work: Path, workers: int) -> int:
    """S1 has no stored rows to equal, so its sample runs only have to complete and pass the pack's own sums; wall time is printed."""
    J = jobs(out, work)["s1"]
    rd = str(work / "rd")
    todo = [(name, J["arms"][name], q, S1_SEEDS[0], rd) for name, q in SMOKE1]
    ok, t0 = True, time.time()
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        futs = {ex.submit(_run, a): a for a in todo}
        for f in as_completed(futs):
            row = f.result()
            field = np.load(work / "st" / row["m_st_file"])
            c = checks(row, {"v": field["v"], "n": field["n"]})
            bad = {k: v for k, v in c.items() if k != "steps" and not bool(v)}
            ok &= not bad
            (work / "smoke1_rows.jsonl").open("a").write(json.dumps(row) + "\n")
            print(row["name"], row["q"], row["seed"], "done after s", round(time.time() - t0), "delay", round(row["all_delay"]), "ttc", row["ttc_net"],
                  "passed", row["passed"], "teleports", row.get("teleports"), "failed checks:", bad, flush=True)
    print("SMOKE1", "PASS" if ok else "FAIL", flush=True)
    return 0 if ok else 1


def plan(out: Path, work: Path) -> dict:
    J = jobs(out, work)
    work.mkdir(parents=True, exist_ok=True)
    n = {}
    for ph, j in J.items():
        (work / f"job_{ph}.json").write_text(json.dumps(j, indent=0))
        n[ph] = len(j["arms"]) * len(j["levels"]) * len(j["seeds"])
    print("runs:", n, "total", sum(n.values()), flush=True)
    return n


def run(out: Path, work: Path, workers: int) -> None:
    try:     # a rented machine runs a git archive with no repository: nothing there can be uncommitted
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "v5b2", "analysis/round2"], capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        dirty = ""
    if dirty:
        raise SystemExit("uncommitted changes in v5b2 or round2: run from a clean, frozen copy")
    from v5b2.fleet.plant_sweep import matrix
    for ph, j in jobs(out, work).items():
        matrix(j["arms"], tuple(j["levels"]), j["seeds"], work / f"rows_{ph}.jsonl", workers, str(work / "rd"))


def panel(title: str, d: dict, unit: str, width: int = 48) -> str:
    """One ASCII panel: per arm, range (-), middle half (=) and median (|) over seeds."""
    vals = np.concatenate([np.asarray(x, float) for x in d.values() if len(x)])
    lo, hi = float(vals.min()), float(vals.max())
    pad = 0.05 * (hi - lo) if hi > lo else (0.05 * abs(hi) if hi else 1.0)
    lo, hi = lo - pad, hi + pad
    lines = [f"{title}, axis {lo:.3g} to {hi:.3g} {unit}"]
    for k, x in d.items():
        q = np.percentile(x, [0, 25, 50, 75, 100])
        pos = lambda z: int(round((z - lo) / (hi - lo) * (width - 1)))
        ln = [" "] * width
        for i in range(pos(q[0]), pos(q[4]) + 1):
            ln[i] = "-"
        for i in range(pos(q[1]), pos(q[3]) + 1):
            ln[i] = "="
        ln[pos(q[2])] = "|"
        lines.append(f"  {k:<14}{''.join(ln)}  med {q[2]:.3g}  IQR {q[1]:.3g}-{q[3]:.3g}")
    return "\n".join(lines)


def analyse(work: Path, rows_file: str = "rows_test.jsonl") -> dict:
    rows = [json.loads(x) for x in (work / rows_file).read_text().splitlines()]
    per = {}
    for r in rows:
        f = np.load(work / "st" / r["m_st_file"])
        per.setdefault((r["name"], r["q"]), {})[r["seed"]] = me.summary(r, {"v": f["v"], "n": f["n"]})
    (work / f"summary_{rows_file.replace('.jsonl', '')}.json").write_text(json.dumps({f"{n}|{q:.0f}": v for (n, q), v in per.items()}, default=float))
    return per


METRICS = [("car speed, median", "km/h", lambda m: m["v_q_car"][2]), ("ALKS speed, median", "km/h", lambda m: m["v_q_alks"][2]),
           ("car |accel| RMS", "m/s²", lambda m: m["a_rms_car"]), ("car decel, 5th pct", "m/s²", lambda m: m["a_q_car"][0]),
           ("braking events, all classes", "per run", lambda m: sum(m[f"events_{c}"] for c in me.CLASSES)),
           ("events peaking at -4.5 or harder", "per run", lambda m: sum(m[f"events_ge45_{c}"] for c in me.CLASSES)),
           ("cascade share (cars)", "share", lambda m: m["cascade_share_car"]), ("petrol fuel, cars + ALKS", "g/km", lambda m: m["fuel_petrol_g_km"]),
           ("merge 1 slow minutes", "min", lambda m: m["m1"]["slow_minutes"]), ("merge 2 slow minutes", "min", lambda m: m["m2"]["slow_minutes"]),
           ("ramp 1 queue, mean", "veh", lambda m: m["ramp1_queue_mean"] + m["ramp1_pending_mean"]),
           ("ramp 2 queue, mean", "veh", lambda m: m["ramp2_queue_mean"] + m["ramp2_pending_mean"]),
           ("jam share (< 30 km/h)", "share", lambda m: m["waves"]["jam_share"]), ("jam clusters", "per run", lambda m: m["waves"]["jams"]),
           ("speed oscillation", "km/h", lambda m: m["waves"]["osc_kmh"]), ("congested length, max", "km", lambda m: m["waves"]["congested_km_max"]),
           ("decisions applied (level moved)", "share", lambda m: m["dec"]["applied_share"] if "dec" in m else None),
           ("excess level changes per ALKS", "per vehicle", lambda m: m["dec"]["excess_changes_per_vehicle"] if "dec" in m else None),
           ("reversals per change", "share", lambda m: m["dec"]["reversal_share"] if "dec" in m else None),
           ("ALKS at the longest level, V2V on", "share", lambda m: m["dec"]["level_share_on"][-1] if "dec" in m and m["dec"]["level_share_on"] else None),
           ("policy confidence, median", "probability", lambda m: m["dec"]["conf_q"][1] if "dec" in m and m["dec"]["conf_q"] else None)]


def groups(out: Path) -> dict:
    v = json.load(open(out / "val/validation.json"))
    import decide2 as dc
    tested, inc = test2.plan(v)
    return {("baseline-v3" if k == "inc" else k): dc.names(k, ch) for k, ch in [*tested, inc]}


def report(out: Path, work: Path, rows_file: str = "rows_test.jsonl") -> str:
    per = analyse(work, rows_file)
    G = groups(out)
    cells = sorted({(n.split("|")[0], q) for n, q in per})
    txt = []
    for cell, q in cells:
        arms = {"no control": ["nc"], "p333": ["p333"], "os1_15_10": ["os1_15_10"], "3E-T": ["3e"], "3E-X1": ["3ex1"], "3E-X2": ["3ex2"], **G}
        for title, unit, f in METRICS:
            d = {}
            for lab, names in arms.items():
                runs = [per.get((f"{cell}|{n}", q)) for n in names]
                if any(r is None for r in runs):
                    continue
                seeds = sorted(set.intersection(*[set(r) for r in runs]))
                xs = [np.mean([f(r[s]) for r in runs]) for s in seeds if all(f(r[s]) is not None for r in runs)]
                if xs:
                    d[lab] = xs
            if d:
                txt.append(panel(f"{cell} at {q:,.0f} veh/h: {title}", d, unit))
    s = "\n\n".join(txt)
    (work / f"report_{rows_file.replace('.jsonl', '')}.txt").write_text(s)
    return s


def main(a: list) -> int:
    if a[0] == "smoke":
        return smoke(Path(a[1]), Path(a[2]), int(a[3]))
    if a[0] == "smoke1":
        return smoke1(Path(a[1]), Path(a[2]), int(a[3]))
    if a[0] == "plan":
        plan(Path(a[1]), Path(a[2]))
        return 0
    if a[0] == "run":
        if "--go" not in a:
            raise SystemExit("the full measurement needs --go")
        run(Path(a[1]), Path(a[2]), int(a[3]))
        return 0
    if a[0] == "analyse":
        analyse(Path(a[1]), *(a[2:3]))
        return 0
    if a[0] == "report":
        print(report(Path(a[1]), Path(a[2]), *(a[3:4])))
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
