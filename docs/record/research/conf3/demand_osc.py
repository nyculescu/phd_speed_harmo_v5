"""Exploratory oscillation test (V407): policies trained at constant demand, now under demand that rises, falls and oscillates within a run.
Each worker replaces the environment's constant-rate demand with a piecewise-constant profile in 30-s steps; the frozen code is not changed.
Same arms as the demand sweep, no slowdown, 10 used evaluation seeds, report-only. usage: demand_osc.py out_dir workers"""
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from pathlib import Path

from common import cfg

CONF3 = Path("/home/catalin/work/phd/v5b1_runs/conf3")
SEEDS = range(7_440_200, 7_440_210)
END, STEP = 1800.0, 30.0


def profile(kind):
    out = []
    for i in range(int(END / STEP)):
        t0 = i * STEP
        m = t0 + STEP / 2
        if kind == "peak":
            q = 4000.0 + 1600.0 * max(0.0, min(1.0, (m - 600.0) / 300.0, (1500.0 - m) / 300.0))
        elif kind == "sine_slow":
            q = 4800.0 + 800.0 * math.sin(2 * math.pi * m / 600.0)
        elif kind == "sine_fast":
            q = 4800.0 + 800.0 * math.sin(2 * math.pi * m / 300.0)
        else:
            q = 5600.0 if 900.0 <= m < 1400.0 else 4200.0
        out.append((t0, t0 + STEP, q))
    return out


KINDS = ("peak", "sine_slow", "sine_fast", "step")


def job(a):
    name, c, seed, kind, rd = a
    from v5b.fleet import fleet as fl, plant_sweep as ps
    base = fl.FleetDemand
    prof = profile(kind)
    fl.FleetDemand = lambda s, _profile, cf: base(s, prof, cf)
    row = ps.run_one((name, c, 4800.0, seed, rd))
    row["profile"] = kind
    return row


if __name__ == "__main__":
    out, w = Path(sys.argv[1]), int(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    o = json.load(open(CONF3 / "opponents.json"))
    arms = {"nc": {}, "p333": o["ctrl"]["p333"], "os1_15_10": o["ctrl"]["os1_15_10"], "lr400_13_2": o["ctrl"]["lr400_13_2"], **{f"d{i}": {"pt": str(CONF3 / "train" / f"C{i}_final.pt")} for i in range(5)}}
    (out / "profiles.json").write_text(json.dumps({k: profile(k) for k in KINDS}))
    f = out / "osc.jsonl"
    done = {(r["name"], r["seed"], r["profile"]) for r in map(json.loads, f.read_text().splitlines())} if f.exists() else set()
    jobs = [(f"S|{n}", cfg(k, "S"), s, kind, str(out / "rd")) for kind in KINDS for n, k in arms.items() for s in SEEDS if (f"S|{n}", s, kind) not in done]
    print(len(jobs), "jobs", flush=True)
    with ProcessPoolExecutor(w, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex, f.open("a") as fo:
        for fut in as_completed([ex.submit(job, j) for j in jobs]):
            fo.write(json.dumps(fut.result()) + "\n")
            fo.flush()
    print("done", flush=True)
