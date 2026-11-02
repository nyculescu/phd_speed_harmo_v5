"""E1 headroom check (V213, docs/research/protocols/e1_headroom.md): job lists, the runner and the stage analyses.

A job is one day (or slice) of `v5b.fleet.day one` on plant v199 at ADT 45,000. Outputs go to
ROOT/<stage>/<cell>/<arm>/<point>/ss<sumo seed>/day_s<seed>.json, so twins and arms never share a file name. Jobs
run as `python -m v5b.fleet.day one`, which the CPU guard pattern `v5b\\.fleet\\.(day|weather|incident) one` matches.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

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
PI_WINDOW = 180.0                  # V226: PI-ALINEA reads the 3-min mean drop-loop occupancy
HOLD_MARGIN = 60.0                 # V226: the T0 hold test skips breakdown episodes ± 60 s


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


MAIN_STAGES = ("A", "B", "C1", "C2", "L")
MAX_WORKERS = 27                           # §10.6


def matches(d: dict, j: dict) -> bool:
    """A stored run belongs to this job: same controller, SUMO seed, hours, simulation code, plant and the inputs that
    argv() passes (V234)."""
    from v5b.fleet.day import code_id
    inputs = {"adt": ADT, "crash_k": 0.0 if j["cell"] == "I" else None, "blocker": BLOCKER if j["cell"] == "I" else None,
              "forced": None}
    return (d.get("ctrl") == j["ctrl"] and d.get("sumo_seed") == j["ss"] and d.get("hours") == j["hours"]
            and d.get("code") == code_id() and d.get("plant") == PLANT and d.get("inputs") == inputs)


def package_temp() -> float | None:
    """CPU package temperature in °C from hwmon (coretemp), logged per batch (§10.5)."""
    for h in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            if (h / "name").read_text().strip() == "coretemp":
                return int((h / "temp1_input").read_text()) / 1000.0
        except OSError:
            continue
    return None


def run(jobs: list, workers: int, root: Path = ROOT) -> None:
    """Runs the jobs whose output is missing; a failed job is retried once, and a second failure, or a main-stage run
    that breaks a §10.6 stop rule, stops new launches (§10.6). A stored run with other settings, or a job folder that
    holds FAILED.txt, or a STOP.txt in root, refuses the batch: archive it first. A job whose attempt 1 failed before a
    stop gets one attempt on resume (ATTEMPT1_FAILED.txt)."""
    import threading
    from concurrent.futures import as_completed
    if workers > MAX_WORKERS:
        raise SystemExit(f"at most {MAX_WORKERS} workers (§10.6)")
    todo, bad = [], []
    if (root / "STOP.txt").exists():
        bad.append(f"stop rule fired before: {root / 'STOP.txt'}")
    for j in order(jobs):
        p = out_path(j, root)
        if (p.parent / "FAILED.txt").exists():
            bad.append(f"failed before: {p.parent}")
        elif p.exists():
            if not matches(json.loads(p.read_text()), j):
                bad.append(f"stale result: {p}")
        else:
            todo.append(j)
    if bad:
        raise SystemExit("refused, archive these first:\n" + "\n".join(bad[:20]))
    env = clean_sumo_env()
    stop = threading.Event()
    print(f"{len(todo)} of {len(jobs)} jobs to run, cpu {_cpu_util():.0f} %, package {package_temp()} °C", flush=True)

    def one(j):
        p = out_path(j, root)
        p.parent.mkdir(parents=True, exist_ok=True)
        errs = []
        first = p.parent / "ATTEMPT1_FAILED.txt"
        for attempt in ((2,) if first.exists() else (1, 2)):
            while _cpu_util(1.0) > 90.0 and not stop.is_set():      # CLAUDE.md CPU rule: launch only below 90 %
                time.sleep(30)
            if stop.is_set():
                if errs:
                    first.write_text("\n".join(errs))
                    return j, -1, 0, "stopped after a failed attempt 1"
                return j, -1, 0, "not started: stopped"
            t0 = time.time()
            r = subprocess.run(["nice", "-n", "10", *argv(j, root)], cwd=REPO_ROOT, env=env, capture_output=True,
                               text=True)
            if r.returncode == 0 and p.exists():
                why = stop_reasons(json.loads(p.read_text()), j["cell"]) if j["stage"] in MAIN_STAGES else []
                if why:
                    stop.set()
                    (root / "STOP.txt").open("a").write(f"{p}: {', '.join(why)}\n")
                    return j, attempt, round(time.time() - t0), "STOP " + ", ".join(why)
                return j, attempt, round(time.time() - t0), ""
            errs.append(f"attempt {attempt}:\n{r.stderr[-4000:]}")
        (p.parent / "FAILED.txt").write_text("\n".join(([first.read_text()] if first.exists() else []) + errs))
        stop.set()
        (root / "STOP.txt").open("a").write(f"{p}: second process failure\n")
        return j, 0, round(time.time() - t0), r.stderr[-300:]

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(one, j) for j in todo]
        for i, f in enumerate(as_completed(futs), 1):
            j, att, wall, err = f.result()
            tag = f"{j['stage']}/{j['cell']}/{j['arm']}/{j['point']}/ss{j['ss'] or j['seed']}/s{j['seed']}"
            word = "done " if att > 0 else "FAIL " if att == 0 else "skip "
            print(word + tag, f"attempt {att}", f"{wall} s", f"[{i}/{len(todo)}]", f"{time.time() - t0:.0f} s", err,
                  flush=True)
    print(f"all done in {time.time() - t0:.0f} s, package {package_temp()} °C" + (", STOPPED" if stop.is_set() else ""),
          flush=True)


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
            "overrides": overrides, "window": PI_WINDOW}


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


def wave1b(l_bar_m: float) -> list:
    """V215: the wave-1 jobs that used the stop-held blocker or the pre-review controllers, re-run from the fixed
    code into stage0_w1b (I days, I slice, smoke, T0 and their NC R slices); the NC R days stand."""
    return [dict(j, stage=W1B) for j in wave1(l_bar_m)
            if j["cell"] == "I" or j["arm"] in ("t0_meter", "t0_alks") or (j["arm"], j["point"]) == ("nc", "slice")]


W1B = "stage0_w1b"


def wave2c(cal: dict, l_bar_m: float) -> list:
    """V226: the T0 meter and ALKS slices, the meter gain check and the self-reaction slices again, after the
    kinematic amber, the PI-ALINEA input window and the ALKS T0 measures (their old results are archived first)."""
    return ([j for j in wave1b(l_bar_m) if j["arm"] in ("t0_meter", "t0_alks")]
            + [j for j in wave2a(cal, l_bar_m) if j["arm"] in ("gain_alinea", "gain_pi", "self_alks")])


SMOKE_CONST = {"meter": {"STOP_DECEL": 3.0, "STOP_MARGIN": 5.0, "AMBER_CAR": 1.0, "AMBER_ONSET": 5.0, "G_MIN": 2.0,
                         "G_MAX": 4.0, "NEAR_SPEED": 3.0, "APPROACH_SPEED": 3.0, "SKIP_SERVED": True},   # V226, V228
               "alks": {"A_CAP": 1.5, "V_ALKS": 100.0 / 3.6, "ZONE_END": 892.0, "FREE_GAP": 120.0}}
SMOKE_HOURS = "15,17"


def _occ_at(d: dict, loop: str, t: float, n: int) -> float:
    from v5b.fleet.e1_analysis import loop_arrays
    ts, _, o = loop_arrays(d, loop)
    x = o[ts <= t + 1e-6][-n:]
    return float(x.mean()) if x.size else 0.0


def smoke_check(d: dict, j: dict) -> dict:
    """V231: the run carries the job's inputs. Config echo, the law parameters read back, the actuator constants,
    and the occupancy each law used equals the mean of its loop over its window. 'active' says whether the
    controller acted, i.e. whether the alignment was exercised."""
    bad, c = [], j["ctrl"] or {}
    if d.get("ctrl") != j["ctrl"] or d.get("hours") != j["hours"] or d.get("sumo_seed") != j["ss"] or d.get("plant") != PLANT:
        bad.append("config echo")
    if not valid(d):
        bad.append("invalid run")
    active = {}
    if "meter" in c:
        m, cm = d["meter"], c["meter"]
        want = {"kind": cm["law"], "setpoint": cm.get("setpoint", 0.0), "k_r": cm.get("k_r", 70.0),
                "k_p": cm.get("k_p", 0.0), "k_i": cm.get("k_i", 0.0), "rate": cm.get("rate", ct.R_MAX)}
        if cm["law"] == "fixed":
            want = {"kind": "fixed", "rate": cm["rate"]}
        bad += [f"meter law {k}" for k, v in want.items() if m["law"].get(k) != v]
        if m["loop"] != cm.get("loop", "alinea") or m["window"] != cm.get("window", 60.0):
            bad.append("meter loop or window")
        if m.get("constants") != SMOKE_CONST["meter"]:
            bad.append("meter constants")
        n = int(round(m["window"] / 30.0))
        off = [r[0] for r in m["log"] if abs(r[3] - _occ_at(d, m["loop"], r[0], n)) > 0.01
               or abs(r[11] - _occ_at(d, m["loop"], r[0], 2)) > 0.01]
        if off:
            bad.append(f"meter input occupancy off at {len(off)} minutes")
        active["meter"] = m["metering_s"] > 0
    if "alks" in c:
        a, ca = d["alks"], c["alks"]
        want = {"setpoint": ca.get("setpoint", 0.0), "k_i": ca.get("k_i", 0.02), "b_min": ca.get("b_min", ct.B_MIN),
                "fixed_b": ca.get("fixed_b"), "zone": ca.get("zone", "long"), "loop": ca.get("loop", "drop")}
        bad += [f"alks {k}" for k, v in want.items() if a.get(k) != v]
        if (a["x_cmd"], a["x_hold"]) != tuple(round(x, 1) for x in ct.ZONES[want["zone"]]):
            bad.append("alks zone geometry")
        if a.get("constants") != SMOKE_CONST["alks"]:
            bad.append("alks constants")
        off = [r[0] for r in a["log"] if abs(r[2] - _occ_at(d, a["loop"], r[0], 2)) > 0.01]
        if off:
            bad.append(f"alks input occupancy off at {len(off)} minutes")
        active["alks"] = a["cmd_steps"] > 0
    if c.get("cascade") != (d.get("ctrl") or {}).get("cascade"):
        bad.append("cascade flag")
    return {"ok": not bad, "bad": bad, "active": active}


def smoke_jobs(jobs: list) -> list:
    """One short slice per distinct controller in a job list, on its first seed and SUMO seed, in a folder per
    simulation code, so a repeat after a code change runs again (V234)."""
    from v5b.fleet.day import code_id
    seen, out, code = set(), [], code_id()
    for j in jobs:
        k = json.dumps(j["ctrl"], sort_keys=True)
        if j["ctrl"] and k not in seen:
            seen.add(k)
            out.append(dict(j, stage=f"smoke/{code}", hours=SMOKE_HOURS, point=f"{j['point']}_{len(out)}"))
    return out


def wave2d(cal: dict, l_bar_m: float) -> list:
    """V228: the T0 meter slices and the ALINEA gain check again, after the 3.0 m/s² amber threshold."""
    return [j for j in wave2c(cal, l_bar_m) if j["arm"] in ("t0_meter", "gain_alinea")]


def pick_n(ns: list) -> int:
    """§9.3: both cells use the larger n; a cell without 0.80 power at 20 (None) still runs at 20."""
    return 20 if None in ns else max(ns)


def _day(st: Path, cell: str, arm: str, point: str, seed: int, ss: int | None = None) -> dict | None:
    p = st / cell / arm / point / f"ss{ss or seed}" / f"day_s{seed}.json"
    return json.loads(p.read_text()) if p.exists() else None


def valid(d: dict) -> bool:
    """§7.7: drained, no teleport, no SUMO error, no physical contact, every vehicle arrived or removed."""
    return bool(d["drained"] and d["teleports"] == 0 and d["sumo_errors"] == 0 and d["contacts"] == 0
                and d["arrived_plus_removed"] == d["generated"])


def braking_by_lane(log: Path, lanes: tuple = ("r_0", "rj_0", ":rm")) -> int:
    """Emergency-braking warnings on the meter's lanes, from a day's SUMO log."""
    if not log.exists():
        return None
    return sum(1 for ln in log.read_text(errors="replace").splitlines()
               if "performs emergency braking" in ln and any(f"lane '{x}" in ln for x in lanes))


def _flow(d: dict, group: str) -> float:
    from v5b.fleet.e1_analysis import loop_arrays
    _, q, _ = loop_arrays(d, group)
    return float(q.sum())


def _occ(d: dict, group: str) -> float:
    from v5b.fleet.e1_analysis import loop_arrays
    _, _, o = loop_arrays(d, group)
    return float(o.sum())


def ratio_rows(m: dict, min_queue: int = 3) -> list:
    """(commanded, realised) per clean metered minute: the rate set at minute k-1 for minute k against the releases
    counted at k; metering, no override, backstop, downstream-limited or supply-limited second (V228), >= 3 vehicles
    on r_0 at its start."""
    lg = m["log"]
    return [(a[1], b[2]) for a, b in zip(lg, lg[1:])
            if a[6] and not (b[7] or b[9] or (len(b) > 12 and b[12])) and a[4] >= min_queue]


def meter_ratio(m: dict, min_queue: int = 3) -> list:
    """T0: realised / commanded per 5 clean minutes, not necessarily adjacent (the V234 reading of §10.3's 5-min
    interval; meter_ratio_clock gives the clock-interval reading, report-only)."""
    rows = ratio_rows(m, min_queue)
    return [round(sum(b for _, b in rows[i:i + 5]) / sum(a for a, _ in rows[i:i + 5]), 3)
            for i in range(0, len(rows) - 4, 5)]


def meter_ratio_clock(m: dict, min_queue: int = 3) -> list:
    """Report-only (V234): realised / commanded over the clean minutes inside each clock 5-min interval, with their
    number."""
    lg, by = m["log"], {}
    for a, b in zip(lg, lg[1:]):
        if a[6] and not (b[7] or b[9] or (len(b) > 12 and b[12])) and a[4] >= min_queue:
            c, r, k = by.get(b[0] // 300, (0.0, 0.0, 0))
            by[b[0] // 300] = (c + a[1], r + b[2], k + 1)
    return [(round(r / c, 3), k) for _, (c, r, k) in sorted(by.items())]


def stop_reasons(d: dict, cell: str) -> list:
    """§10.6 and §7.5 stop rules of one main-stage run."""
    why = []
    if not valid(d):
        why.append("invalid run (drain, teleport, SUMO error, contact or vehicle count)")
    m, a = d.get("meter"), d.get("alks")
    if m:
        if m["red_passages"]:
            why.append("red passage")
        if (m.get("max_red_exposure_s") or 0.0) > 245.0:
            why.append("red exposure above 245 s")
        rows = ratio_rows(m)
        if rows and not 0.90 <= sum(b for _, b in rows) / sum(x for x, _ in rows) <= 1.10:
            why.append("meter actuator fault")
    if a:
        if a["cap_violations"] or a["restore_mismatch"] or a.get("allowed_mismatch"):     # V226 exact restore
            why.append("ALKS invariant")
        if a["compliance"] is not None and a["compliance"] < 0.90:
            why.append("ALKS compliance below 90 %")
    if cell == "I" and not (d.get("blocker") or {}).get("x_stop"):
        why.append("blocker did not stop")
    return why


def report_w1(root: Path = ROOT, r_only: bool = False) -> dict:
    """§10.3 criteria on wave 1. Reads checks only: no controller outcome (delay of a controlled run) is used.
    NC R days come from stage0_w1, everything else from stage0_w1b (V215). r_only: the R-day checks and the
    calibration that wave 2a needs."""
    from v5b.fleet import e1_analysis as ea
    st, sb = root / "stage0_w1", root / W1B
    ref = json.loads((REPO_ROOT / "docs/research/results/fleet_v190_tpoff_v0.json").read_text())["reference_days"]
    out, stop = {}, []
    cells = ("R",) if r_only else ("R", "I")
    src = {"R": st, "I": sb}
    base = {c: {s: _day(src[c], c, "nc", "base", s) for s in THROWAWAY} for c in cells}
    twin = {c: {s: _day(src[c], c, "nc", "base", s, s + TWIN) for s in THROWAWAY} for c in cells}
    missing = [(c, s) for c in cells for s in THROWAWAY if base[c][s] is None or twin[c][s] is None]
    if missing:
        return {"incomplete": missing}
    out["validity"] = {c: {"base": sum(valid(d) for d in base[c].values()), "twin": sum(valid(d) for d in twin[c].values())}
                       for c in cells}
    if any(v != 10 for c in out["validity"].values() for v in c.values()):
        stop.append("invalid NC day")
    inert = {s: base["R"][s]["hash"] == ref[f"day_s{s}"]["hash"] for s in THROWAWAY}
    out["inert_hashes_match"] = sum(inert.values())
    if out["inert_hashes_match"] != 10:
        stop.append("NC R days do not reproduce the V198 hashes")
    tw = {c: {"route_same": sum(base[c][s]["route_sha1"] == twin[c][s]["route_sha1"] for s in THROWAWAY),
              "hash_differs": sum(base[c][s]["hash"] != twin[c][s]["hash"] for s in THROWAWAY)} for c in cells}
    out["twins"] = tw
    if any(v != 10 for c in tw.values() for v in c.values()):
        stop.append("twin check")
    pm = [ea.main_pm(d["series"]) for d in base["R"].values()]
    drops = [e and e["drop"] for e in pm]
    dd = [x for x in drops if x is not None]
    out["T1"] = {"pm_drop_per_day": drops, "median_drop": float(np.median(dd)) if dd else None,
                 "qdf": [e and e["qdf"] for e in pm], "main_pm": pm}
    if not dd or np.median(dd) < 0.02:
        stop.append("T1: median drop below 2 %")
    cal = ea.calibrate(list(base["R"].values()))
    out["calibration"] = cal
    if cal["stop"]:
        stop.append("calibration: onset, drop loop or alinea_3 test")
    jl = root / "w1_jobs.json"
    out["l_bar_m"] = json.loads(jl.read_text())["l_bar_m"] if jl.exists() else None
    if r_only:
        out["stop"] = stop
        return out
    out["power"] = {}
    for c in cells:
        dn = np.array([base[c][s]["d_all"] for s in THROWAWAY])
        d0 = dn - np.array([twin[c][s]["d_all"] for s in THROWAWAY])
        sc = float(np.std(d0, ddof=1) / np.median(dn))
        ch = ea.choose_n(sc)
        ch["s"], ch["median_D_NC"] = sc, float(np.median(dn))
        out["power"][c] = ch
    ns = [out["power"][c]["n"] for c in cells]
    out["underpowered_cells"] = [c for c in cells if out["power"][c]["n"] is None]
    # §9.3: an underpowered cell still runs at 20, and both cells use the larger n; floors at the n that runs
    out["n"] = pick_n(ns)
    for c in cells:
        nf = ea.noise_floors(out["power"][c]["s"], out["n"])
        out["power"][c]["noise_floors"] = nf
        out["power"][c]["global_null"] = ea.global_null(out["power"][c]["s"], out["n"], nf["rule2_tuned_replicate"])
    out["I_minus_R_D_NC"] = {s: round(base["I"][s]["d_all"] - base["R"][s]["d_all"], 2) for s in THROWAWAY}
    pre = {}
    for s in THROWAWAY:
        a = [x for x in base["R"][s]["series"] if x[0] <= 57600.0]
        b = [x for x in base["I"][s]["series"] if x[0] <= 57600.0]
        la = [x for x in base["R"][s]["loops30"]["rows"] if x[0] <= 57600.0]
        lb = [x for x in base["I"][s]["loops30"]["rows"] if x[0] <= 57600.0]
        pre[s] = a == b and la == lb
    out["prefix_match"] = sum(pre.values())
    if out["prefix_match"] != 10:
        stop.append("R/I prefix mismatch")
    out["blocker"] = {s: base["I"][s]["blocker"] for s in THROWAWAY}
    if any(b is None or b.get("x_stop") is None for b in out["blocker"].values()):
        stop.append("blocker did not stop on every NC I day")
    for name in ("eta", "eta_mid", "eta_hold", "eta_hold_mid"):
        p = st / name / "analysis.json"
        out[name] = json.loads(p.read_text())["chosen"] if p.exists() else None
    e = out["eta_hold"]                        # V215 A1: the held blocker replaced the stop hold
    if e is None or not (abs(e["eta_median"] - 0.54) <= 0.05 and e["n_valid"] >= 8):
        stop.append("blocker eta check")
    out["T0"] = t0_report(sb)
    stop += [f"T0 {k}" for k, v in out["T0"].items() if not v.get("pass", True)]
    sm = {}
    for k in ("ma", "mp", "c", "mc"):
        d = _day(sb, "I", f"smoke_{k}", "provisional", THROWAWAY[1])
        sm[k] = None if d is None else {
            "valid": valid(d), "blocker_stopped": bool(d["blocker"] and d["blocker"].get("x_stop")),
            "schema": all(d.get(x) is not None for x in ("d_all", "d_ramp", "served", "ttt_w_h", "loops30", "route_sha1",
                                                          "d_recovery")) and (d["meter"] or d["alks"]) is not None,
            "removed_handling": d["removed_ids"] == [d["blocker"]["vid"]] and d["arrived_plus_removed"] == d["generated"]
            and _n_trips(sb, "I", f"smoke_{k}", "provisional", THROWAWAY[1]) == d["generated"] - 1,
            "wall_s": d["wall_s"]}
    out["smoke"] = sm
    if any(v is None or not (v["valid"] and v["blocker_stopped"] and v["schema"] and v["removed_handling"])
           for v in sm.values()):
        stop.append("smoke")
    out["wall_s_I_days"] = [base["I"][s]["wall_s"] for s in THROWAWAY]
    out["stop"] = stop
    return out


def _scalars(x: dict | None) -> dict | None:
    return None if x is None else {k: v for k, v in x.items() if not isinstance(v, (list, dict))}


def _n_trips(st: Path, cell: str, arm: str, point: str, seed: int) -> int:
    with np.load(out_dir(st, cell, arm, point, seed) / f"trips_s{seed}.npz") as z:
        return int(z["delay"].size)


def _ttc_behind(st: Path, cell: str, arm: str, point: str, seed: int, ids: set) -> int:
    """T0 (§10.3, report-only): human TTC < 1.5 s records whose leader is one of the given ALKS."""
    p = out_dir(st, cell, arm, point, seed) / f"conflicts_s{seed}.npz"
    if not p.exists():
        return -1
    with np.load(p) as z:
        lead = z["leader"][z["ttc"] < 1.5]
    return int(sum(f"main.{i}" in ids for i in lead))


def hold_uncongested(d: dict, blockage: bool = False) -> list:
    """V226 (V215 A5): speed minus c of free held ALKS in seconds outside the run's own drop-loop breakdown
    episodes ± 60 s; blockage = True (report-only) also skips the blocker's stop."""
    from v5b.fleet.e1_analysis import _episodes
    ep = _episodes(d["series"], 7)
    if blockage and d.get("blocker"):
        ep.append((d["blocker"]["t"], d["blocker"]["t"] + d["blocker"]["duration"]))
    return [x for t, x in d["alks"].get("hold_free", [])
            if not any(a - HOLD_MARGIN <= t <= b + HOLD_MARGIN for a, b in ep)]


