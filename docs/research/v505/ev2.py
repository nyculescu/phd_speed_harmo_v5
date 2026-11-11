"""EV part 2 (docs/research/protocols/v505_ev_informed_rule.md v2 §3, §5, V508, V515): tuning, picks, planned power, evaluation and
the reading. The told rule (IP) and the detecting rule (SW (a)) act through one switch path (v5b/fleet/v505.py), both on the FX
pick; ASCH is SW (b). Read once each, by this committed script.

usage: ev2.py plan STAGE --out JOBS.json --limit L [--picks PICKS.json] [--a A]
         STAGE: ev_tune_fx, ev_tune_sw (needs fx in --picks), ev_eval and ev_va (need --picks; ev_va also --a), *_ext twins
       ev2.py fx ROWS.jsonl OUT.json                         FX's pick on the tuning seeds
       ev2.py power FX_ROWS.jsonl GATE_ROWS.jsonl FX.json OUT.json --limit L
       ev2.py picks ROWS_FX.jsonl ROWS_SW.jsonl FX.json OUT.json [--ext]
       ev2.py read ROWS.jsonl PICKS.json OUT.json [--ext ROWS_EXT.jsonl]"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "planb"))
sys.path.insert(0, str(HERE))
import read6  # noqa: E402
import v5  # noqa: E402
from read_m2 import arr, drops_of, load, usable  # noqa: E402

FX_NAMES = tuple(n for n in v5.pb.CARRIED if n != "copy") + ("grid_a41000_10_2", "grid_lr400_13_1", "grid_os1_10_10", "grid_r4a2", "grid_z31333",
                                                              "3E-C_TRUCK", "3E-D_TRUCK")     # EV §3: 21 rules
IP_D, IP_AFTER = (500.0, 1000.0, 2000.0), (0.0, 60.0, 180.0)
SW_R, SW_TH, SW_AFTER = (400.0, 1000.0, 2000.0), (10.0, 13.0, 16.0), (0.0, 60.0, 180.0)
LEVELS = (0, 1, 2, 3)     # 1.6, 1.2, 1.0, 0.8 s
ASCH_THETA, ASCH_TAU, ASCH_H = (40.0, 55.0, 70.0), (10.0, 30.0, 60.0), (5.0, 15.0)
ASCH_DIST = ("3e", "3E-C_TRUCK", "3E-D_TRUCK")
G_BAR = 10.0     # % of the untold arm's event cost (E3)
LVL = (2.5, 97.5)     # 95 % two-sided: one event decides (EV §5)
FLOW_PCT, COLL, BRAKE_RATIO = -0.5, 0.05, 1.05
M2_GROUPS = ("4a", "4", "ramp2", "pending_ramp2", "junction")     # V482's merge-2 groups (planb.md:143)
FALSE_KILL_MAX = 0.10


def merge(A: dict, B: dict) -> dict:
    """Rows of two stages of the same arms: (cell, arm) -> seed -> row, seeds joined."""
    return {k: {**A.get(k, {}), **B.get(k, {})} for k in set(A) | set(B)}


def ctrl_of(arm_cfg: dict) -> dict:
    return {k: v for k, v in arm_cfg.get("ctrl", {}).items() if k != "env"}


def uniform_level(ctrl: dict) -> int | None:
    """The FX pick's level where it is one level everywhere (p333: 3); None for zone or state rules."""
    lv = ctrl.get("cav_rule")
    return lv[0] if lv and len(set(lv)) == 1 and not ctrl.get("speed") else None


def with_ctrl(base_cfg: dict, ctrl: dict) -> dict:
    """A stored S arm's plant and env with another controller."""
    c = copy.deepcopy(base_cfg)
    env = c.get("ctrl", {}).get("env", {})
    c["ctrl"] = {**ctrl, **({"env": env} if env else {})}
    return c


