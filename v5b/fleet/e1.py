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


K_R_CAND = (35.0, 70.0, 140.0)
PI_CAND = {"wang": WANG, "conservative": CONSERVATIVE}
K_I_CAND = (0.005, 0.01, 0.02, 0.04, 0.08, 0.16)
NOMINAL = {"alinea": "kr70", "pi": "wang", "mtfc": "ki0.02"}
GAIN_SEEDS = THROWAWAY[:3]


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
    best = 0
    for h0 in range(int(min(t) // 3600), int(max(t) // 3600) + 1):
        k = [i for i, ti in enumerate(t) if h0 * 3600 <= ti < (h0 + 1) * 3600]
        if k and any(active[i] for i in k):
            best = max(best, swings([x[i] for i in k], top, bottom))
    return best


def gain_stats(d: dict, law: str) -> dict:
    """Swing count, lead time and the RMS of the controlled occupancy around ô, from one gain-check slice."""
    onset = next((e["t_break"] for e in d["breakdowns_drop"] or [] if e["t_break"] >= 13 * 3600), None)
    if law == "mtfc":
        a = d["alks"]
        t, x, o = [r[0] for r in a["log"]], [r[1] for r in a["log"]], [r[2] for r in a["log"]]
        act = [v < 1.0 for v in x]
        sw = max_swings_per_hour(t, x, act, 0.9, 0.4)
        ref = a["setpoint"]
    else:
        m = d["meter"]
        t, x, o = [r[0] for r in m["log"]], [r[1] for r in m["log"]], [r[3] for r in m["log"]]
        act = [bool(r[6] and not (r[7] or r[8])) for r in m["log"]]
        sw = max_swings_per_hour(t, x, act, 850.0, 300.0)
        ref = m["law"]["setpoint"]
    on = [ti for ti, a_ in zip(t, act) if a_]
    rms = (math.sqrt(sum((oi - ref) ** 2 for oi, a_ in zip(o, act) if a_) / sum(act)) if any(act) else None)
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
        return {"choice": nom, "rms": {}, "note": "no candidate acts on >= 2 of 3 seeds: nominal"}
    best = min(rms, key=rms.get)
    pick = nom if nom in rms and rms[nom] <= 1.10 * rms[best] else best
    return {"choice": pick, "rms": rms, "kept": sorted(ok), "stop": False}


def report_w2a(cal: dict, l_bar_m: float, root: Path = ROOT) -> dict:
    st = root / "stage0_w2"
    out = {}
    for law, cands in gain_points(cal, l_bar_m).items():
        stats = {k: [gain_stats(d, law) for s in GAIN_SEEDS if (d := _day(st, "R", f"gain_{law}", k, s))] for k in cands}
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
        sr[s] = {"occ_rise": float(np.mean(on) / np.mean(off) - 1.0) if np.mean(off) > 0 else None,
                 "recovered_share": round(sum(v >= 0.9 for v in free) / len(free), 3) if free else None,
                 "n_free": len(free)}
    out["self_reaction"] = sr
    rises = [v["occ_rise"] for v in sr.values() if v["occ_rise"] is not None]
    out["c_loop"] = "dropend" if rises and np.median(rises) > 0.10 and cal["tests"]["dropend"]["pass"] else cal["drop_loop"]
    out["recovery_pass"] = bool(sr) and all((v["recovered_share"] or 0) >= 1.0 for v in sr.values())
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
    for sp in fz.get("setpoints", {}).get("mp", (0.85, 0.95, 1.05)):
        pts[f"mp/p{sp:g}"] = {"meter": meter_ctrl("pi", round(sp * od, 4), pi=PI_CAND[g["pi"]], l_bar_m=fz["l_bar"])
                              | {"loop": fz["drop_loop"]}}
    for zone in ("short", "long"):
        for sp in fz.get("setpoints", {}).get(f"c_{zone}", (0.85, 0.95, 1.05)):
            pts[f"c/p{sp:g}_{zone}"] = {"alks": alks_ctrl(round(sp * oc, 4), zone, k_i=g["k_i"], b_min=fz.get("b_min", ct.B_MIN),
                                                         loop=fz["c_loop"])}
    return pts


def mc_ctrl(pts: dict, m_star: str, c_star: str) -> dict:
    """§3.4: M* and C* together; a cascade when M* is PI-ALINEA (both laws on the drop loop)."""
    return {**pts[m_star], **pts[c_star], "cascade": m_star.startswith("mp/")}


def stage_a(fz: dict, n: int, first: bool) -> list:
    """§9.3 stage A: NC + 12 points x n seeds x 2 cells; first=True gives the first 3 seeds of every point."""
    seeds = main_seeds(n)[:FIRST] if first else main_seeds(n)[FIRST:]
    pts = {"nc/base": None, **grid(fz)}
    return [job("A", cell, k.split("/")[0], k.split("/")[1], s, ctrl=c) for cell in ("R", "I") for k, c in pts.items()
            for s in seeds]


def idle(d: dict) -> bool:
    """§4: a run where the meter meters < 5 min and b < 1 for < 5 min over the day."""
    m, a = d.get("meter"), d.get("alks")
    on_m = (m["metering_s"] >= 300) if m else False
    on_c = (sum(1 for r in a["log"] if r[1] < 1.0) >= 5) if a else False
    return not (on_m or on_c)


def idle_points(root: Path = ROOT, n: int = 10) -> list:
    """Points idle on all 3 first seeds in both cells."""
    out = []
    base = root / "A"
    for cell_dir in (base / "R",):
        for arm in sorted(p.name for p in cell_dir.iterdir() if p.is_dir() and p.name != "nc"):
            for point in sorted(p.name for p in (cell_dir / arm).iterdir()):
                ds = [_day(base, "R", arm, point, s) for s in main_seeds(n)[:FIRST]]
                if all(d is not None and idle(d) for d in ds):
                    out.append(f"{arm}/{point}")
    return out


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
        f["incident_unbalanced"] = sum(t > 60.0 for t in dt) >= 3
    f["intrusions"] = sum(d["mingap_intrusions"] for d in x)
    f["expected_crashes_mean"] = {"nc": float(np.mean(ec_nc)), "x": float(np.mean(ec_x))}
    return f


VARIANTS = {"ma": lambda k: k.startswith("ma/"), "mp": lambda k: k.startswith("mp/"),
            "c_short": lambda k: k.startswith("c/") and k.endswith("_short"),
            "c_long": lambda k: k.startswith("c/") and k.endswith("_long")}


def report_stage(n: int, root: Path = ROOT, stages: tuple = ("A", "B")) -> dict:
    """§8-9 on stages A-B: tuned arms, O_off, the B1, C1, C2 and Rule 2 triggers, flags and labels. Every outcome is read
    only through these pre-registered rules."""
    from v5b.fleet import e1_analysis as ea
    seeds = main_seeds(n)
    rep = {"n": n, "seeds": [seeds[0], seeds[-1]], "cells": {}}
    intr = {}
    for cell in ("R", "I"):
        runs = load_stage(stages, cell, seeds, root)
        st_nc, nc = runs.pop("nc/base")
        missing = [k for k, (_, v) in runs.items() if any(d is None for d in v)] + (["nc"] if None in nc else [])
        if missing:
            rep["cells"][cell] = {"incomplete": missing}
            continue
        nc_npz = [_npz(root, st_nc, cell, "nc/base", s) for s in seeds]
        d_nc = np.array([d["d_all"] for d in nc])
        D = {k: np.array([d["d_all"] for d in v]) for k, (_, v) in runs.items()}
        eff = {k: ea.effect(d_nc, v) for k, v in D.items()}
        grid_pts = {k: v for k, v in D.items() if not k.startswith("mc/")}
        tuned_arms = {"M*": ea.tuned(d_nc, grid_pts, ("ma", "mp")), "C*": ea.tuned(d_nc, grid_pts, ("c",))}
        if "mc/star" in D:
            tuned_arms["MC*"] = "mc/star"
        tuned_pass = any(eff[k]["pass"] for k in tuned_arms.values())
        edges = {}
        for var, member in VARIANTS.items():
            pts = {k: v for k, v in grid_pts.items() if member(k)}
            if len(pts) >= 3:
                best = max(pts, key=lambda k: float(np.median(d_nc - pts[k])))
                edges[var] = {"best": best, "next": ea.edge_fires(d_nc, pts, best, tuned_pass)}
        o, picks = ea.o_off(d_nc, D)
        eo = ea.effect(d_nc, o)
        best_tuned = max(tuned_arms.values(), key=lambda k: eff[k]["rel"])
        fl_ = {name: flags(nc, runs[k][1], nc_npz, [_npz(root, runs[k][0], cell, k, s) for s in seeds], cell)
               for name, k in tuned_arms.items()}
        o_days = [nc[i] if p == "nc" else runs[p][1][i] for i, p in enumerate(picks)]
        o_npz = [nc_npz[i] if p == "nc" else _npz(root, runs[p][0], cell, p, s) for i, (p, s) in enumerate(zip(picks, seeds))]
        fl_["O_off"] = flags(nc, o_days, nc_npz, o_npz, cell)
        for k, (_, v) in runs.items():
            intr[k] = intr.get(k, 0) + sum(d["mingap_intrusions"] for d in v)
        intr["O_off"] = intr.get("O_off", 0) + fl_["O_off"]["intrusions"]
        intr["nc/base"] = intr.get("nc/base", 0) + sum(d["mingap_intrusions"] for d in nc)
        loo = []
        for i in range(n):
            rest = [j for j in range(n) if j != i]
            k = max(grid_pts, key=lambda q: float(np.median(d_nc[rest] - grid_pts[q][rest])))
            loo.append(float(grid_pts[k][i]))
        keep = ("diff", "diff_ci", "rel", "rel_ci", "pass", "sign")
        rep["cells"][cell] = {
            "invalid_runs": {k: sum(not valid(d) for d in v) for k, (_, v) in runs.items() if any(not valid(d) for d in v)}
            | ({"nc/base": sum(not valid(d) for d in nc)} if any(not valid(d) for d in nc) else {}),
            "median_D_NC": float(np.median(d_nc)),
            "effects": {k: {x: e[x] for x in keep} | {"mean_rel": e["mean"]["rel"],
                                                      "seeds_ge_10pct": int(np.sum((d_nc - D[k]) >= 0.10 * d_nc))}
                        for k, e in eff.items()},
            "tuned": tuned_arms, "best_tuned": best_tuned, "tuned_pass": tuned_pass,
            "o_off": {x: eo[x] for x in keep}, "o_off_picks": picks, "o_off_nc_picks": picks.count("nc"),
            "o_off_edge_picks": sum(1 for p in picks if p != "nc" and not p.startswith("mc/")
                                    and p.split("/")[1].split("_")[0] != "p0.95"),
            "leave_one_out_rel": ea.effect(d_nc, np.array(loo))["rel"],
            "G": float((np.median(D[best_tuned]) - np.median(o)) / np.median(D[best_tuned])),
            "B1_edges": edges, "C1_needed": bool(ea.c1_needed(eff[best_tuned]) and not tuned_pass),
            "C2_needed": bool(eo["pass"] and not tuned_pass), "flags": fl_,
            "lane_drop_pm": [next(((e["drop"], e["qdf"]) for e in (d["breakdowns_drop"] or []) if e["t_break"] >= 43200),
                                  None) for d in nc],
        }
    if all("effects" in c for c in rep["cells"].values()):
        for cell, other in (("R", "I"), ("I", "R")):
            c, o_ = rep["cells"][cell], rep["cells"][other]
            c["harm_in_other_cell"] = {name: ea.harm_label({"rel_ci": o_["effects"][k]["rel_ci"]})
                                       for name, k in c["tuned"].items() if k in o_["effects"]}
        rep["intrusion_flags"] = {k: ea.intrusion_flag(v, intr["nc/base"]) for k, v in intr.items() if k != "nc/base"}
    return rep

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