def t0_report(st: Path) -> dict:
    """§10.3 T0 meter and CAV criteria against the paired NC slices."""
    a, b = THROWAWAY[0], THROWAWAY[1]
    nc = {("R", a): _day(st, "R", "nc", "slice", a), ("R", b): _day(st, "R", "nc", "slice", b),
          ("I", a): _day(st, "I", "nc", "slice", a)}
    res = {}
    for point, s in (("r300_test", a), ("r450_test", a), ("r500_test", b), ("r300_ovr", b)):
        d, n = _day(st, "R", "t0_meter", point, s), nc[("R", s)]
        if d is None or n is None:
            res[point] = {"pass": False, "missing": True}
            continue
        m = d["meter"]
        ratio = meter_ratio(m)
        lanes = [e.get("lane", "") for e in d["collision_events"]]
        r = {"ratio": ratio, "ratio_ok": bool(ratio) and all(0.95 <= x <= 1.05 for x in ratio),
             "ratio_clock": meter_ratio_clock(m),
             "red_passages": m["red_passages"], "contacts": d["contacts"],
             "intrusions_ramp": sum(1 for x in lanes if x.startswith(("r_", "rj_", "3a_", ":rm"))),
             "braking": braking_by_lane(out_dir(st, "R", "t0_meter", point, s) / f"sumo_s{s}.log"),
             "braking_nc": braking_by_lane(out_dir(st, "R", "nc", "slice", s) / f"sumo_s{s}.log"),
             "ramp_flow_differs": _flow(d, "ramp_out") != _flow(n, "ramp_out"),
             "alinea_occ_differs": _occ(d, "alinea") != _occ(n, "alinea"),
             "merge": _scalars(d["ramp_merge"]), "merge_nc": _scalars(n["ramp_merge"]), "amber_kin": m.get("amber_kin")}
        common = (r["red_passages"] == 0 and r["contacts"] == 0 and r["intrusions_ramp"] == 0
                  and r["braking"] is not None and r["braking_nc"] is not None and r["braking"] <= r["braking_nc"]
                  and r["ramp_flow_differs"] and r["alinea_occ_differs"])
        r["pass"] = r["ratio_ok"] and common
        if point == "r300_ovr":
            # overrides make most minutes unclean; the ratio applies to the clean ones that remain
            r |= {"override_s": m["override_s"], "backstop_s": m["backstop_s"], "max_red_exposure_s": m["max_red_exposure_s"]}
            r["pass"] = (common and (not ratio or r["ratio_ok"]) and m["override_s"] > 0 and m["backstop_s"] > 0
                         and m["max_red_exposure_s"] <= 245.0)
        res[point] = r
    for cell in ("R", "I"):
        d, n = _day(st, cell, "t0_alks", "b0.5_long", a), nc[(cell, a)]
        if d is None or n is None:
            res[f"alks_{cell}"] = {"pass": False, "missing": True}
            continue
        k = d["alks"]
        free = [v for v, g in k["recovery"] if g is None or g > 100.0]
        unc = hold_uncongested(d)
        r = {"cap_violations": k["cap_violations"], "restore_mismatch": k["restore_mismatch"],
             "allowed_mismatch": k.get("allowed_mismatch"), "compliance": k["compliance"],
             "max_decel": k["max_decel"], "hold_excess_p95": k["hold_excess_p95"],
             "hold_free_mean_all": k.get("hold_free_mean"), "hold_free_n_all": k.get("hold_free_n", 0),
             "hold_free_mean": round(float(np.mean(unc)), 3) if unc else None, "hold_free_n": len(unc),
             "recovered_share": round(sum(v >= 0.9 for v in free) / len(free), 3) if free else None, "n_free": len(free),
             "drop_flow_differs": _flow(d, "drop") != _flow(n, "drop") or _occ(d, "drop") != _occ(n, "drop"),
             "contacts": d["contacts"], "max_decel_any_cause": k["max_decel_any_cause"],
             "ttc15_behind_commanded": _ttc_behind(st, cell, "t0_alks", "b0.5_long", a, set(k["commanded_ids"])),
             "ttc15_behind_same_ids_nc": _ttc_behind(st, cell, "nc", "slice", a, set(k["commanded_ids"]))}
        r["pass"] = (r["cap_violations"] == 0 and r["restore_mismatch"] == 0 and r["allowed_mismatch"] == 0
                     and (r["compliance"] or 0) >= 0.95 and r["max_decel"] <= 1.6 and r["hold_free_n"] >= HOLD_MIN_N
                     and abs(r["hold_free_mean"]) <= 1.0 and r["drop_flow_differs"] and r["contacts"] == 0)
        if cell == "I":
            u = hold_uncongested(d, blockage=True)
            r["hold_free_mean_outside_blockage"] = (round(float(np.mean(u)), 3) if u else None, len(u))
        r["recovery_note"] = "report-only (V226); the exact-restore stop rule also runs on the off-peak slices"
        res[f"alks_{cell}"] = r
    return res