def plan(stage: str, out_dir: Path, limit: float, picks: dict | None = None, a: float | None = None) -> dict:
    arms = v5.s6_arms()
    base = lambda n: v5.ev_cfg(arms[f"S|{n}"], limit, None)
    s_cfg = lambda n: v5.ev_cfg(arms[f"S|{n}"], None, None)
    cell = f"EVA{limit:g}"
    pack = stage in ("ev_eval", "ev_eval_ext", "ev_va")
    st = out_dir / "st"
    stem = stage.removesuffix("_ext")
    jobs = {}
    if stem == "ev_tune_fx":
        jobs = {f"{cell}|{n}": base(n) for n in FX_NAMES}
    elif stem == "ev_tune_sw":
        fx = picks["fx"]
        fxc = ctrl_of(arms[f"S|{fx}"])
        p3 = ctrl_of(arms["S|p333"])
        u = uniform_level(fxc)
        for d in IP_D:
            for L in LEVELS:
                for af in IP_AFTER:
                    if L != u:
                        jobs[f"{cell}|ip_d{d:g}_L{L}_a{af:g}"] = with_ctrl(base("p333"), {"told": {"base": fxc, "d": d, "L": L, "after": af}})
        for r in SW_R:
            for th in SW_TH:
                for L in LEVELS:
                    for af in SW_AFTER:
                        if L != u:
                            jobs[f"{cell}|swa_r{r:g}_th{th:g}_L{L}_a{af:g}"] = with_ctrl(base("p333"), {"detect": {"base": fxc, "r": r, "th": th, "L": L, "after": af}})
        for dn in ASCH_DIST:
            for th in ASCH_THETA:
                for tau in ASCH_TAU:
                    for h in ASCH_H:
                        jobs[f"{cell}|swb_{dn}_t{th:g}_s{tau:g}_h{h:g}"] = with_ctrl(base("p333"), {"asch": {"steady": p3, "dist": ctrl_of(arms[f"S|{dn}"]),
                                                                                                           "theta_kmh": th, "tau_s": tau, "h_kmh": h}})
    elif stem in ("ev_eval", "ev_va"):
        sel = {"nc": base("nc"), "N": base("p333"), "FX": base(picks["fx"]), "SW": picks["sw_cfg"], "IP": picks["ip_cfg"]}
        jobs = {f"{cell}|{k}": copy.deepcopy(c) for k, c in sel.items()}
        jobs |= {f"S|{k}": s_cfg(n) for k, n in (("nc", "nc"), ("N", "p333"), ("FX", picks["fx"]))}
        jobs["S|SW"] = s_with(picks["sw_cfg"], arms)
        if stem == "ev_va":
            if a is None:
                raise SystemExit("ev_va needs --a, M2's picked V-A level")
            jobs = {n: {**c, "ramp2_assertive": float(a)} for n, c in jobs.items()}
            jobs = {n.replace(f"{cell}|", f"{cell}V{a:g}|").replace("S|", f"SV{a:g}|"): c for n, c in jobs.items()}
    else:
        raise SystemExit(f"no EV part-2 job for stage {stage}")
    for c in jobs.values():
        c.pop("measure", None)
        if pack:
            c["measure"] = str(st)
    lo, hi = v5.STAGES[stage]
    return {"stage": stage, "seed_range": [lo, hi], "q": v5.pb.Q, "limit": limit, "a": a, "arms": jobs}


def s_with(cell_cfg: dict, arms: dict) -> dict:
    """The same controller in S (no event): SW's S row for its event cost."""
    c = copy.deepcopy(cell_cfg)
    env = c.get("ctrl", {}).get("env", {})
    env.pop("perturb", None)
    if not env and "ctrl" in c:
        c["ctrl"].pop("env", None)
    return c


def med_delay(T: dict, cell: str, arm: str, seeds: list) -> float:
    return float(np.median(arr(T, cell, arm, seeds, "all_delay")))


def fx_pick(T: dict, cell: str, seeds: list) -> dict:
    meds = {n: med_delay(T, cell, n, seeds) for n in FX_NAMES}
    fx = min(meds, key=meds.get)
    return {"fx": fx, "medians": meds, "n": len(seeds)}


def paired_med(T: dict, cell: str, a: str, b: str, seeds: list) -> float:
    return float(np.median(arr(T, cell, a, seeds, "all_delay") - arr(T, cell, b, seeds, "all_delay")))


