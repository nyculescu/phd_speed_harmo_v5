"""E1 headroom check (V213, docs/research/protocols/e1_headroom.md): job lists, the runner and the stage analyses.

A job is one day (or slice) of `v5b.fleet.day one` on plant v199 at ADT 45,000. Outputs go to
ROOT/<stage>/<cell>/<arm>/<point>/ss<sumo seed>/day_s<seed>.json, so twins and arms never share a file name. Jobs
run as `python -m v5b.fleet.day one`, which the CPU guard pattern `v5b\\.fleet\\.(day|weather|incident) one` matches.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.fleet import control as ct
from v5b.p1c.calibrate import _cpu_util

ROOT = Path("/home/catalin/work/phd/v5b1_runs/e1")
PLANT, ADT = "v199", 45000.0
BLOCKER = "57600,3,1,650,2700"
TWIN = 5000
THROWAWAY = tuple(range(7430040, 7430050))
L_BAR_SEED = 7430040
WAVE1_PROVISIONAL_O = 20.0          # placeholder setpoint for the smoke days (§10.2); outcomes are not read
WANG, CONSERVATIVE = (100.0, 4.0), (60.0, 1.0)   # PI-ALINEA K_P, K_I in km·lane/h (§3.2)


def job(stage: str, cell: str, arm: str, point: str, seed: int, ss: int | None = None, ctrl: dict | None = None,
        hours: str | None = None) -> dict:
    return {"stage": stage, "cell": cell, "arm": arm, "point": point, "seed": seed, "ss": ss, "ctrl": ctrl,
            "hours": hours}


def out_path(j: dict, root: Path = ROOT) -> Path:
    return root / j["stage"] / j["cell"] / j["arm"] / j["point"] / f"ss{j['ss'] or j['seed']}" / f"day_s{j['seed']}.json"


def argv(j: dict, root: Path = ROOT) -> list:
    a = [PYTHON_BIN, "-m", "v5b.fleet.day", "one", "--seed", str(j["seed"]), "--out", str(out_path(j, root)),
         "--plant", PLANT, "--adt", f"{ADT:g}"]
    if j["cell"] == "I":
        a += ["--crash-k", "0", "--blocker", BLOCKER]
    if j["ss"] is not None:
        a += ["--sumo-seed", str(j["ss"])]
    if j["ctrl"]:
        a += ["--ctrl", json.dumps(j["ctrl"], sort_keys=True)]
    if j["hours"]:
        a += ["--hours", j["hours"]]
    return a


def order(jobs: list) -> list:
    """Slowest first: I days, then full days, then slices (§10.5); stable otherwise."""
    return sorted(jobs, key=lambda j: (j["cell"] != "I", j["hours"] is not None))


def run(jobs: list, workers: int, root: Path = ROOT) -> None:
    """Runs the jobs whose output is missing; a failed job is retried once (§10.6)."""
    todo = [j for j in order(jobs) if not out_path(j, root).exists()]
    env = clean_sumo_env()
    print(f"{len(todo)} of {len(jobs)} jobs to run, cpu {_cpu_util():.0f} %", flush=True)

    def one(j):
        p = out_path(j, root)
        p.parent.mkdir(parents=True, exist_ok=True)
        for attempt in (1, 2):
            while _cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
                time.sleep(30)
            t0 = time.time()
            r = subprocess.run(["nice", "-n", "10", *argv(j, root)], cwd=REPO_ROOT, env=env, capture_output=True,
                               text=True)
            if r.returncode == 0 and p.exists():
                return j, attempt, round(time.time() - t0), ""
        (p.parent / "FAILED.txt").write_text(r.stderr[-4000:])
        return j, 0, round(time.time() - t0), r.stderr[-300:]

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for i, (j, att, wall, err) in enumerate(ex.map(one, todo), 1):
            tag = f"{j['stage']}/{j['cell']}/{j['arm']}/{j['point']}/ss{j['ss'] or j['seed']}/s{j['seed']}"
            print(("FAIL " if not att else "done ") + tag, f"attempt {att}", f"{wall} s", f"[{i}/{len(todo)}]",
                  f"{time.time() - t0:.0f} s", err, flush=True)
    print(f"all done in {time.time() - t0:.0f} s", flush=True)


def l_bar(seed: int = L_BAR_SEED) -> float:
    """Mean vehicle length of the generated fleet on one seed (PI-ALINEA conversion, §3.2)."""
    import dataclasses

    from v5b.fleet import day, fleet as fl
    from v5b.fleet.smoke import CFG
    cfg = fl.apply_plant(PLANT, dataclasses.replace(CFG))
    dem = fl.FleetDemand(seed, day.profile(ADT), cfg)
    return sum(v.length for v in dem.veh) / len(dem.veh)


def meter_ctrl(law: str, o: float, overrides: bool = True, k_r: float = 70.0, pi: tuple = WANG,
               l_bar_m: float = 5.2, rate: float | None = None) -> dict:
    if law == "fixed":
        return {"law": "fixed", "rate": rate, "overrides": overrides, "loop": "alinea"}
    if law == "alinea":
        return {"law": "alinea", "loop": "alinea", "setpoint": o, "k_r": k_r, "overrides": overrides}
    k_p, k_i = ct.pi_gains(*pi, l_bar_m)
    return {"law": "pi", "loop": "drop", "setpoint": o, "k_p": round(k_p, 4), "k_i": round(k_i, 4),
            "overrides": overrides}


def alks_ctrl(o: float | None, zone: str = "long", k_i: float = 0.02, b_min: float = ct.B_MIN,
              fixed_b: float | None = None, loop: str = "drop") -> dict:
    c = {"loop": loop, "zone": zone, "k_i": k_i, "b_min": b_min}
    return c | ({"fixed_b": fixed_b} if fixed_b is not None else {"setpoint": o})


def wave1(l_bar_m: float) -> list:
    """§10.2: NC full days and twins in both cells, T0 slices, provisional smoke days (no outcome is read)."""
    st, js = "stage0_w1", []
    for s in THROWAWAY:
        for cell in ("R", "I"):
            js += [job(st, cell, "nc", "base", s), job(st, cell, "nc", "base", s, s + TWIN)]
    sl = "15,19"
    a, b = THROWAWAY[0], THROWAWAY[1]
    js += [job(st, "R", "nc", "slice", a, hours=sl), job(st, "R", "nc", "slice", b, hours=sl),
           job(st, "I", "nc", "slice", a, hours=sl)]
    for rate, s, ovr in ((300.0, a, False), (450.0, a, False), (500.0, b, False), (300.0, b, True)):
        js.append(job(st, "R", "t0_meter", f"r{rate:g}_{'ovr' if ovr else 'test'}", s,
                      ctrl={"meter": meter_ctrl("fixed", 0.0, ovr, rate=rate)}, hours=sl))
    for cell in ("R", "I"):
        js.append(job(st, cell, "t0_alks", "b0.5_long", a, ctrl={"alks": alks_ctrl(None, fixed_b=0.5)}, hours=sl))
    o = WAVE1_PROVISIONAL_O
    smoke = {"ma": {"meter": meter_ctrl("alinea", o)}, "mp": {"meter": meter_ctrl("pi", o, l_bar_m=l_bar_m)},
             "c": {"alks": alks_ctrl(o)},
             "mc": {"meter": meter_ctrl("pi", o, l_bar_m=l_bar_m), "alks": alks_ctrl(o), "cascade": True}}
    js += [job(st, "I", f"smoke_{k}", "provisional", b, ctrl=c) for k, c in smoke.items()]
    return js


def main(argv_=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--jobs", required=True, help="job list JSON")
    r.add_argument("--workers", type=int, default=16)
    m = sub.add_parser("make")
    m.add_argument("--wave", choices=("w1",), required=True)
    m.add_argument("--out", required=True)
    a = ap.parse_args(argv_)
    if a.cmd == "make":
        lb = l_bar()
        js = wave1(lb)
        Path(a.out).write_text(json.dumps({"l_bar_m": lb, "jobs": js}, indent=1))
        print(f"{len(js)} jobs, L_bar {lb:.4f} m")
    else:
        run(json.loads(Path(a.jobs).read_text())["jobs"], a.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