def out_dir(st: Path, cell: str, arm: str, point: str, seed: int, ss: int | None = None) -> Path:
    return st / cell / arm / point / f"ss{ss or seed}"


K_R_CAND = (35.0, 70.0, 140.0)
PI_CAND = {"wang": WANG, "conservative": CONSERVATIVE}
K_I_CAND = (0.005, 0.01, 0.02, 0.04, 0.08, 0.16)
NOMINAL = {"alinea": "kr70", "pi": "wang", "mtfc": "ki0.02"}
GAIN_SEEDS = THROWAWAY[:3]
HOLD_MIN_N = 30                            # free ALKS-seconds in the held stretch for the T0 hold test (V215 A5)


def gain_points(cal: dict, l_bar_m: float) -> dict:
    """§10.4 candidates at 0.95 x ô_cr: law -> {candidate: ctrl}."""
    om, od, loop = 0.95 * cal["o_cr"]["alinea"], 0.95 * cal["o_cr"][cal["drop_loop"]], cal["drop_loop"]
    pi = {k: meter_ctrl("pi", od, pi=v, l_bar_m=l_bar_m) | {"loop": loop} for k, v in PI_CAND.items()}
    return {"alinea": {f"kr{k:g}": {"meter": meter_ctrl("alinea", om, k_r=k)} for k in K_R_CAND},
            "pi": {k: {"meter": c} for k, c in pi.items()},
            "mtfc": {f"ki{k:g}": {"alks": alks_ctrl(od, "long", k_i=k, loop=loop)} for k in K_I_CAND}}