def picks(T: dict, cell: str, fx: str, seeds: list, sw_jobs: dict) -> dict:
    """EV §3: IP and SW (a) by the median paired difference against the FX base; SW (b) (ASCH) against p333; SW = the better of (a)
    and (b) by median event-cell delay; bU = the lowest median event-cell delay of N, FX and SW, all on the tuning seeds."""
    names = lambda pre: [n.split("|", 1)[1] for n in sw_jobs if n.split("|", 1)[1].startswith(pre)]
    by = lambda pre, ref: min(names(pre), key=lambda n: paired_med(T, cell, n, ref, seeds)) if names(pre) else None
    ip, swa, swb = by("ip_", fx), by("swa_", fx), by("swb_", "p333")
    ip_vs_fx = paired_med(T, cell, ip, fx, seeds)
    cand = {k: med_delay(T, cell, n, seeds) for k, n in (("swa", swa), ("swb", swb)) if n}
    sw_key = min(cand, key=cand.get)
    sw = swa if sw_key == "swa" else swb
    u = {"N": med_delay(T, cell, "p333", seeds), "FX": med_delay(T, cell, fx, seeds), "SW": med_delay(T, cell, sw, seeds)}
    return {"fx": fx, "ip": ip, "ip_vs_fx_median": ip_vs_fx, "kill_by_pick": ip_vs_fx >= 0.0, "swa": swa, "swb": swb, "sw": sw,
            "ip_cfg": sw_jobs[f"{cell}|{ip}"], "sw_cfg": sw_jobs[f"{cell}|{sw}"], "bU": min(u, key=u.get), "untold_medians": u, "n": len(seeds)}


def power(fx_T: dict, gate_T: dict, cell: str, fx: str, tune_n: int, eval_n: int, n_ip: int, sims: int = 400, seed: int = 505_501) -> dict:
    """EV §5's planned power, model fixed in the protocol: one IP setting has a true G of 15 %, every other 0; the setting-to-setting
    spread is that of the FX family's paired differences against the FX pick on the tuning seeds; the event cost and its spread come
    from the gate rows (p333); evaluation n as given. Returns P(KILL | true 15 %)."""
    rng = np.random.default_rng(seed)
    t_seeds = sorted(next(iter(fx_T.values())))
    fxd = arr(fx_T, cell, fx, t_seeds, "all_delay")
    diffs = np.concatenate([arr(fx_T, cell, n, t_seeds, "all_delay") - fxd for n in FX_NAMES if n != fx])
    diffs = diffs - np.median(diffs)
    g_seeds = sorted(gate_T[(cell, "p333")])
    cost = arr(gate_T, cell, "p333", g_seeds, "all_delay") - arr(gate_T, "S", "p333", g_seeds, "all_delay")
    true = 0.15 * float(np.median(cost))
    kills = 0
    for _ in range(sims):
        tune = rng.choice(diffs, (n_ip, tune_n))
        tune[0] -= true     # setting 0 is the good one (lower delay)
        good = int(np.argmin(np.median(tune, axis=1))) == 0
        d = rng.choice(diffs, eval_n) + (true if good else 0.0)     # delay_U - delay_IP on the evaluation seeds
        c = rng.choice(cost, eval_n)
        idx = rng.integers(0, eval_n, (2000, eval_n))
        g = 100.0 * np.median(d[idx], axis=1) / np.maximum(np.median(c[idx], axis=1), 1e-9)
        kills += np.percentile(g, LVL[1]) < G_BAR
    return {"p_false_kill_at_15": kills / sims, "true_gain_veh_s": true, "event_cost_median": float(np.median(cost)), "tune_n": tune_n,
            "eval_n": eval_n, "n_ip": n_ip, "sims": sims}


def gain(st: read6.Stat, T: dict, cell: str, u: str, seeds: list, groups=None, s_cell: str = "S") -> dict:
    """G(U) = median(delay_U - delay_IP) in the cell / U's median event cost (cell - S), seeds resampled jointly; groups: only those
    road groups' delay (for the KILL's off-merge-2 check), from read6.location."""
    if groups is None:
        dU, dI = arr(T, cell, u, seeds, "all_delay"), arr(T, cell, "IP", seeds, "all_delay")
    else:
        loc = lambda arm: np.array([sum(v for k, v in read6.location(T[(cell, arm)][s]).items() if k.startswith("delay|") and k.split("|")[1] in groups)
                                    for s in seeds])
        dU, dI = loc(u), loc("IP")
    cost = arr(T, cell, u, seeds, "all_delay") - arr(T, s_cell, u, seeds, "all_delay")
    num, den = dU - dI, cost
    pt = 100.0 * float(np.median(num)) / max(float(np.median(den)), 1e-9)
    b = 100.0 * np.median(num[st.idx], axis=1) / np.maximum(np.median(den[st.idx], axis=1), 1e-9)
    return {"G": pt, "ci": read6.ci(b, LVL), "d": num, "event_cost_median": float(np.median(den))}


