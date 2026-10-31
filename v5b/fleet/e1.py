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
        return -1
    return sum(1 for ln in log.read_text(errors="replace").splitlines()
               if "performs emergency braking" in ln and any(f"lane '{x}" in ln for x in lanes))


def _flow(d: dict, group: str) -> float:
    from v5b.fleet.e1_analysis import loop_arrays
    _, q, _ = loop_arrays(d, group)
    return float(q.sum())


def meter_ratio(m: dict, min_queue: int = 3) -> list:
    """T0: realised / commanded per 5 clean minutes (metering, no override, backstop or downstream limit, >= 3 queued)."""
    clean = [r for r in m["log"] if r[6] and not (r[7] or r[8] or r[9]) and r[4] >= min_queue]
    return [round(sum(r[2] for r in clean[i:i + 5]) / sum(r[1] for r in clean[i:i + 5]), 3)
            for i in range(0, len(clean) - 4, 5)]


def report_w1(root: Path = ROOT) -> dict:
    """§10.3 criteria on wave 1. Reads checks only: no controller outcome (delay of a controlled run) is used."""
    from v5b.fleet import e1_analysis as ea
    st = root / "stage0_w1"
    ref = json.loads((REPO_ROOT / "docs/research/results/fleet_v190_tpoff_v0.json").read_text())["reference_days"]
    out, stop = {}, []
    base = {c: {s: _day(st, c, "nc", "base", s) for s in THROWAWAY} for c in ("R", "I")}
    twin = {c: {s: _day(st, c, "nc", "base", s, s + TWIN) for s in THROWAWAY} for c in ("R", "I")}
    missing = [(c, s) for c in ("R", "I") for s in THROWAWAY if base[c][s] is None or twin[c][s] is None]
    if missing:
        return {"incomplete": missing}
    out["validity"] = {c: {"base": sum(valid(d) for d in base[c].values()), "twin": sum(valid(d) for d in twin[c].values())}
                       for c in ("R", "I")}
    if any(v != 10 for c in out["validity"].values() for v in c.values()):
        stop.append("invalid NC day")
    inert = {s: base["R"][s]["hash"] == ref[f"day_s{s}"]["hash"] for s in THROWAWAY}
    out["inert_hashes_match"] = sum(inert.values())
    if out["inert_hashes_match"] != 10:
        stop.append("NC R days do not reproduce the V198 hashes")
    tw = {c: {"route_same": sum(base[c][s]["route_sha1"] == twin[c][s]["route_sha1"] for s in THROWAWAY),
              "hash_differs": sum(base[c][s]["hash"] != twin[c][s]["hash"] for s in THROWAWAY)} for c in ("R", "I")}
    out["twins"] = tw
    if any(v != 10 for c in tw.values() for v in c.values()):
        stop.append("twin check")
    drops = []
    for d in base["R"].values():
        pm = [e for e in (d["breakdowns_drop"] or []) if e["t_break"] >= ea.NOON and e["drop"] is not None]
        drops.append(pm[0]["drop"] if pm else None)
    dd = [x for x in drops if x is not None]
    out["T1"] = {"pm_drop_per_day": drops, "median_drop": float(np.median(dd)) if dd else None,
                 "qdf": [next((e["qdf"] for e in (d["breakdowns_drop"] or []) if e["t_break"] >= ea.NOON), None)
                         for d in base["R"].values()]}
    if not dd or np.median(dd) < 0.02:
        stop.append("T1: median drop below 2 %")
    cal = ea.calibrate(list(base["R"].values()))
    out["calibration"] = cal
    if cal["stop"]:
        stop.append("calibration: onset, drop loop or alinea_3 test")
    out["power"] = {}
    for c in ("R", "I"):
        dn = np.array([base[c][s]["d_all"] for s in THROWAWAY])
        d0 = dn - np.array([twin[c][s]["d_all"] for s in THROWAWAY])
        sc = float(np.std(d0, ddof=1) / np.median(dn))
        ch = ea.choose_n(sc)
        ch["noise_floors"] = ea.noise_floors(sc, ch["n"] or 20)
        ch["median_D_NC"] = float(np.median(dn))
        out["power"][c] = ch
    ns = [out["power"][c]["n"] for c in ("R", "I")]
    out["n"] = max(n for n in ns if n is not None) if any(n is not None for n in ns) else 20
    out["underpowered_cells"] = [c for c in ("R", "I") if out["power"][c]["n"] is None]
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
    for name in ("eta", "eta_mid"):
        p = st / name / "analysis.json"
        out[name] = json.loads(p.read_text())["chosen"] if p.exists() else None
    if out["eta"] is None or not (abs(out["eta"]["eta_median"] - 0.54) <= 0.05 and out["eta"]["n_valid"] >= 8):
        stop.append("blocker eta check")
    out["T0"] = t0_report(st)
    stop += [f"T0 {k}" for k, v in out["T0"].items() if not v.get("pass", True)]
    sm = {}
    for k in ("ma", "mp", "c", "mc"):
        d = _day(st, "I", f"smoke_{k}", "provisional", THROWAWAY[1])
        sm[k] = None if d is None else {
            "valid": valid(d), "blocker_stopped": bool(d["blocker"] and d["blocker"].get("x_stop")),
            "schema": all(d.get(x) is not None for x in ("d_all", "d_ramp", "served", "ttt_w_h", "loops30", "route_sha1",
                                                          "d_recovery")) and (d["meter"] or d["alks"]) is not None,
            "wall_s": d["wall_s"]}
    out["smoke"] = sm
    if any(v is None or not (v["valid"] and v["blocker_stopped"] and v["schema"]) for v in sm.values()):
        stop.append("smoke")
    out["wall_s_I_days"] = [base["I"][s]["wall_s"] for s in THROWAWAY]
    out["stop"] = stop
    return out


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
             "red_passages": m["red_passages"], "contacts": d["contacts"],
             "intrusions_ramp": sum(1 for x in lanes if x.startswith(("r_", "rj_", "3a_", ":rm"))),
             "braking": braking_by_lane(out_dir(st, "R", "t0_meter", point, s) / f"sumo_s{s}.log"),
             "braking_nc": braking_by_lane(out_dir(st, "R", "nc", "slice", s) / f"sumo_s{s}.log"),
             "ramp_flow_differs": _flow(d, "ramp_out") != _flow(n, "ramp_out"),
             "alinea_occ_differs": _flow(d, "alinea") != _flow(n, "alinea"),
             "merge_waits": (d["ramp_merge"] or {}).get("waits_over_s"), "merge_waits_nc": (n["ramp_merge"] or {}).get("waits_over_s")}
        r["pass"] = (r["ratio_ok"] and r["red_passages"] == 0 and r["contacts"] == 0 and r["intrusions_ramp"] == 0
                     and r["braking"] <= r["braking_nc"] and r["ramp_flow_differs"])
        if point == "r300_ovr":
            r |= {"override_s": m["override_s"], "backstop_s": m["backstop_s"], "max_red_exposure_s": m["max_red_exposure_s"]}
            r["pass"] = (r["red_passages"] == 0 and r["contacts"] == 0 and m["override_s"] > 0 and m["backstop_s"] > 0
                         and m["max_red_exposure_s"] <= 245.0)
        res[point] = r
    for cell in ("R", "I"):
        d, n = _day(st, cell, "t0_alks", "b0.5_long", a), nc[(cell, a)]
        if d is None or n is None:
            res[f"alks_{cell}"] = {"pass": False, "missing": True}
            continue
        k = d["alks"]
        free = [v for v, g in k["recovery"] if g is None or g > 100.0]
        r = {"cap_violations": k["cap_violations"], "restore_mismatch": k["restore_mismatch"], "compliance": k["compliance"],
             "max_decel": k["max_decel"], "hold_excess_p95": k["hold_excess_p95"],
             "recovered_share": round(sum(v >= 0.9 for v in free) / len(free), 3) if free else None, "n_free": len(free),
             "drop_flow_differs": _flow(d, "drop") != _flow(n, "drop"), "contacts": d["contacts"]}
        r["pass"] = (r["cap_violations"] == 0 and r["restore_mismatch"] == 0 and (r["compliance"] or 0) >= 0.95
                     and r["max_decel"] <= 1.6 and r["hold_excess_p95"] is not None and r["hold_excess_p95"] <= 1.0
                     and r["drop_flow_differs"] and r["contacts"] == 0)
        r["recovery_note"] = "report-only in PM slices; the recovery test runs on the wave-2 off-peak slices"
        res[f"alks_{cell}"] = r
    return res


def out_dir(st: Path, cell: str, arm: str, point: str, seed: int, ss: int | None = None) -> Path:
    return st / cell / arm / point / f"ss{ss or seed}"


def main(argv_=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--jobs", required=True, help="job list JSON")
    r.add_argument("--workers", type=int, default=16)
    rp = sub.add_parser("report")
    rp.add_argument("--wave", choices=("w1",), required=True)
    rp.add_argument("--out", required=True)
    m = sub.add_parser("make")
    m.add_argument("--wave", choices=("w1",), required=True)
    m.add_argument("--out", required=True)
    a = ap.parse_args(argv_)
    if a.cmd == "make":
        lb = l_bar()
        js = wave1(lb)
        Path(a.out).write_text(json.dumps({"l_bar_m": lb, "jobs": js}, indent=1))
        print(f"{len(js)} jobs, L_bar {lb:.4f} m")
    elif a.cmd == "report":
        rep = report_w1()
        Path(a.out).write_text(json.dumps(rep, indent=1, default=str))
        print("stop:", rep.get("stop", rep))
    else:
        run(json.loads(Path(a.jobs).read_text())["jobs"], a.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