def wave2a(cal: dict, l_bar_m: float) -> list:
    """§10.4: the gain check (R, 13:00-20:00) and the self-reaction slices (10:00-13:00, also the ALKS recovery test)."""
    st, js = "stage0_w2", []
    for law, cands in gain_points(cal, l_bar_m).items():
        for k, c in cands.items():
            js += [job(st, "R", f"gain_{law}", k, s, ctrl=c, hours="13,20") for s in GAIN_SEEDS]
    for s in GAIN_SEEDS:
        js += [job(st, "R", "nc", "offpeak", s, hours="10,13"),
               job(st, "R", "self_alks", "b0.5_long", s, ctrl={"alks": alks_ctrl(None, fixed_b=0.5, loop=cal["drop_loop"])},
                   hours="10,13")]
    return js


def swings(x: list, top: float, bottom: float) -> int:
    """Top -> bottom -> top cycles in a sequence."""
    n, state = 0, None
    for v in x:
        if v >= top:
            if state == "down":
                n += 1
            state = "top"
        elif v <= bottom and state == "top":
            state = "down"
    return n


def max_swings_per_hour(t: list, x: list, active: list, top: float, bottom: float) -> int:
    """The most swings in any 60-min window (starting at each sample) that contains active control."""
    best = 0
    for t0 in t:
        k = [i for i, ti in enumerate(t) if t0 <= ti < t0 + 3600]
        if any(active[i] for i in k):
            best = max(best, swings([x[i] for i in k], top, bottom))
    return best


def gain_stats(d: dict, law: str) -> dict:
    """Swing count, lead time and the RMS of the controlled occupancy around ô, from one gain-check slice."""
    from v5b.fleet.e1_analysis import drop_onset
    onset = drop_onset(d["series"], start=13 * 3600.0)
    if law == "mtfc":
        a = d["alks"]
        t, x, o = [r[0] for r in a["log"]], [r[1] for r in a["log"]], [r[2] for r in a["log"]]
        act = [v < 1.0 for v in x]
        sw = max_swings_per_hour(t, x, act, 0.9, 0.4)
        ref = a["setpoint"]
    else:
        m = d["meter"]
        # the RMS is on the raw 60-s occupancy (element 11), not on a filtered law input (V226)
        t, x, o = [r[0] for r in m["log"]], [r[1] for r in m["log"]], [r[11] if len(r) > 11 else r[3] for r in m["log"]]
        act = [bool(r[6]) for r in m["log"]]        # §10.4 r < 900 is the applied rate: 900 while resting green
        sw = max_swings_per_hour(t, x, act, 850.0, 300.0)
        ref = m["law"]["setpoint"]
    on = [ti for ti, a_ in zip(t, act) if a_]
    # a row's flag is the mode for the next minute, whose occupancy the next row logs (V234)
    pair = [(oi, a_) for oi, a_ in zip(o[1:], act[:-1]) if a_]
    rms = math.sqrt(sum((oi - ref) ** 2 for oi, _ in pair) / len(pair)) if pair else None
    return {"swings": sw, "acts": bool(on), "lead": bool(onset is None or (on and on[0] < onset)), "rms": rms,
            "onset": onset, "first_active": on[0] if on else None}


def choose_gain(stats: dict, law: str) -> dict:
    """§10.4: exclude swinging candidates, prefer lead time (drop-loop laws), then the lowest median RMS; the nominal
    wins within 10 %; a candidate that never acts on >= 2 of 3 seeds has no RMS."""
    ok = {k: v for k, v in stats.items() if sum(x["swings"] > 2 for x in v) < 2}
    if not ok:
        return {"choice": None, "stop": True}
    if law in ("pi", "mtfc"):
        lead = {k: v for k, v in ok.items() if sum(x["lead"] for x in v) >= 2}
        ok = lead or ok
    rms = {k: float(np.median([x["rms"] for x in v if x["rms"] is not None])) for k, v in ok.items()
           if sum(x["acts"] for x in v) >= 2}
    nom = NOMINAL[law]
    if not rms:
        if nom in ok:
            return {"choice": nom, "rms": {}, "kept": sorted(ok), "stop": False,
                    "note": "no candidate acts on >= 2 of 3 seeds: nominal"}
        return {"choice": None, "rms": {}, "kept": sorted(ok), "stop": True,
                "note": "no candidate acts and the nominal is excluded"}
    best = min(rms, key=rms.get)
    pick = nom if nom in rms and rms[nom] <= 1.10 * rms[best] else best
    return {"choice": pick, "rms": rms, "kept": sorted(ok), "stop": False}


def report_w2a(cal: dict, l_bar_m: float, root: Path = ROOT) -> dict:
    st = root / "stage0_w2"
    out = {}
    missing = [(law, k, s) for law, cands in gain_points(cal, l_bar_m).items() for k in cands for s in GAIN_SEEDS
               if _day(st, "R", f"gain_{law}", k, s) is None]
    if missing:
        return {"incomplete": missing}
    for law, cands in gain_points(cal, l_bar_m).items():
        stats = {k: [gain_stats(_day(st, "R", f"gain_{law}", k, s), law) for s in GAIN_SEEDS] for k in cands}
        out[law] = {"stats": stats, **choose_gain(stats, law)}
    sr = {}
    for s in GAIN_SEEDS:
        n, c = _day(st, "R", "nc", "offpeak", s), _day(st, "R", "self_alks", "b0.5_long", s)
        if n is None or c is None:
            continue
        from v5b.fleet.e1_analysis import loop_arrays
        on = [o for t, o in zip(*loop_arrays(c, cal["drop_loop"])[::2])]
        off = [o for t, o in zip(*loop_arrays(n, cal["drop_loop"])[::2])]
        free = [v for v, g in c["alks"]["recovery"] if g is None or g > 100.0]
        k = c["alks"]
        sr[s] = {"occ_rise": float(np.mean(on) / np.mean(off) - 1.0) if np.mean(off) > 0 else None,
                 "recovered_share": round(sum(v >= 0.9 for v in free) / len(free), 3) if free else None,
                 "n_free": len(free), "restores": k["restores"], "restore_mismatch": k["restore_mismatch"],
                 "allowed_mismatch": k.get("allowed_mismatch")}
    out["self_reaction"] = sr
    rises = [v["occ_rise"] for v in sr.values() if v["occ_rise"] is not None]
    out["c_loop"] = "dropend" if rises and np.median(rises) > 0.10 and cal["tests"]["dropend"]["pass"] else cal["drop_loop"]
    # V226: the stop rule is the exact restore; the recovered share is report-only
    out["recovery_pass"] = len(sr) == len(GAIN_SEEDS) and all(
        v["restores"] > 0 and v["restore_mismatch"] == 0 and v["allowed_mismatch"] == 0 for v in sr.values())
    out["pi"]["dropped"] = bool(out["pi"].get("stop"))      # V226: no admissible PI-ALINEA set drops the variant
    out["stop"] = ([f"gain: no admissible {law} candidate" for law in ("alinea", "mtfc") if out[law].get("stop")]
                   + ([] if out["recovery_pass"] else ["ALKS exact-restore test (V226)"]))
    return out


MAIN0 = 7430230
FIRST = 3                                  # seeds per point that run first (idle check, §4)


def main_seeds(n: int) -> list:
    return list(range(MAIN0, MAIN0 + n))


def fresh_seeds(n: int) -> list:
    """C1: the 10 seeds after the main set (§6)."""
    return list(range(MAIN0 + n, MAIN0 + n + 10))


def grid(fz: dict) -> dict:
    """§4: point name -> ctrl at the frozen stage-0 values fz = {o_cr, drop_loop, c_loop, gains, l_bar}."""
    om, od, oc = fz["o_cr"]["alinea"], fz["o_cr"][fz["drop_loop"]], fz["o_cr"][fz["c_loop"]]
    g, pts = fz["gains"], {}
    for sp in fz.get("setpoints", {}).get("ma", (0.85, 0.95, 1.05)):
        pts[f"ma/p{sp:g}"] = {"meter": meter_ctrl("alinea", round(sp * om, 4), k_r=g["k_r"])}
    for sp in fz.get("setpoints", {}).get("mp", (0.85, 0.95, 1.05)) if g.get("pi") else ():   # V226: may be dropped
        pts[f"mp/p{sp:g}"] = {"meter": meter_ctrl("pi", round(sp * od, 4), pi=PI_CAND[g["pi"]], l_bar_m=fz["l_bar"])
                              | {"loop": fz["drop_loop"]}}
    for zone in ("short", "long"):
        for sp in fz.get("setpoints", {}).get(f"c_{zone}", (0.85, 0.95, 1.05)):
            pts[f"c/p{sp:g}_{zone}"] = {"alks": alks_ctrl(round(sp * oc, 4), zone, k_i=g["k_i"], b_min=fz.get("b_min", ct.B_MIN),
                                                         loop=fz["c_loop"])}
    return pts


LITE_HOURS = "13,20"


def lite_jobs(fz: dict, ext: bool = False) -> list:
    """V236 E1-lite: NC and the frozen grid on PM slices in the R cell; ext = the 10 extension seeds."""
    seeds = fresh_seeds(10) if ext else main_seeds(10)
    pts = {"nc/base": None, **grid(fz)}
    return [job("L", "R", k.split("/")[0], k.split("/")[1], s, ctrl=c, hours=LITE_HOURS) for k, c in pts.items()
            for s in seeds]