def location_share(T: dict, cell: str, u: str, seeds: list, loser: str = "IP") -> float | None:
    """V482: the median paired road-delay difference (U - IP, or IP - U for a KILL) over the merge-2 groups over the same over all
    groups; None where the denominator is not above 0."""
    def per(arm, only):
        return np.array([sum(v for k, v in read6.location(T[(cell, arm)][s]).items() if k.startswith("delay|") and (not only or k.split("|")[1] in M2_GROUPS))
                         for s in seeds])
    a, b = (u, "IP") if loser == "IP" else ("IP", u)
    den = float(np.median(per(a, False) - per(b, False)))
    return float(np.median(per(a, True) - per(b, True))) / den if den > 0 else None


def read(T: dict, p: dict, cell: str, seeds: list, swaps: int = 2000, s_cell: str = "S", underpowered: float | None = None) -> dict:
    """EV §5: GAIN, KILL, KILL BY PICK or NOT SHOWN; nulls per comparison; the location rule of common §6 (repeat on V-A flagged)."""
    st = read6.Stat(len(seeds))
    G = {u: gain(st, T, cell, u, seeds, s_cell=s_cell) for u in ("N", "FX", "SW")}
    nulls = {u: read6.swap_null(G[u]["d"], LVL[0], swaps, 505_601) for u in G}
    failed = sorted(u for u, r in nulls.items() if r > read6.NULL_FACTOR * LVL[0] / 100.0)
    b = G[p["bU"]]
    flow = 100.0 * float(np.median(arr(T, cell, "IP", seeds, "passed") - arr(T, cell, p["bU"], seeds, "passed"))) / max(float(np.median(arr(T, cell, p["bU"], seeds, "passed"))), 1e-9)
    coll = float(arr(T, cell, "IP", seeds, "collisions").mean() - arr(T, cell, p["bU"], seeds, "collisions").mean())
    brake = float(arr(T, cell, "IP", seeds, "b45_step").mean() / max(arr(T, cell, p["bU"], seeds, "b45_step").mean(), 1e-9))
    side = flow >= FLOW_PCT and coll <= COLL and brake <= BRAKE_RATIO
    out = {"G": {u: {"G": r["G"], "ci": r["ci"], "event_cost_median": r["event_cost_median"]} for u, r in G.items()}, "nulls": nulls, "bU": p["bU"],
           "side": {"flow_pct": flow, "coll_excess": coll, "b45_ratio": brake, "ok": side}, "n": len(seeds)}
    if p["kill_by_pick"]:     # the told grid found nothing better than its FX base on the tuning seeds (EV §5)
        out["outcome"] = "KILL BY PICK"
    elif p["bU"] in failed:
        out["outcome"] = read6.FAILED_NULL
    elif b["G"] >= G_BAR and all(G[u]["ci"][0] > 0 for u in G) and side and not failed:
        out["outcome"] = "GAIN"
    elif b["ci"][1] < G_BAR:
        out["outcome"] = "KILL" if underpowered is None else f"KILL, underpowered (P = {underpowered:.2f})"     # EV §5: closes nothing
    else:
        out["outcome"] = "NOT SHOWN"
    if out["outcome"].startswith("KILL"):
        out["kill_sentence"] = (f"being told the time and place of this upstream slowdown, used as zone headway switching, did not cut its delay cost "
                                f"by 10 % against the best untold rule{' (by pick)' if out['outcome'] == 'KILL BY PICK' else ''}; "
                                f"a gain of up to {b['ci'][1]:.1f} % is not excluded")
        groups = sorted({k.split("|")[1] for k in read6.location(T[(cell, "IP")][seeds[0]]) if k.startswith("delay|")} - set(M2_GROUPS))
        g_off = gain(st, T, cell, p["bU"], seeds, groups=tuple(groups), s_cell=s_cell)
        out["kill_off_merge2"] = {"G": g_off["G"], "ci": g_off["ci"], "groups": groups}
        out["lane_end_bound"] = g_off["ci"][1] >= G_BAR     # common §6: the KILL does not hold once merge 2 is taken out
    elif out["outcome"] == "GAIN":
        share = location_share(T, cell, p["bU"], seeds)
        out["location_share"] = share
        out["lane_end_bound"] = share is not None and share > 0.5
    else:
        out["lane_end_bound"] = False
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("plan", "fx", "power", "picks", "read"))
    ap.add_argument("args", nargs="*")
    ap.add_argument("--out")
    ap.add_argument("--limit", type=float)
    ap.add_argument("--picks")
    ap.add_argument("--a", type=float)
    ap.add_argument("--ext", action="store_true")
    ap.add_argument("--ext-rows")
    ap.add_argument("--s-cell", default="S")
    ap.add_argument("--underpowered", type=float)
    x = ap.parse_args(argv)
    write = lambda p, obj: v5.pb.cma2.write_json(Path(p), obj)
    if x.step == "plan":
        out = Path(x.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        j = plan(x.args[0], out.parent, x.limit, json.loads(Path(x.picks).read_text()) if x.picks else None, x.a)
        write(out, j)
        print(j["stage"], len(j["arms"]), "arms, seeds", j["seed_range"])
        return 0
    if x.step == "fx":
        rows, out = map(Path, x.args)
        T, dropped = load(rows), drops_of(rows)
        sd = v5.seeds("ev_tune")
        if x.ext_rows:     # EV §5's extension: every family re-picked on n = 100
            T = merge(T, load(Path(x.ext_rows)))
            dropped += drops_of(Path(x.ext_rows))
            sd += v5.seeds("ev_tune_ext")
        cell = next(iter(T))[0]
        sd, void = usable(sd, dropped)
        res = {"outcome": "VOID"} if void else fx_pick(T, cell, sd)
        write(out, res)
        print("fx", res.get("fx"))
        return 0
    if x.step == "power":
        fx_rows, gate_rows, fxj, out = map(Path, x.args)
        T, G = load(fx_rows), load(gate_rows)
        cell = f"EVA{x.limit:g}"
        fx = json.loads(fxj.read_text())["fx"]
        n_ip = len(IP_D) * len(LEVELS) * len(IP_AFTER)
        res = {f"tune{t}_eval{e}": power(T, G, cell, fx, t, e, n_ip) for t, e in ((60, 120), (100, 120), (100, 160))}
        res["rule"] = next((k for k in ("tune60_eval120", "tune100_eval120", "tune100_eval160") if res[k]["p_false_kill_at_15"] <= FALSE_KILL_MAX), "underpowered")
        write(out, res)
        print("power", res["rule"], {k: v["p_false_kill_at_15"] for k, v in res.items() if k != "rule"})
        return 0
    if x.step == "picks":
        fx_rows, sw_rows, fxj, out = map(Path, x.args)
        paths = [fx_rows, sw_rows] + ([fx_rows.parent.parent / "ev_tune_fx_ext" / "s6_rows.jsonl", sw_rows.parent.parent / "ev_tune_sw_ext" / "s6_rows.jsonl"] if x.ext else [])
        T, dropped = {}, []
        for f in paths:
            T = merge(T, load(f))
            dropped += drops_of(f)
        cell = next(k for k in T if k[0].startswith("EVA"))[0]
        stage = "ev_tune_ext" if x.ext else "ev_tune"
        sd, void = usable(v5.seeds("ev_tune") + (v5.seeds("ev_tune_ext") if x.ext else []), dropped)
        sw_jobs = json.loads((sw_rows.parent / "jobs.json").read_text())["arms"]
        res = {"outcome": "VOID"} if void else picks(T, cell, json.loads(fxj.read_text())["fx"], sd, sw_jobs)
        res["stage"] = stage
        write(out, res)
        print("picks", {k: res.get(k) for k in ("fx", "ip", "sw", "bU", "kill_by_pick")})
        return 0
    rows, pj, out = map(Path, x.args)
    T = load(rows)
    p = json.loads(pj.read_text())
    cell = next(k for k in T if k[0].startswith("EVA"))[0]
    sd = v5.seeds("ev_eval")
    dropped = drops_of(rows)
    if x.ext_rows:
        T = merge(T, load(Path(x.ext_rows)))
        sd += v5.seeds("ev_eval_ext")
        dropped += drops_of(Path(x.ext_rows))
    sd, void = usable(sd, dropped)
    res = {"outcome": "VOID", "reason": "more than 3 seeds dropped"} if void else read(T, p, cell, sd, s_cell=x.s_cell, underpowered=x.underpowered)
    res["dropped"] = dropped
    write(out, res)
    print("ev", res["outcome"], res.get("lane_end_bound"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