def lite_report(fz: dict, ext: bool = False, root: Path = ROOT) -> dict:
    """V236 direction rule on the best arm; every arm reported."""
    from v5b.fleet import e1_analysis as ea
    seeds = main_seeds(10) + (fresh_seeds(10) if ext else [])
    pts = ["nc/base", *grid(fz)]
    runs = {k: [_day(root / "L", "R", *k.split("/"), s) for s in seeds] for k in pts}
    missing = [(k, s) for k, v in runs.items() for s, d in zip(seeds, v) if d is None]
    if missing:
        return {"incomplete": missing[:20]}
    codes = sorted({str(d.get("code")) for v in runs.values() for d in v})
    if len(codes) > 1 or (root / "STOP.txt").exists():
        return {"refused": {"codes": codes, "stop_file": (root / "STOP.txt").exists()}}
    nc_valid = all(valid(d) for d in runs["nc/base"])
    nc = np.array([d["d_all"] for d in runs["nc/base"]])
    arms = {}
    for k in pts[1:]:
        e = ea.effect(nc, np.array([d["d_all"] for d in runs[k]]))
        why = sorted({w for d in runs[k] for w in stop_reasons(d, "R")})
        arms[k] = {"rel": e["rel"], "rel_ci": e["rel_ci"], "D": e["treat"], "counts": not why, "stop": why,
                   "ttt_w_h": float(np.median([d["ttt_w_h"] for d in runs[k]])),
                   "braking": [braking_by_lane(out_dir(root / "L", "R", *k.split("/"), s) / f"sumo_s{s}.log") for s in seeds]}
    ok = {k: v for k, v in arms.items() if v["counts"]}
    best = max(ok, key=lambda k: ok[k]["rel"]) if ok else None
    b = ok.get(best)
    if not nc_valid:
        direction = "NC INVALID"
    elif b is None:
        direction = "NO VALID ARM"
    elif b["rel"] < 0.05 and b["rel_ci"][1] < 0.10:
        direction = "KILL direction"
    elif b["rel"] >= 0.10 and b["rel_ci"][0] > 0:
        direction = "GO direction"
    else:
        direction = "UNCLEAR"
    oracle = ea.effect(nc, np.min([[d["d_all"] for d in runs[k]] for k in pts], axis=0))
    return {"n": len(seeds), "D_NC_median": float(np.median(nc)), "nc_valid": nc_valid, "codes": codes,
            "nc_braking": [braking_by_lane(out_dir(root / "L", "R", "nc", "base", s) / f"sumo_s{s}.log") for s in seeds],
            "arms": arms, "best": best, "direction": direction,
            "oracle_noise_dominated": {"rel": oracle["rel"], "rel_ci": oracle["rel_ci"]}}


def floors(fz: dict, w1: dict) -> dict:
    """V234: the §9.4 noise floors and global null at the frozen grid (report_w1 assumed 12 points, 6 per family);
    Rule 2 uses the larger family."""
    from v5b.fleet import e1_analysis as ea
    pts = grid(fz)
    mf, cf = sum(k.startswith(("ma/", "mp/")) for k in pts), sum(k.startswith("c/") for k in pts)
    out = {"points": len(pts), "meter_family": mf, "cav_family": cf, "n": fz["n"]}
    for c in ("R", "I"):
        s = w1["power"][c]["s"]
        nf = ea.noise_floors(s, fz["n"], points=len(pts), family=max(mf, cf))
        out[c] = {"s": s, **nf, "global_null": ea.global_null(s, fz["n"], nf["rule2_tuned_replicate"], mf=mf, cf=cf)}
    return out


def mc_ctrl(pts: dict, m_star: str, c_star: str) -> dict:
    """§3.4: M* and C* together; a cascade when both laws use the drop loop (M* is PI-ALINEA and C kept that loop)."""
    m, c = pts[m_star], pts[c_star]
    return {**m, **c, "cascade": m_star.startswith("mp/") and m["meter"].get("loop") == c["alks"]["loop"],
            "of": f"{m_star}+{c_star}"}


def stage_a(fz: dict, n: int, first: bool, skip: tuple = ()) -> list:
    """§9.3 stage A: NC + 12 points x n seeds x 2 cells; first=True gives the first 3 seeds of every point. skip: idle
    points already replaced (§4), whose later seeds do not run."""
    seeds = main_seeds(n)[:FIRST] if first else main_seeds(n)[FIRST:]
    pts = {"nc/base": None, **{k: v for k, v in grid(fz).items() if k not in skip}}
    return [job("A", cell, k.split("/")[0], k.split("/")[1], s, ctrl=c) for cell in ("R", "I") for k, c in pts.items()
            for s in seeds]


def idle(d: dict) -> bool:
    """§4: a run where the meter meters < 5 min and b < 1 for < 5 min over the day."""
    m, a = d.get("meter"), d.get("alks")
    on_m = (m["metering_s"] >= 300) if m else False
    on_c = (sum(1 for r in a["log"] if r[1] < 1.0) >= 5) if a else False
    return not (on_m or on_c)


def idle_points(fz: dict, n: int, root: Path = ROOT) -> list:
    """Grid points idle on all 3 first seeds in both cells."""
    seeds = main_seeds(n)[:FIRST]
    out = []
    for k in grid(fz):
        ds = [_day(root / "A", cell, *k.split("/"), s) for cell in ("R", "I") for s in seeds]
        if all(d is not None and idle(d) for d in ds):
            out.append(k)
    return out


def replace_idle(fz: dict, n: int, root: Path = ROOT) -> dict:
    """§4: each idle point is replaced, once per family variant, by the next lower setpoint not in the grid (step
    0.10), run on all main seeds in both cells. Returns {idle, replaced: {idle point: new point}, extra_idle, fz, jobs}."""
    sp_of = lambda k: float(k.split("/")[1].split("_")[0][1:])      # noqa: E731
    out = {"idle": idle_points(fz, n, root), "replaced": {}, "extra_idle": []}
    new_fz, jobs = fz, []
    for k in sorted(out["idle"], key=sp_of, reverse=True):     # V234: the highest first keeps p0.95 where possible
        var = variant(k)
        if any(variant(x) == var for x in out["replaced"]):
            out["extra_idle"].append(k)
            continue
        have = {sp_of(x) for x in grid(new_fz) if VARIANTS[var](x)}
        sp = round(min(have) - EDGE_STEP_A, 2)
        while sp in have:
            sp = round(sp - EDGE_STEP_A, 2)
        sps = dict(new_fz.get("setpoints", {}))
        sps[var] = tuple(sorted((set(sps.get(var, (0.85, 0.95, 1.05))) - {sp_of(k)}) | {sp}))
        new_fz = {**new_fz, "setpoints": sps}
        key = next(x for x in grid(new_fz) if VARIANTS[var](x) and sp_of(x) == sp)
        out["replaced"][k] = key
        jobs += [job("A", cell, *key.split("/"), s, ctrl=grid(new_fz)[key]) for cell in ("R", "I") for s in main_seeds(n)]
    return {**out, "fz": new_fz, "jobs": jobs}


EDGE_STEP_A = 0.10


K_CRASH, U_CRASH = 0.001085, 1.5
BRAKE_TOL = 5.0


def expected_crashes(npz: Path) -> float:
    """§7.5: expected crashes per day from a run's conflict records (V198 offline replay rule)."""
    from v5b.fleet import crash as cr
    with np.load(npz) as z:
        m = cr.encounters(z, U_CRASH, "human")
    return float(cr.p_crash(m, K_CRASH, U_CRASH, "linear").sum())


def load_stage(stages: tuple, cell: str, seeds: list, root: Path = ROOT) -> dict:
    """point 'arm/point' -> (stage, per-seed day dicts, None if missing), over the given stage folders."""
    out = {}
    for st in stages:
        base = root / st / cell
        if not base.exists():
            continue
        for arm in sorted(p.name for p in base.iterdir() if p.is_dir()):
            for point in sorted(p.name for p in (base / arm).iterdir() if p.is_dir()):
                out[f"{arm}/{point}"] = (st, [_day(root / st, cell, arm, point, s) for s in seeds])
    return out


def _npz(root: Path, st: str, cell: str, key: str, s: int) -> Path:
    arm, pt = key.split("/")
    return root / st / cell / arm / pt / f"ss{s}" / f"conflicts_s{s}.npz"


def flags(nc: list, x: list, nc_npz: list, x_npz: list, cell: str) -> dict:
    """§7.2-7.5 flags of one arm (or of the oracle's per-day composite) against NC in one cell."""
    from v5b.fleet import e1_analysis as ea
    f = {}
    e = ea.effect(np.array([d["emergency_braking_warnings"] for d in x], float),
                  np.array([d["emergency_braking_warnings"] for d in nc], float))      # d = x - nc
    f["braking"] = bool(e["diff"] > BRAKE_TOL and e["diff_ci"][0] > 0)
    ec_nc, ec_x = [expected_crashes(p) for p in nc_npz], [expected_crashes(p) for p in x_npz]
    f["expected_crashes"] = bool(ea.effect(np.array(ec_nc), np.array(ec_x))["rel_ci"][1] < -0.05)
    pm = lambda d: d["served"]["pm"]["main"] + d["served"]["pm"]["ramp"]      # noqa: E731
    f["throughput_loss"] = ea.throughput_loss([pm(d) for d in nc], [pm(d) for d in x])
    f["ttt_conflict"] = ea.ttt_conflict([d["ttt_w_h"] for d in nc], [d["ttt_w_h"] for d in x])
    if cell == "I":
        dt = [abs((b["blocker"] or {}).get("t_stop", 1e9) - (a["blocker"] or {}).get("t_stop", 0.0)) for a, b in zip(nc, x)]
        f["incident_unbalanced"] = sum(t > 60.0 for t in dt) >= math.ceil(0.3 * len(dt))     # 3 of 10 (§5.3)
    f["intrusions"] = sum(d["mingap_intrusions"] for d in x)
    f["expected_crashes_mean"] = {"nc": float(np.mean(ec_nc)), "x": float(np.mean(ec_x))}
    return f


VARIANTS = {"ma": lambda k: k.startswith("ma/"), "mp": lambda k: k.startswith("mp/"),
            "c_short": lambda k: k.startswith("c/") and k.endswith("_short"),
            "c_long": lambda k: k.startswith("c/") and k.endswith("_long")}


def variant(key: str) -> str:
    return next(v for v, member in VARIANTS.items() if member(key))


def with_setpoint(fz: dict, var: str, sp: float) -> dict:
    """fz with one more setpoint for a grid variant (edge extension, §8)."""
    sps = dict(fz.get("setpoints", {}))
    sps[var] = tuple(sorted(set(sps.get(var, (0.85, 0.95, 1.05))) | {sp}))
    return {**fz, "setpoints": sps}


def stage_b1(rep: dict, fz: dict, n: int) -> tuple:
    """§8 B1: the edge extensions per cell; returns (jobs, fz per cell with the new setpoints)."""
    js, fzc = [], {}
    for cell, c in rep["cells"].items():
        fzc[cell] = fz
        for fam, e in c["B1_edges"].items():
            if e["next"] is None:
                continue
            fzc[cell] = with_setpoint(fzc[cell], e["variant"], e["next"])
            key = next(k for k in grid(fzc[cell]) if VARIANTS[e["variant"]](k) and k.split("/")[1].startswith(f"p{e['next']:g}"))
            js += [job("B", cell, *key.split("/"), s, ctrl=grid(fzc[cell])[key]) for s in main_seeds(n)]
    return js, fzc


def stage_b2(rep: dict, fzc: dict, n: int) -> list:
    """§3.4 B2: MC* = the cell's tuned M* and C* (recomputed on stages A and B1) together."""
    js = []
    for cell, c in rep["cells"].items():
        pts = grid(fzc[cell])
        js += [job("B", cell, "mc", "star", s, ctrl=mc_ctrl(pts, c["tuned"]["M*"], c["tuned"]["C*"])) for s in main_seeds(n)]
    return js


def _ctrl_of(root: Path, cell: str, key: str, seed: int) -> dict:
    for st in ("A", "B"):
        d = _day(root / st, cell, *key.split("/"), seed)
        if d is not None:
            return d["ctrl"]
    raise FileNotFoundError(key)


def stage_c1(rep: dict, n: int, root: Path = ROOT) -> list:
    """§9.6 C1 (runs first, §9.3): NC and the borderline best tuned arm on the 10 fresh seeds."""
    js = []
    for cell, c in rep["cells"].items():
        if c["C1_needed"]:
            k = c["best_tuned"]
            ctrl = _ctrl_of(root, cell, k, main_seeds(n)[0])
            js += [job("C1", cell, "nc", "base", s) for s in fresh_seeds(n)]
            js += [job("C1", cell, *k.split("/"), s, ctrl=ctrl) for s in fresh_seeds(n)]
    return js


def c1_result(rep: dict, cell: str, n: int, root: Path = ROOT) -> dict | None:
    """C1 on all n + 10 seeds; None when it was not needed, {'incomplete': True} while runs are missing."""
    from v5b.fleet import e1_analysis as ea
    c = rep["cells"][cell]
    if not c["C1_needed"]:
        return None
    key, seeds = c["best_tuned"], main_seeds(n)
    a = [_day(root / "C1", cell, "nc", "base", s) for s in fresh_seeds(n)]
    b = [_day(root / "C1", cell, *key.split("/"), s) for s in fresh_seeds(n)]
    if None in a or None in b:
        return {"incomplete": True}
    d0 = np.array([d["d_all"] for d in _all(root, cell, "nc/base", seeds)] + [d["d_all"] for d in a])
    d1 = np.array([d["d_all"] for d in _all(root, cell, key, seeds)] + [d["d_all"] for d in b])
    r = ea.c1_pass(d0, d1, n)
    r["pass"] = bool(r["pass"] and all(valid(d) for d in a + b))
    r["stop"] = sorted({w for d in a + b for w in stop_reasons(d, cell)})      # §10.6 on the C1 runs (V234)
    return {**r, "key": key}


def passes_after_c1(rep: dict, cell: str, n: int, root: Path = ROOT) -> list:
    """Tuned keys that pass in-sample (§9.2, valid runs) or through C1."""
    c = rep["cells"][cell]
    keys = sorted({k for k in c["tuned"].values() if c["effects"][k]["pass_valid"]})
    r = c1_result(rep, cell, n, root)
    if r and r.get("pass") and r["key"] not in keys:
        keys.append(r["key"])
    return keys


def stage_c2(rep: dict, n: int, rule2: dict, root: Path = ROOT) -> list:
    """§9.4-9.5 after C1: the Rule 2 replicates of every tuned pass (in-sample or C1) where Rule 2 holds, and the O_off
    pick replicates where O_off passes in-sample and no tuned arm passes, or where every tuned pass still needs its
    Rule 2 replicate (so that one round covers a tuned pass that then fails). Twins: SUMO seed = seed + 5,000."""
    js = []
    for cell, c in rep["cells"].items():
        seeds, twins = main_seeds(n), set()
        tp = passes_after_c1(rep, cell, n, root)
        if rule2[cell]:
            twins |= {(s, k) for k in tp for s in seeds}
        if c["o_off"]["pass"] and (not tp or rule2[cell]):
            twins |= {(s, p) for s, p in zip(seeds, c["o_off_picks"]) if p != "nc"}
        if twins:
            js += [job("C2", cell, "nc", "base", s, s + TWIN) for s in seeds]
            js += [job("C2", cell, *k.split("/"), s, s + TWIN, ctrl=_ctrl_of(root, cell, k, s)) for s, k in sorted(twins)]
    return js


FLAG_KEYS = ("braking", "expected_crashes", "throughput_loss", "ttt_conflict", "incident_unbalanced")


def final_verdict(rep: dict, n: int, powered: dict, rule2: dict, root: Path = ROOT) -> dict:
    """§9.7 on the stage report and the stage-C runs. powered[cell]: the stage-0 power rule held for that cell; the
    post-hoc power of report_stage is combined with it. 'incomplete' while a required replicate is missing."""
    from v5b.fleet import e1_analysis as ea
    if rep.get("stop"):
        return {"verdict": None, "refused": "stage report has stop reasons", "stop": rep["stop"]}
    seeds, cells, detail, missing = main_seeds(n), {}, {}, []
    for cell, c in rep["cells"].items():
        nc_tw = [_day(root / "C2", cell, "nc", "base", s, s + TWIN) for s in seeds]
        intr = rep["intrusion_flags"]

        def flagged(name, key):
            # flags of a C1 pass are those of its main seeds
            fr = intr.get(key, {})
            if key == "mc/star":
                fr = fr.get(cell, {})
            return any(c["flags"][name].get(x) for x in FLAG_KEYS) or fr.get("flag", False)

        def replicate(picks):
            if any(d is None for d in nc_tw):
                return None
            xs = []
            for s, p, d0 in zip(seeds, picks, nc_tw):
                d = d0 if p == "nc" else _day(root / "C2", cell, *p.split("/"), s, s + TWIN)
                if d is None:
                    return None
                xs.append(d)
            e = ea.effect(np.array([d["d_all"] for d in nc_tw]), np.array([d["d_all"] for d in xs]))
            why = sorted({w for d in nc_tw + xs for w in stop_reasons(d, cell)})      # §10.6 on the C2 runs (V234)
            return {**e, "pass": bool(e["pass"] and all(valid(d) for d in nc_tw + xs)), "stop": why}

        det = {"C1": c1_result(rep, cell, n, root)}
        if det["C1"] and det["C1"].get("incomplete"):
            missing.append(f"{cell} C1")
        pt, any_ok, f_list = False, False, []
        names = {k: name for name, k in c["tuned"].items()}
        tp = passes_after_c1(rep, cell, n, root)
        for key in tp:
            name = names.get(key, key)
            ok = True
            if rule2[cell]:
                r = replicate([key] * n)
                det[f"{name}_rule2"] = r
                if r is None:
                    missing.append(f"{cell} Rule 2 {name}")
                ok = bool(r and r["pass"])
            any_ok |= ok
            if ok and flagged(name, key):
                f_list.append(name)
            elif ok:
                pt = True
        po = False
        # §9.5: O_off counts only where no tuned arm passes, flagged or not (V234)
        if c["o_off"]["pass"] and not any_ok and (not tp or rule2[cell]):      # C2 ran (stage_c2)
            r = replicate(c["o_off_picks"])
            det["O_off_C2"] = r
            if r is None:
                missing.append(f"{cell} C2")
            ok = bool(r and r["pass"])
            if ok and flagged("O_off", "O_off"):
                f_list.append("O_off")
            elif ok:
                po = True
        cells[cell] = {"P_T": pt, "P_O": po, "F": f_list,
                       "powered": bool(powered[cell] and c["post_hoc_power"] >= ea.POWER)}
        detail[cell] = det
    if missing:
        return {"verdict": None, "incomplete": missing}
    stops = {f"{cell} {k}": r["stop"] for cell, det in detail.items() for k, r in det.items() if r and r.get("stop")}
    if stops:
        return {"verdict": None, "refused": "stage-C runs break stop rules", "stop": stops}
    v = ea.verdict(cells)
    if rep["oracle_fails_both"] and v["verdict"] != "KILL":
        v["note"] = "O_off failed in both cells; the continue comes from a C1 pass (V215 A4)"
    if v["kill_label"] and any(not rep["cells"][x]["post_hoc_power"] >= ea.POWER for x in cells):
        v["kill_label"] += "; underpowered (post hoc): " + ", ".join(
            x for x in cells if rep["cells"][x]["post_hoc_power"] < ea.POWER)
    return {**v, "cells": cells, "detail": detail}


def _all(root: Path, cell: str, key: str, seeds: list) -> list:
    out = []
    for s in seeds:
        d = next((x for st in ("A", "B") if (x := _day(root / st, cell, *key.split("/"), s)) is not None), None)
        out.append(d)
    return out


def prefix_same(a: dict, b: dict) -> bool:
    """§5.3: an R and an I day of one arm and seed match up to 57,600 s (30-s series and loop rows)."""
    pre = lambda d, k: [x for x in d[k] if x[0] <= 57600.0]      # noqa: E731
    return pre(a, "series") == pre(b, "series") and \
        [x for x in a["loops30"]["rows"] if x[0] <= 57600.0] == [x for x in b["loops30"]["rows"] if x[0] <= 57600.0]


def intrusion_table(days: list) -> dict:
    """§7.5: minGap intrusions by location and by whether the follower trails a commanded ALKS."""
    def where(e):
        ln, x = e.get("lane", ""), e.get("pos", -1.0)
        if ln.startswith(("r_", "rj_", ":rm")):
            return "ramp"
        if ln.startswith("3a_"):
            return "3a"
        if ln.startswith("3_"):
            if 600.0 <= x <= 700.0:
                return "incident site"
            if x >= 1092.0:
                return "lane-end area"
            return "zone" if x >= 150.0 else "3 upstream"
        return "other"
    tab = {}
    for d in days:
        for e in d["collision_events"]:
            if e.get("bumper") is not None and e["bumper"] > 0:
                k = f"{where(e)}{' behind commanded ALKS' if e.get('behind_cmd') else ''}"
                tab[k] = tab.get(k, 0) + 1
    return tab


def report_stage(n: int, root: Path = ROOT, stages: tuple = ("A", "B")) -> dict:
    """§8-9 on stages A-B: stop rules, tuned arms, O_off, the B1, C1 and C2 triggers, flags and labels. Every outcome is
    read only through these pre-registered rules."""
    from v5b.fleet import e1_analysis as ea
    seeds = main_seeds(n)
    rep = {"n": n, "seeds": [seeds[0], seeds[-1]], "cells": {}, "stop": []}
    rp = root / "A" / "replaced.json"
    repl = json.loads(rp.read_text()) if rp.exists() else {"idle": [], "replaced": {}, "extra_idle": []}
    rep["idle"] = repl
    intr, intr_nc, runs_by_cell = {}, {}, {}
    for cell in ("R", "I"):
        runs = load_stage(stages, cell, seeds, root)
        for k in repl["replaced"]:
            runs.pop(k, None)                  # the kept idle runs (first 3 seeds) are reported in rep["idle"]
        st_nc, nc = runs.pop("nc/base")
        missing = [k for k, (_, v) in runs.items() if any(d is None for d in v)] + (["nc"] if None in nc else [])
        if missing:
            rep["cells"][cell] = {"incomplete": missing}
            continue
        runs_by_cell[cell] = (nc, runs)
        for k, (_, v) in [("nc/base", (st_nc, nc))] + list(runs.items()):
            for s, d in zip(seeds, v):
                if why := stop_reasons(d, cell):
                    rep["stop"].append(f"{cell} {k} s{s}: {', '.join(why)}")
        nc_npz = [_npz(root, st_nc, cell, "nc/base", s) for s in seeds]
        d_nc = np.array([d["d_all"] for d in nc])
        D = {k: np.array([d["d_all"] for d in v]) for k, (_, v) in runs.items()}
        eff = {k: ea.effect(d_nc, v) for k, v in D.items()}
        ok_nc = all(valid(d) for d in nc)
        for k, e in eff.items():
            e["pass_valid"] = bool(e["pass"] and ok_nc and all(valid(d) for d in runs[k][1]))     # §9.2 (3)
        grid_pts = {k: v for k, v in D.items() if not k.startswith("mc/")}
        tuned_arms = {"M*": ea.tuned(d_nc, grid_pts, ("ma", "mp")), "C*": ea.tuned(d_nc, grid_pts, ("c",))}
        if "mc/star" in D:
            tuned_arms["MC*"] = "mc/star"
        tuned_pass = any(eff[k]["pass_valid"] for k in tuned_arms.values())
        edges = {}
        for fam, star in (("M", tuned_arms["M*"]), ("C", tuned_arms["C*"])):
            var = variant(star)
            pts = {k: v for k, v in grid_pts.items() if VARIANTS[var](k)}
            edges[fam] = {"best": star, "variant": var, "next": ea.edge_fires(d_nc, pts, star, tuned_pass)}
        o, picks = ea.o_off(d_nc, D)
        eo = ea.effect(d_nc, o)
        o_days = [nc[i] if p == "nc" else runs[p][1][i] for i, p in enumerate(picks)]
        eo["pass"] = bool(eo["pass"] and ok_nc and all(valid(d) for d in o_days))
        best_tuned = max(tuned_arms.values(), key=lambda k: eff[k]["rel"])
        fl_ = {name: flags(nc, runs[k][1], nc_npz, [_npz(root, runs[k][0], cell, k, s) for s in seeds], cell)
               for name, k in tuned_arms.items()}
        o_npz = [nc_npz[i] if p == "nc" else _npz(root, runs[p][0], cell, p, s) for i, (p, s) in enumerate(zip(picks, seeds))]
        fl_["O_off"] = flags(nc, o_days, nc_npz, o_npz, cell)
        mc_of = runs["mc/star"][1][0]["ctrl"].get("of") if "mc/star" in runs else None
        for k, (_, v) in list(runs.items()) + [("O_off", (None, o_days))]:
            kk = f"mc/star:{mc_of}" if k == "mc/star" else k
            intr[kk] = intr.get(kk, 0) + sum(d["mingap_intrusions"] for d in v)
            intr_nc[kk] = intr_nc.get(kk, 0) + sum(d["mingap_intrusions"] for d in nc)
        loo = []
        for i in range(n):
            rest = [j for j in range(n) if j != i]
            k = max(grid_pts, key=lambda q: float(np.median(d_nc[rest] - grid_pts[q][rest])))
            loo.append(float(grid_pts[k][i]))
        dd = d_nc - D[best_tuned]
        s_post = float(np.std(dd, ddof=1) / np.median(d_nc))
        keep = ("diff", "diff_ci", "rel", "rel_ci", "pass", "pass_valid", "sign")
        drop_of = lambda v: [e and (e["drop"], e["qdf"]) for e in (ea.main_pm(d["series"]) for d in v)]   # noqa: E731
        rep["cells"][cell] = {
            "invalid_runs": {k: sum(not valid(d) for d in v) for k, (_, v) in runs.items() if any(not valid(d) for d in v)}
            | ({"nc/base": sum(not valid(d) for d in nc)} if not ok_nc else {}),
            "median_D_NC": float(np.median(d_nc)),
            "effects": {k: {x: e[x] for x in keep} | {"mean_rel": e["mean"]["rel"],
                                                      "seeds_ge_10pct": int(np.sum((d_nc - D[k]) >= 0.10 * d_nc))}
                        for k, e in eff.items()},
            "tuned": tuned_arms, "best_tuned": best_tuned, "tuned_pass": tuned_pass, "mc_star_of": mc_of,
            "o_off": {x: eo[x] for x in ("diff", "diff_ci", "rel", "rel_ci", "pass", "sign")}, "o_off_picks": picks,
            "o_off_nc_picks": picks.count("nc"),
            "o_off_edge_picks": sum(1 for p in picks if p != "nc" and not p.startswith("mc/")
                                    and p.split("/")[1].split("_")[0] != "p0.95"),
            "leave_one_out_rel": ea.effect(d_nc, np.array(loo))["rel"],
            "G": float((np.median(D[best_tuned]) - np.median(o)) / np.median(D[best_tuned])),
            "B1_edges": edges, "C1_needed": bool(ea.c1_needed(eff[best_tuned])),
            "flags": fl_, "s_post": s_post,
            "post_hoc_power": ea.p_pass(n, ea.MDE, ea.s_upper(s_post, n_pairs=n)),
            "lane_drop_pm": {"nc/base": drop_of(nc)} | {k: drop_of(v) for k, (_, v) in runs.items()},
            "intrusion_table": {"nc/base": intrusion_table(nc)} | {k: intrusion_table(v) for k, (_, v) in runs.items()},
        }
    if len(runs_by_cell) == 2:
        (nc_r, runs_r), (nc_i, runs_i) = runs_by_cell["R"], runs_by_cell["I"]
        for old, new in repl["replaced"].items():
            if new in runs_r and new in runs_i and all(idle(d) for d in runs_r[new][1][:FIRST] + runs_i[new][1][:FIRST]):
                rep["stop"].append(f"replacement {new} of {old} is idle too")
        for k in ["nc/base"] + [k for k in runs_r if k in runs_i]:
            a, b = (nc_r, nc_i) if k == "nc/base" else (runs_r[k][1], runs_i[k][1])
            if k != "nc/base" and a and b and a[0].get("ctrl") != b[0].get("ctrl"):
                continue                      # V234: a per-cell controller (MC*) differs by design
            if not all(prefix_same(x, y) for x, y in zip(a, b)):
                rep["stop"].append(f"R/I prefix mismatch: {k}")
    if all("effects" in c for c in rep["cells"].values()):
        for cell, other in (("R", "I"), ("I", "R")):
            c, o_ = rep["cells"][cell], rep["cells"][other]
            lab = {}
            for name, k in c["tuned"].items():
                if k == "mc/star" and c["mc_star_of"] != o_["mc_star_of"]:
                    lab[name] = "not run in the other cell (MC* differs)"
                elif k in o_["effects"]:
                    lab[name] = ea.harm_label({"rel_ci": o_["effects"][k]["rel_ci"]})
                else:
                    lab[name] = "not run in the other cell"
            c["harm_in_other_cell"] = lab
        rep["intrusion_flags"] = {k: ea.intrusion_flag(v, intr_nc[k]) for k, v in intr.items()}
        for cell, c in rep["cells"].items():
            if c["mc_star_of"] and f"mc/star:{c['mc_star_of']}" in rep["intrusion_flags"]:
                rep["intrusion_flags"].setdefault("mc/star", {})[cell] = rep["intrusion_flags"][f"mc/star:{c['mc_star_of']}"]
        rep["oracle_fails_both"] = not any(c["o_off"]["pass"] for c in rep["cells"].values())
    return rep


T3_REPEATS = 5


def wave2b(fz: dict) -> list:
    """§10.4: b_min 0.5 at the chosen K_I (report-only), T3 at 0.85 x ô_cr (5 repeats per arm, 3-h I slices), and one
    MC full day run twice."""
    st, js = "stage0_w2", []
    od = fz["o_cr"][fz["drop_loop"]]          # the same law and loop as the gain-check run it is compared with
    for s in GAIN_SEEDS:
        js.append(job(st, "R", "bmin", "b0.5", s, ctrl={"alks": alks_ctrl(0.95 * od, "long", k_i=fz["gains"]["k_i"],
                                                                         b_min=0.5, loop=fz["drop_loop"])}, hours="13,20"))
    pts = grid({**fz, "setpoints": {v: (0.85,) for v in VARIANTS}})
    m_star = "mp/p0.85" if "mp/p0.85" in pts else "ma/p0.85"
    arms = {"ma": pts["ma/p0.85"], "c": pts["c/p0.85_long"], "mc": mc_ctrl(pts, m_star, "c/p0.85_long")}
    if "mp/p0.85" in pts:
        arms["mp"] = pts["mp/p0.85"]
    a = THROWAWAY[0]
    js.append(job(st, "I", "t3_nc", "slice", a, hours="15,18"))
    for k, c in arms.items():
        js += [job(st, "I", f"t3_{k}", f"rep{i}", a, ctrl=c, hours="15,18") for i in range(T3_REPEATS)]
    js += [job(st, "I", "t3_mc_day", f"rep{i}", THROWAWAY[1], ctrl=arms["mc"]) for i in range(2)]
    return js


def report_w2b(fz: dict, root: Path = ROOT) -> dict:
    st, out = root / "stage0_w2", {}
    a = THROWAWAY[0]
    nc = _day(st, "I", "t3_nc", "slice", a)
    for k in ("ma", "mp", "c", "mc") if fz["gains"].get("pi") else ("ma", "c", "mc"):
        reps = [_day(st, "I", f"t3_{k}", f"rep{i}", a) for i in range(T3_REPEATS)]
        if None in reps or nc is None:
            out[k] = {"pass": False, "missing": True}
            continue
        logs = [json.dumps([d.get("meter", {}) and d["meter"]["log"], d.get("alks", {}) and d["alks"]["log"]]) for d in reps]
        def busy(d):
            m_ok = (d["meter"] or {}).get("red_phases", 0) >= 10
            a_ok = d["alks"] is not None and sum(1 for r in d["alks"]["log"] if r[1] < 1.0) >= 10
            return {"ma": m_ok, "mp": m_ok, "c": a_ok, "mc": m_ok and a_ok}[k]
        act = [busy(d) for d in reps]
        out[k] = {"hashes_identical": len({d["hash"] for d in reps}) == 1, "logs_identical": len(set(logs)) == 1,
                  "active": all(act), "differs_from_nc": reps[0]["hash"] != nc["hash"]}
        out[k]["pass"] = all(out[k].values())
    days = [_day(st, "I", "t3_mc_day", f"rep{i}", THROWAWAY[1]) for i in range(2)]
    out["mc_full_day"] = {"pass": None not in days and days[0]["hash"] == days[1]["hash"]
                          and all(valid(d) for d in days)}
    bm = {}
    for s in GAIN_SEEDS:
        b5 = _day(st, "R", "bmin", "b0.5", s)
        b3 = _day(st, "R", "gain_mtfc", f"ki{fz['gains']['k_i']:g}", s)
        if b5 and b3:
            bm[s] = {f"b{b}": {"ttc_below_1.5": d["ttc_seconds_below"]["1.5"], "intrusions": d["mingap_intrusions"],
                               "min_at_bmin": sum(1 for r in d["alks"]["log"] if abs(r[1] - d["alks"]["b_min"]) < 1e-9)}
                     for b, d in (("0.3", b3), ("0.5", b5))}
    out["b_min_report"] = bm
    out["stop"] = [k for k, v in out.items() if isinstance(v, dict) and v.get("pass") is False]
    return out


def _fz_a(fz: dict) -> dict:
    """The frozen values with the stage-A idle replacements (§4) applied."""
    p = ROOT / "A" / "replaced.json"
    return json.loads(p.read_text())["fz"] if p.exists() else fz


def main(argv_=None) -> int:
    """make: write a job list; run: run one; report: write a stage report. Frozen inputs come from JSON files."""
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--jobs", required=True, help="job list JSON")
    r.add_argument("--workers", type=int, default=16)
    m = sub.add_parser("make")
    m.add_argument("--wave", choices=("w1", "w1b", "w2a", "w2c", "w2d", "w2b", "L1", "L2", "A1", "Arep", "A2", "B1", "B2", "C1", "C2"),
                   required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--freeze", help="JSON with the stage-0 values (o_cr, drop_loop, c_loop, gains, l_bar, n)")
    m.add_argument("--cal", help="wave-1 report JSON (for w2a)")
    m.add_argument("--stage-report", help="stage report JSON (for B1, B2, C)")
    m.add_argument("--b1", help="the B1 job file (its fz_by_cell, for B2)")
    sm = sub.add_parser("smoke", help="V231: run one short slice per distinct ctrl of a job list and check read-back")
    sm.add_argument("--jobs", required=True)
    sm.add_argument("--workers", type=int, default=16)
    rp = sub.add_parser("report")
    rp.add_argument("--wave", choices=("cal", "w1", "w2a", "w2b", "floors", "L1", "L2", "stage", "verdict"), required=True)
    rp.add_argument("--out", required=True)
    rp.add_argument("--freeze")
    rp.add_argument("--cal")
    rp.add_argument("--stage-report")
    a = ap.parse_args(argv_)
    rd = lambda x: json.loads(Path(x).read_text()) if x else None      # noqa: E731
    fz, cal, srep = rd(getattr(a, "freeze", None)), rd(getattr(a, "cal", None)), rd(getattr(a, "stage_report", None))
    if a.cmd == "run":
        run(json.loads(Path(a.jobs).read_text())["jobs"], a.workers)
        return 0
    if a.cmd == "smoke":
        js = smoke_jobs(json.loads(Path(a.jobs).read_text())["jobs"])
        run(js, a.workers)
        rep = {f"{j['cell']}/{j['arm']}/{j['point']}": (smoke_check(d, j) if (d := json.loads(out_path(j).read_text())
                                                                               if out_path(j).exists() else None)
                                                         else {"ok": False, "bad": ["missing"]}) for j in js}
        Path(a.jobs).with_suffix(".smoke.json").write_text(json.dumps(rep, indent=1))
        bad = {k: v["bad"] for k, v in rep.items() if not v["ok"]}
        print(f"smoke: {len(rep)} controllers, {len(bad)} failed", bad or "")
        return 1 if bad else 0
    if a.cmd == "make":
        if a.wave == "w1":
            lb = l_bar()
            js, extra = wave1(lb), {"l_bar_m": lb}
        elif a.wave == "w1b":
            lb = json.loads((ROOT / "w1_jobs.json").read_text())["l_bar_m"]
            js, extra = wave1b(lb), {"l_bar_m": lb}
        elif a.wave == "w2a":
            js, extra = wave2a(cal["calibration"], cal["l_bar_m"]), {}
        elif a.wave == "w2c":
            js, extra = wave2c(cal["calibration"], cal["l_bar_m"]), {}
        elif a.wave == "w2d":
            js, extra = wave2d(cal["calibration"], cal["l_bar_m"]), {}
        elif a.wave in ("L1", "L2"):
            js, extra = lite_jobs(fz, ext=a.wave == "L2"), {}
        elif a.wave == "w2b":
            js, extra = wave2b(fz), {}
        elif a.wave == "A1":
            js, extra = stage_a(fz, fz["n"], True), {}
        elif a.wave == "Arep":
            r = replace_idle(fz, fz["n"])
            (ROOT / "A" / "replaced.json").write_text(json.dumps({k: r[k] for k in ("idle", "replaced", "extra_idle", "fz")},
                                                                 indent=1))
            js, extra = r["jobs"], {}
        elif a.wave == "A2":
            r = json.loads((ROOT / "A" / "replaced.json").read_text())
            js, extra = stage_a(r["fz"], fz["n"], False, skip=tuple(r["replaced"])), {}
        elif a.wave == "B1":
            js, fzc = stage_b1(srep, _fz_a(fz), fz["n"])
            extra = {"fz_by_cell": fzc}
        elif a.wave == "B2":
            js, extra = stage_b2(srep, rd(a.b1)["fz_by_cell"], fz["n"]), {}
        elif a.wave == "C1":
            js, extra = stage_c1(srep, fz["n"]), {}
        else:
            js, extra = stage_c2(srep, fz["n"], fz["rule2"]), {}
        Path(a.out).write_text(json.dumps({**extra, "jobs": js}, indent=1))
        print(f"{len(js)} jobs")
        return 0
    if a.wave in ("cal", "w1"):
        rep = report_w1(r_only=a.wave == "cal")
    elif a.wave == "w2a":
        rep = report_w2a(cal["calibration"], cal["l_bar_m"])
    elif a.wave == "w2b":
        rep = report_w2b(fz)
    elif a.wave == "floors":
        rep = floors(fz, cal)
    elif a.wave in ("L1", "L2"):
        rep = lite_report(fz, ext=a.wave == "L2")
        Path(a.out).write_text(json.dumps(rep, indent=1, default=str))
        print("direction:", rep.get("direction"), rep.get("best"))
        return 0
    elif a.wave == "stage":
        rep = report_stage(fz["n"])
    else:
        rep = final_verdict(srep, fz["n"], fz["powered"], fz["rule2"])
    Path(a.out).write_text(json.dumps(rep, indent=1, default=str))
    print("stop:" if a.wave != "verdict" else "verdict:", rep.get("stop", rep.get("verdict")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
