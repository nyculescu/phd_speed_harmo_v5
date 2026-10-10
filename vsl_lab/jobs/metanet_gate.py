"""U.S.169 SB METANET plant gate, protocol v4 (v3 §5, outcome §0.3, F1 trigger §6.1, plus §A12 P11-k). Runs only
after the v4 freeze commit (docs/lab/day_pattern/metanet_v4_calibration.json; guard §A9). Validation days = the frozen
F11 list (Wednesdays + extension); single look (§A6).

python -m vsl_lab.jobs.metanet_gate prep                         # validation inputs/targets -> val_data.npz (no model)
python -m vsl_lab.jobs.metanet_gate deterministic [--plant SEED] # N0, P1-P9 at c1 = c2 = 1
python -m vsl_lab.jobs.metanet_gate draws-plan [--plant SEED]    # 200 joint draws per day (seed 7,191,301)
python -m vsl_lab.jobs.metanet_gate draws --day-index I [--plant SEED]
python -m vsl_lab.jobs.metanet_gate draws-run --gate-ok [--plant SEED]
python -m vsl_lab.jobs.metanet_gate stochastic [--plant SEED]    # N0s, P8s, P6s, P10a, P10b
python -m vsl_lab.jobs.metanet_gate verdict                      # §0.3 outcome for the nominal plant
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import warnings

import numpy as np
from scipy.stats import binom

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_facts as F
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_items as IT
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

RUNS = C.RUNS
FREEZE = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v4_calibration.json"
FREEZE_F1 = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v4_f1_calibration.json"
SEED_BOOT_F1 = 7191302                    # §A8: bootstrap of the F1 gate statistics
SEED_BOOT = 7191300                       # §A8
SEED_DRAW = 7191301
N_DRAWS = 200
EV0, NEV = Q.EV0, Q.NEV
MPH = 1.609344
UPST = {"B1": "S1773", "B2": "S1140"}
MERGE_E = {"B1": "E13", "B2": "E14"}
F1_SET = {"P1c", "P4-1", "P4-2", "P5a-1", "P5a-2", "P5b-1", "P5b-2", "P7a-1", "P7a-2", "P7b", "P7c", "P9"}


# ---------------------------------------------------------------- statistics helpers
def wilson(k: int, n: int, z: float = 1.959964) -> list | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


def boot_median_ci(x, seed: int | None = None, n: int = 10000) -> list | None:
    seed = SEED_BOOT if seed is None else seed                # read at call time (F1 switches it, §A8)
    x = np.asarray(x, float)
    if x.size == 0:
        return None
    rng = np.random.default_rng(seed)
    m = np.median(rng.choice(x, (n, x.size)), axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def binom_tol(n: int, R: int) -> int:
    """P6: k_h = the smallest k with P(|X - round(n p~)| <= k) >= 0.9747, X ~ Bin(n, p~), p~ = (R + 0.5)/(n + 1)."""
    p = (R + 0.5) / (n + 1)
    c = round(n * p)
    for k in range(n + 1):
        if binom.cdf(c + k, n, p) - binom.cdf(c - k - 1, n, p) >= 0.9747:
            return k
    return n


def pb_pmf(ps) -> np.ndarray:
    """Poisson-binomial pmf by dynamic programming."""
    f = np.array([1.0])
    for p in ps:
        f = np.concatenate([f * (1 - p), [0.0]]) + np.concatenate([[0.0], f * p])
    return f


def need(n: int) -> int:
    return max(6, math.ceil(0.75 * n))


def med(x):
    return float(np.median(x)) if len(x) else None


# ---------------------------------------------------------------- arrivals A_b (P9, unit test 12)
def travel_h(net: M.Net, p: dict, km_a: float, km_b: float) -> float:
    """Free-flow travel time (h) from km_a to km_b at the frozen group v_f (G4 ties v_f to G3)."""
    vfg = [p["vf1"], p["vf2"], p["vf3"], p["vf3"]]
    t = 0.0
    for i in range(net.N):
        lo, hi = max(km_a, net.km_from[i]), min(km_b, net.km_to[i])
        if hi > lo:
            t += (hi - lo) / vfg[int(net.group[i])]
    return t


def _shift(q: np.ndarray, tt_h: float) -> np.ndarray:
    tb = np.arange(len(q)) + 0.5
    return np.interp(tb - tt_h * 12.0, tb, q)


def arrivals(d0: np.ndarray, d_o: np.ndarray, x_q: np.ndarray, net: M.Net, p: dict, b: str) -> np.ndarray:
    """A_b in 15-min bins (76 from 04:00): boundary + replayed entrance inflows up to and including b's merge
    (E13 / E14) - replayed exit flows up to and including X12 / X13, each shifted by its free-flow travel time
    to b's downstream station."""
    st = next(s for s in net.stations if s["id"] == Q.DOWN[b])
    A = _shift(d0, travel_h(net, p, net.km_from[0], st["km"]))
    ei = [e["id"] for e in net.entrances].index(MERGE_E[b])
    for j, e in enumerate(net.entrances[:ei + 1]):
        A = A + _shift(d_o[j], travel_h(net, p, e["km"], st["km"]))
    xi = [x["id"] for x in net.exits].index(Q.EXIT_IN[b])
    for j, x in enumerate(net.exits[:xi + 1]):
        A = A - _shift(x_q[j], travel_h(net, p, x["km"], st["km"]))
    return A.reshape(-1, 3).mean(axis=1)


# ---------------------------------------------------------------- queue extent (P7b)
def congested(v: np.ndarray, windows: list) -> bool:
    """< 40 mph for >= 15 consecutive minutes (3 bins), the run overlapping one of the windows."""
    run = 0
    for j, x in enumerate(np.nan_to_num(v, nan=99.0) < 40.0):
        run = run + 1 if x else 0
        if run >= 3:
            a, b = j - run + 1, j
            if any(a <= e and s <= b for s, e in windows):
                return True
    return False


def extent(speeds: dict, valid: dict, start: str, windows: list) -> str:
    """The most upstream congested station in the unbroken run that starts at `start` and goes upstream; invalid
    stations are skipped and do not break the run."""
    order = sorted(speeds, key=lambda s: I.ST[s]["km"])
    i = order.index(start)
    ext = start
    for s in reversed(order[:i]):
        if not valid.get(s, False):
            continue
        if congested(speeds[s], windows):
            ext = s
        else:
            break
    return ext


# ---------------------------------------------------------------- data
def val_days() -> list:
    return json.loads(C.FACTS.read_text())["F11"]["validation_days"]


def load_val() -> dict:
    z = np.load(RUNS / "val_data.npz")
    return {k: z[k] for k in z.files}


def freeze() -> dict:
    """§A9 guard: the v4 freeze record must be tracked by git, unchanged against HEAD, name protocol v4, have stage
    freeze and a route not starting with STOP. The v3 record is never read."""
    import subprocess
    rel = str(FREEZE.relative_to(C.REPO))
    tracked = subprocess.run(["git", "-C", str(C.REPO), "ls-files", "--error-unmatch", rel], capture_output=True)
    dirty = subprocess.run(["git", "-C", str(C.REPO), "diff", "--quiet", "HEAD", "--", rel])
    if tracked.returncode != 0 or dirty.returncode != 0:
        raise SystemExit(f"{rel} is not committed or differs from HEAD: the gate must not run (§A9)")
    fz = json.loads(FREEZE.read_text())
    if fz.get("protocol_version") != "v4" or not str(fz.get("stage", "")).startswith("freeze"):
        raise SystemExit(f"{rel} does not name protocol v4 at stage freeze (§A9)")
    return fz


def plant(seed: int | None) -> tuple:
    """Parameters come from the committed freeze record only (§A9); the untracked run files must agree exactly.
    Only the nominal plant and recorded ensemble candidates may be judged."""
    fz = freeze()
    if fz["route"].startswith("STOP"):
        raise SystemExit(f"route is '{fz['route']}' in {FREEZE.name}: the gate must not run (§8.6 step 4)")
    seed = fz["nominal_seed"] if seed is None else seed
    if seed == fz["nominal_seed"]:
        p = {k: float(v) for k, v in fz["frozen_params"].items()}
    else:
        c = next((c for c in fz["ensemble_candidates"]["candidates"] if c["seed"] == seed), None)
        if c is None:
            raise SystemExit(f"seed {seed} is not a recorded ensemble candidate")
        p = {k: float(v) for k, v in c["params"].items()}
    if p != Q.plant_params(seed):
        raise SystemExit("run-file parameters differ from the committed freeze record: the gate must not run")
    return seed, p


def code_commit() -> str:
    """§A6 (6): only committed code reads validation-day data."""
    import subprocess
    dirty = subprocess.run(["git", "-C", str(C.REPO), "status", "--porcelain", "--untracked-files=all", "--", "vsl_lab"],
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        raise SystemExit("vsl_lab has uncommitted changes: the gate must not run (§A6 (6))")
    return subprocess.run(["git", "-C", str(C.REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def nulls() -> dict:
    """P1c nulls from the usable calibration days on scaled speeds (km/h): N1 per station = median of the 05:00-23:00
    speeds >= 45 mph; N2 per station and bin = median calibration-day speed."""
    c = C.load_data()
    v = np.where(c["mv"], c["v"], np.nan)[:, :, EV0:]
    n1 = np.array([np.nanmedian(np.where(v[:, s] >= 45 * MPH, v[:, s], np.nan)) if np.any(v[:, s] >= 45 * MPH)
                   else np.nan for s in range(v.shape[1])])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")                       # all-NaN station-bins stay NaN
        n2 = np.nanmedian(v, axis=0)
    full2 = np.full((v.shape[1], M.N_BINS), np.nan)
    full2[:, EV0:] = n2
    return {"N1": n1, "N2": full2}


# ---------------------------------------------------------------- deterministic rows (§5.3)
def deterministic(seed: int | None = None, ctx: dict | None = None) -> dict:
    """ctx (protocol v5 §B5 in-sample screen; None = the validation gate unchanged): {"seed", "p", "data", "f11"
    (calibration-derived substitutes: P8_tolerance, floors, flow_null_N2_q), "nulls_for" (day index -> nulls),
    "stephalving_PASS", "boot_seed", "write"}."""
    global SEED_BOOT
    boot_saved = SEED_BOOT
    if ctx is not None:
        seed, p, data = ctx["seed"], ctx["p"], ctx["data"]
        f11 = ctx["f11"]
        sh = {"PASS": ctx["stephalving_PASS"]}
        SEED_BOOT = ctx["boot_seed"]
    else:
        seed, p = plant(seed)
        data = load_val()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    cs = Q.part1()["c_s"]
    if ctx is None:
        facts = json.loads(C.FACTS.read_text())
        f11 = facts["F11"]
        fz = freeze()
        sh = fz["stephalving"] if seed == fz["nominal_seed"] else \
            {"PASS": next(c for c in fz["ensemble_candidates"]["candidates"] if c["seed"] == seed)["stephalving_PASS"]}
    tol8 = f11["P8_tolerance"]
    try:
        return _deterministic_rows(seed, p, data, days, net, cs, f11, tol8, sh, ctx)
    finally:
        SEED_BOOT = boot_saved


def _deterministic_rows(seed, p, data, days, net, cs, f11, tol8, sh, ctx) -> dict:
    sids = [s["id"] for s in net.stations]
    o = Q.simf(net, {k: np.array([v]) for k, v in p.items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]),
                   record_cells=True)
    nl = nulls() if ctx is None else None
    qa = np.array([s in I.Q_A for s in sids])
    rows, per = {}, {}
    real_ev = {d: F.day_events(d) for d in days}
    md = {d: Q.model_day(d, o.q_st[i], o.v_st[i], o.exit_flow[i], net, cs, real_ev[d]) for i, d in enumerate(days)}
    # N0
    rows["N0"] = {"clip_max": float(o.clipped_share.max()), "nonfinite_days": int(o.nonfinite.sum()),
                  "stephalving_PASS": sh["PASS"],
                  "PASS": bool(o.clipped_share.max() <= 0.01 and not o.nonfinite.any() and sh["PASS"])}
    # P1a, P1b
    nq = [V.nrmse(o.q_st[i], data["q"][i], data["mq"][i]) for i in range(len(days))]
    nv = [V.nrmse(o.v_st[i], data["v"][i], data["mv"][i]) for i in range(len(days))]
    nq_s, nv_s = [x for x in nq if x is not None], [x for x in nv if x is not None]
    rows["P1a"] = {"n": len(nq_s), "unscored": len(nq) - len(nq_s), "median": med(nq_s), "ci": boot_median_ci(nq_s),
                   "N2_q_null": f11["flow_null_N2_q"]["median_nrmse_q"], "PASS": bool(nq_s and med(nq_s) <= 0.10)}
    rows["P1b"] = {"n": len(nv_s), "unscored": len(nv) - len(nv_s), "median": med(nv_s), "ci": boot_median_ci(nv_s),
                   "PASS": bool(nv_s and med(nv_s) <= 0.20)}
    # P1c
    act = [i for i, d in enumerate(days) if real_ev[d]["B1"] or real_ev[d]["B2"]]
    D1, D2, unsc = [], [], 0
    for i in act:
        d = days[i]
        win = np.zeros(M.N_BINS, bool)
        for s, e in list(real_ev[d]["B1"]) + list(real_ev[d]["B2"]):
            win[max(0, EV0 + s - 6):min(M.N_BINS, EV0 + e + 7)] = True
        nl_i = nl if ctx is None else ctx["nulls_for"](i)
        m = data["mv"][i] & qa[:, None] & win[None, :] & np.isfinite(nl_i["N2"]) & np.isfinite(nl_i["N1"])[:, None]
        nm = V.nrmse(o.v_st[i], data["v"][i], m)
        n1 = V.nrmse(np.broadcast_to(nl_i["N1"][:, None], m.shape), data["v"][i], m)
        n2 = V.nrmse(nl_i["N2"], data["v"][i], m)
        if nm is None or n1 is None or n2 is None:
            unsc += 1
            continue
        D1.append(nm - n1)
        D2.append(nm - n2)
    ci1 = boot_median_ci(D1)
    rows["P1c"] = {"n_A": len(act), "n_scored": len(D1), "unscored": unsc, "median_D_N1": med(D1), "ci_D_N1": ci1,
                   "median_D_N2": med(D2), "ci_D_N2": boot_median_ci(D2),
                   "PASS": bool(D1 and ci1[1] < 0 and med(D2) < 0)}
    # P2
    ok2 = []
    for i in act:
        d = days[i]
        cand = [(e[0], 0, "B1") for e in real_ev[d]["B1"]] + [(e[0], 1, "B2") for e in real_ev[d]["B2"]]
        s0, _, k0 = min(cand)
        estar = next(tuple(e) for e in real_ev[d][k0] if e[0] == s0)
        ov = [(e[0], pr) for pr, eps in md[d]["pairs"].items() for e in eps if Q.overlaps([e], [estar])]
        if not ov:
            ok2.append(False)
            continue
        first = min(x[0] for x in ov)
        ok2.append(any(pr == Q.PAIR[k0] for s, pr in ov if s == first))     # ties: e*'s pair among the earliest
    rows["P2"] = {"n_A": len(ok2), "share": float(np.mean(ok2)) if ok2 else None, "wilson": wilson(sum(ok2), len(ok2)),
                  "PASS": bool(ok2 and np.mean(ok2) >= 0.80)}
    for kk, k in ((1, "B1"), (2, "B2")):
        # P3-k
        ra = np.array([bool(real_ev[d][k]) for d in days])
        mo = np.array([md[d][k]["active"] for d in days])
        ag = np.array([md[d][k]["agree"] for d in days])
        rows[f"P3-{kk}"] = {"n": len(days), "agreement": float(ag.mean()), "wilson": wilson(int(ag.sum()), len(days)),
                            "confusion": {"real1_agree": int((ra & ag).sum()), "real1_miss": int((ra & ~ag).sum()),
                                          "real0_model1": int((~ra & mo).sum()), "real0_model0": int((~ra & ~mo).sum())},
                            "PASS": bool(ag.mean() >= 0.75)}
        # P4-k
        dts, nm_ = [], 0
        for d in days:
            for dt_, _ in IT.p4_day([tuple(e) for e in real_ev[d][k]], md[d][k]["episodes"]):
                if dt_ is not None:
                    dts.append(dt_)
                    nm_ += 1
                else:
                    dts.append(IT.UNMATCHED_ONSET_MIN)
        rows[f"P4-{kk}"] = {"n_episodes": len(dts), "matched_share": nm_ / len(dts) if dts else None,
                            "median_abs_onset_min": med(dts), "ci": boot_median_ci(dts),
                            "PASS": bool(dts and med(dts) <= 15 and nm_ / len(dts) >= 0.75)}
        # P5a-k, P5b-k
        heavy = [d for d in days if real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"]]
        hm = [d for d in heavy if md[d][k]["c4"] is not None]
        Dq = [IT.p5a_day(real_ev[d][k + "_long"], md[d][k]["c4"]) for d in hm]
        dr = [md[d][k]["c4"]["r"] - real_ev[d][k + "_long"]["c4"]["r"] for d in hm]
        rm = [md[d][k]["c4"]["r"] for d in hm]
        enough = len(hm) >= need(len(heavy))
        Lr = f11["floors"][k]["L_r"]
        rows[f"P5a-{kk}"] = {"n_H": len(heavy), "n_matched": len(hm), "required": need(len(heavy)),
                             "median_D": med(Dq), "ci": boot_median_ci(Dq),
                             "PASS": bool(enough and abs(med(Dq)) <= 0.05)}
        rows[f"P5b-{kk}"] = {"n_matched": len(hm), "required": need(len(heavy)), "median_r_diff": med(dr),
                             "ci_r_diff": boot_median_ci(dr), "median_r_model": med(rm), "ci_r_model": boot_median_ci(rm),
                             "L_r": Lr, "median_r_real": med([real_ev[d][k + "_long"]["c4"]["r"] for d in hm]),
                             "PASS": bool(enough and med(dr) >= -0.02 and med(rm) >= Lr)}
        # P6-k
        dem = {d: float(data["d0"][i, EV0:].sum() * 5 / 60) for i, d in enumerate(days)}
        srt = sorted(days, key=lambda d: dem[d])
        nL = len(srt) // 2
        halves = {"L": srt[:nL], "U": srt[nL:]}
        h = {}
        for hn, hd in halves.items():
            R = sum(bool(real_ev[d][k]) for d in hd)
            Mh = sum(md[d][k]["active"] for d in hd)
            h[hn] = {"n": len(hd), "R": R, "M": Mh, "k": binom_tol(len(hd), R)}
        g_r = h["U"]["R"] / h["U"]["n"] - h["L"]["R"] / h["L"]["n"]
        g_m = h["U"]["M"] / h["U"]["n"] - h["L"]["M"] / h["L"]["n"]
        a_ok = all(abs(x["M"] - x["R"]) <= x["k"] for x in h.values())
        bc = (g_m > 0 and g_m >= 0.5 * g_r) if g_r > 0 else True
        rows[f"P6-{kk}"] = {"halves": h, "gradient_real": g_r, "gradient_model": g_m, "a": a_ok,
                            "bc_applied": g_r > 0, "bc": bc, "PASS": bool(a_ok and bc)}
        # P7a-k
        diffs, sdiff, unc = [], [], []
        for d in heavy:
            dm, dr0, tc = IT.p7a_day(real_ev[d], md[d][k], k)
            diffs.append(abs(dm - dr0))
            sdiff.append(dm - dr0)
            if k == "B1" and tc is None:
                unc.append(abs(dm - dr0))
        rows[f"P7a-{kk}"] = {"n_H": len(heavy), "median_abs_min": med(diffs), "ci": boot_median_ci(diffs),
                             "signed_median_min": med(sdiff), "uncensored_median_abs_min": med(unc) if k == "B1" else None,
                             "n_uncensored": len(unc) if k == "B1" else None, "PASS": bool(diffs and med(diffs) <= 30)}
    # P5c
    both = [d for d in days if all(real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"] for k in ("B1", "B2"))]
    rmerge = {d: [F.merge_section(d, k, real_ev[d]) for k in ("B1", "B2")] for d in both}
    both_q = [d for d in both if all(rmerge[d])]                       # real merge section defined at both heads
    Dc = []
    for d in both_q:
        dc = IT.p5c_day(rmerge[d], [md[d][k]["merge"] for k in ("B1", "B2")])
        if dc is not None:
            Dc.append(dc)
    gated = len(both) >= 6
    rows["P5c"] = {"n_H_both": len(both), "n_real_merge_defined": len(both_q), "n_matched": len(Dc),
                   "required": need(len(both_q)), "gated": gated, "median_D": med(Dc), "ci": boot_median_ci(Dc),
                   "PASS": bool(len(Dc) >= need(len(both_q)) and abs(med(Dc)) <= 0.05) if gated else None}
    # P7b, P7c
    hv_any = [d for d in days if any(real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"] for k in ("B1", "B2"))]
    hit, p7c = [], []
    for d in hv_any:
        i = days.index(d)
        rsp = {s: I.event_station(d, s)["v"] for s in I.EVENT_STATIONS}
        rvl = {s: I.event_station(d, s)["valid"] for s in I.EVENT_STATIONS}
        msp, mvl = Q.model_speeds(d, o.v_st[i], net, cs)
        hit.append(IT.p7b_hit(IT.p7b_day(real_ev[d], md[d], rsp, rvl, msp, mvl, extent, UPST)))
        dr_, dm_ = IT.p7c_day(real_ev[d], md[d])
        p7c.append(abs(dm_ - dr_))
    rows["P7b"] = {"n": len(hit), "share": float(np.mean(hit)) if hit else None, "wilson": wilson(sum(hit), len(hit)),
                   "PASS": bool(hit and np.mean(hit) >= 0.70)}
    rows["P7c"] = {"n": len(p7c), "median_abs_min": med(p7c), "ci": boot_median_ci(p7c),
                   "PASS": bool(p7c and med(p7c) <= 30)}
    # P8
    pair_m, pair_r, spur_days, extra = {}, {}, 0, {"B1": 0, "B2": 0}
    extra_min = {"B1": 0, "B2": 0}
    spur_list = []
    for d in days:
        rp = {k: e for k, e in I.event_pairs(d).items() if e}
        for pr in set(md[d]["pairs"]) | set(rp):
            if pr in (I.P1, I.P2):
                continue
            key = f"{pr[0]}->{pr[1]}"
            pair_m[key] = pair_m.get(key, 0) + bool(md[d]["pairs"].get(pr))
            pair_r[key] = pair_r.get(key, 0) + bool(rp.get(pr))
        p8 = IT.p8_day(md[d], real_ev[d], rp, Q.spurious, Q.overlaps)
        sp = p8["spurious"]
        if sp:
            spur_days += 1
            spur_list += [{"day": d, "pair": list(x), "episodes": md[d]["pairs"][x]} for x in sp]
        for k in ("B1", "B2"):
            if p8["extra"][k]:
                extra[k] += 1
                extra_min[k] += p8["extra_min"][k]
    excess = {k: pair_m[k] - pair_r.get(k, 0) for k in pair_m}
    rows["P8"] = {"tolerance": tol8, "pair_model_minus_real": excess, "spurious_days": spur_days,
                  "extra_days": extra, "extra_minutes": extra_min, "spurious_list": spur_list[:60],
                  "PASS": bool(all(v <= tol8 for v in excess.values()) and spur_days <= tol8
                               and all(v <= tol8 for v in extra.values()))}
    # P9
    hf = [d for d in days if real_ev[d]["heavy_first"]]
    s1d, s2, trunc, zero_ex = [], [], 0, 0
    hfm = [d for d in hf if md[d][real_ev[d]["first"]]["c4"] is not None]
    for d in hfm:
        i = days.index(d)
        b = real_ev[d]["first"]
        ob = "B2" if b == "B1" else "B1"
        rl = real_ev[d][b + "_long"]
        rs, re_ = rl["ep"]
        ms, me_ = md[d][b]["matched"]
        cut = min((e[0] for e in real_ev[d][ob] if rs - 12 <= e[0] <= re_), default=None)
        if cut is not None:
            trunc += 1
        qr = I.event_station(d, Q.DOWN[b])["q"]
        qm = np.where(np.isfinite(qr), o.q_st[i][sids.index(Q.DOWN[b])][EV0:EV0 + NEV], np.nan)
        a, bb = IT.s1_ratio(qr, rs, re_, rl["c4"]["Q_dis"], cut), IT.s1_ratio(qm, ms, me_, md[d][b]["c4"]["Q_dis"], cut)
        if a is not None and bb is not None:
            s1d.append(bb - a)
        qd_m = md[d][b]["c4"]["Q_dis"]
        A = np.repeat(arrivals(data["d0"][i], data["d_o"][i], data["x_q"][i], net, p, b), 3)[EV0:EV0 + NEV]
        w0, w1 = max(0, ms - 12), (me_ if cut is None else min(me_, cut - 1))
        ex_min = int((A[w0:w1 + 1] > qd_m).sum()) * 5
        above = np.nan_to_num(qm) >= 0.95 * qd_m
        lo = hi = ms
        if above[ms] and ms <= w1:
            while lo - 1 >= w0 and above[lo - 1]:
                lo -= 1
            while hi + 1 <= w1 and above[hi + 1]:
                hi += 1
            plateau = (hi - lo + 1) * 5
        else:
            plateau = 0
        if ex_min > 0:
            s2.append(plateau / ex_min)
        else:
            zero_ex += 1
    enough9 = len(hfm) >= need(len(hf))
    rows["P9"] = {"n_H_first": len(hf), "n_matched": len(hfm), "required": need(len(hf)), "truncated": trunc,
                  "median_S1_diff": med(s1d), "ci_S1_diff": boot_median_ci(s1d), "n_S2": len(s2),
                  "median_S2": med(s2), "ci_S2": boot_median_ci(s2), "days_excess_zero": zero_ex,
                  "PASS": bool(enough9 and s1d and med(s1d) <= 0.03 and len(s2) >= 5 and med(s2) >= 1.2)}
    # reported (§5.5, subset): drop-label check against the validation CI of real r
    rep = {}
    for k in ("B1", "B2"):
        rr = [real_ev[d][k + "_long"]["c4"]["r"] for d in days if real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"]]
        ci = boot_median_ci(rr)
        rm = rows[f"P5b-{k[1]}"]["median_r_model"]
        rep[k] = {"real_r_median": med(rr), "real_r_ci": ci, "model_r_median": rm,
                  "drop_under_reproduced": bool(rm is not None and ci and rm > ci[1])}
    # §A12 P11-k (gated; not in the F1 trigger set)
    p11 = Q.p11_verdict({d: Q.p11_day(d, o.v_st[i], o.rho_cell[i], o.rc_cell[i], net, cs) for i, d in enumerate(days)})
    for kk, k in ((1, "B1"), (2, "B2")):
        rows[f"P11-{kk}"] = {kk2: p11[k][kk2] for kk2 in ("n_unbacked", "unbacked_days", "pooled_backed_share",
                                                         "most_downstream_congested_cell")} | {
            "tolerance": p11["tolerance"], "PASS": p11[k]["PASS"]}
    det = [r for r in rows if r != "P5c" or rows["P5c"]["gated"]]
    failed = [r for r in det if not rows[r]["PASS"]]
    res = {"plant_seed": seed, "n_val": len(days), "rows": rows, "reported": rep, "failed": failed,
           "deterministic_PASS": not failed,
           "F1_trigger": bool(set(failed) & F1_SET), "per_day_active": {
               d: {k: [bool(real_ev[d][k]), md[d][k]["active"]] for k in ("B1", "B2")} for d in days}}
    if ctx is None or ctx.get("write", False):
        (RUNS / f"gate_det_{seed}.json").write_text(json.dumps(res, indent=1, default=float))
    return res


# ---------------------------------------------------------------- stochastic rows (§5.3, §4.7 draws)
def draws_plan(seed: int | None = None) -> dict:
    """200 joint, re-centred, clipped draws per usable validation day, in day order, from one stream (7,190,095)."""
    seed, _ = plant(seed)
    fz = freeze()
    cf = fz["capacity_factors"]["nominal" if seed == fz["nominal_seed"] else str(seed)]
    spread = cf.get("spread_used", "none (deterministic-only)")
    if spread not in ("KM", "Tobit"):
        return {"plant_seed": seed, "spread": spread, "draws": None}
    days = val_days()
    rng = np.random.default_rng(SEED_DRAW)
    hi = {"B1": 1.20, "B2": min(1.20, cf["c2_star"])}
    m = cf["recentring_m"]
    out = np.zeros((len(days), N_DRAWS, 2))
    clipped = np.zeros(2)
    if spread == "KM":
        rep = [d for d, x in cf["per_day"].items() if x["reproducible"]]
        Fh = {k: (np.array(cf["F_hat"][k]["support"]), np.array(cf["F_hat"][k]["mass"])) for k in ("B1", "B2")}
        for i in range(len(days)):
            for j in range(N_DRAWS):
                u = cf["per_day"][rep[rng.integers(len(rep))]]["components"]
                for kk, k in enumerate(("B1", "B2")):
                    c = u[k]
                    if c["type"] == "exact":
                        x = c["c"]
                    else:
                        sup, ms = Fh[k]
                        sel = sup > c["c_low"] + 1e-9
                        x = float(rng.choice(sup[sel], p=ms[sel] / ms[sel].sum())) if ms[sel].sum() > 0 \
                            else float(sup[-1])
                    x = x / m[k]
                    lo_ = 0.80
                    xc = min(max(x, lo_), hi[k])
                    clipped[kk] += xc != x
                    out[i, j, kk] = xc
    else:
        tb = cf["tobit"]
        for i in range(len(days)):
            for kk, k in enumerate(("B1", "B2")):
                x = rng.normal(tb[k]["mu"], tb[k]["sigma"], N_DRAWS) / tb[k]["mu"]
                xc = np.clip(x, 0.80, hi[k])
                clipped[kk] += (xc != x).sum()
                out[i, :, kk] = xc
    np.save(RUNS / f"gate_draws_{seed}.npy", out)
    res = {"plant_seed": seed, "spread": spread, "n_days": len(days), "n_draws": N_DRAWS,
           "clipped_share": {"c1": clipped[0] / out[..., 0].size, "c2": clipped[1] / out[..., 1].size}}
    (RUNS / f"gate_draws_{seed}.json").write_text(json.dumps(res, indent=1))
    return res


def draws_day(i: int, seed: int | None = None) -> dict:
    seed, p = plant(seed)
    data = load_val()
    d = str(data["days"][i])
    net = M.build_network(C.VARIANT)
    cs = Q.part1()["c_s"]
    cc = np.load(RUNS / f"gate_draws_{seed}.npy")[i]
    sl = slice(i, i + 1)
    o = Q.simf(net, {k: np.full(N_DRAWS, v) for k, v in p.items()},
                   M.Inputs(data["d0"][sl], data["d_o"][sl], data["beta"][sl]), n_param_sets=N_DRAWS,
                   c1=cc[:, 0], c2=cc[:, 1], record_cells=True)
    rp = {k: e for k, e in I.event_pairs(d).items() if e}
    act, z, x, bad, unb = {"B1": 0, "B2": 0}, 0, {"B1": 0, "B2": 0}, 0, 0
    for j in range(N_DRAWS):
        mp = Q.model_pairs(d, o.v_st[j], net, cs)
        rl = Q.relocation(mp, o.rho_cell[j][:, EV0:], o.rc_cell[j][:, EV0:], net.b2_cells[-1] + 1)
        z += bool(Q.spurious(mp, rp)) or rl["flag"]
        for k in ("B1", "B2"):
            me = mp.get(Q.PAIR[k], [])
            act[k] += bool(me)
            x[k] += any(not Q.overlaps([e], rp.get(Q.PAIR[k], [])) for e in me)
        bad += bool(o.nonfinite[j] or o.clipped_share[j] > 0.01)
        pk = Q.p11_day(d, o.v_st[j], o.rho_cell[j], o.rc_cell[j], net, cs, pairs=mp)
        unb += pk["B1"]["unbacked"] or pk["B2"]["unbacked"]            # §A12 report-only under draws
    res = {"day": d, "active": act, "z": z, "extra": x, "bad": bad, "nonfinite": int(o.nonfinite.sum()),
           "share_draws_unbacked_report_only": unb / N_DRAWS,
           "real_active": {k: bool(rp.get(Q.PAIR[k])) for k in ("B1", "B2")}}
    (RUNS / f"gate_draw_{seed}_{i:03d}.json").write_text(json.dumps(res))
    return res


def stochastic(seed: int | None = None) -> dict:
    seed, _ = plant(seed)
    days = val_days()
    data = load_val()
    dem = {str(d): float(data["d0"][i, EV0:].sum() * 5 / 60) for i, d in enumerate(data["days"])}
    tol8 = json.loads(C.FACTS.read_text())["F11"]["P8_tolerance"]
    bm = freeze()["diagnostics"]["benchmarks"]
    R = [json.loads((RUNS / f"gate_draw_{seed}_{i:03d}.json").read_text()) for i in range(len(days))]
    rows = {}
    share_bad = [r["bad"] / N_DRAWS for r in R]
    rows["N0s"] = {"nonfinite_draws": sum(r["nonfinite"] for r in R), "max_share_bad": max(share_bad),
                   "PASS": bool(sum(r["nonfinite"] for r in R) == 0 and max(share_bad) <= 0.05)}
    zs = sum(r["z"] / N_DRAWS for r in R)
    xs = {k: sum(r["extra"][k] / N_DRAWS for r in R) for k in ("B1", "B2")}
    rows["P8s"] = {"sum_z": zs, "sum_x": xs, "tolerance": tol8, "PASS": bool(zs <= tol8 and all(v <= tol8 for v in xs.values()))}
    srt = sorted(range(len(days)), key=lambda i: dem[R[i]["day"]])
    nL = len(srt) // 2
    halves = {"L": srt[:nL], "U": srt[nL:]}
    for kk, k in ((1, "B1"), (2, "B2")):
        ph = np.array([(r["active"][k] + 0.5) / (N_DRAWS + 1) for r in R])
        y = np.array([r["real_active"][k] for r in R], float)
        h = {}
        for hn, idx in halves.items():
            f = pb_pmf(ph[idx])
            Rh = int(y[idx].sum())
            h[hn] = {"n": len(idx), "R": Rh, "E_M": float(ph[idx].sum()), "P_le": float(f[:Rh + 1].sum()),
                     "P_ge": float(f[Rh:].sum())}
        a_ok = all(x["P_le"] >= 0.003135 and x["P_ge"] >= 0.003135 for x in h.values())
        g_r = h["U"]["R"] / h["U"]["n"] - h["L"]["R"] / h["L"]["n"]
        g_m = h["U"]["E_M"] / h["U"]["n"] - h["L"]["E_M"] / h["L"]["n"]
        bc = (g_m > 0 and g_m >= 0.5 * g_r) if g_r > 0 else True
        rows[f"P6s-{kk}"] = {"halves": h, "gradient_real": g_r, "gradient_expected": g_m, "a": a_ok, "bc": bc,
                             "PASS": bool(a_ok and bc)}
        pi = np.where(y == 1, ph, 1 - ph)
        S_obs = int((pi < 0.05).sum())
        sd = np.where(np.minimum(ph, 1 - ph) < 0.05, np.minimum(ph, 1 - ph), 0.0)
        cdf = np.cumsum(pb_pmf(sd))
        crit = int(np.searchsorted(cdf, 0.9875 - 1e-12))
        rows[f"P10a-{kk}"] = {"S_obs": S_obs, "critical": crit, "PASS": bool(S_obs <= crit)}
        thr = bm["daily_demand_median_veh"]
        pc = np.array([bm[k]["climatology"]["p_upper"] if dem[r["day"]] >= thr else bm[k]["climatology"]["p_lower"]
                       for r in R])
        bp, bcl = (ph - y) ** 2, (pc - y) ** 2
        rng = np.random.default_rng(SEED_BOOT)
        bs = [float(np.mean(bp[i] - bcl[i])) for i in (rng.integers(0, len(y), len(y)) for _ in range(10000))]
        rows[f"P10b-{kk}"] = {"brier_plant": float(bp.mean()), "brier_clim": float(bcl.mean()),
                              "diff": float(bp.mean() - bcl.mean()),
                              "ci_diff": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                              "expected_agreement": float(pi.mean()),
                              "threshold_classifier_brier_cal": bm[k]["threshold_brier"],
                              "PASS": bool(bp.mean() <= bcl.mean() + 0.02)}
    failed = [r for r in rows if not rows[r]["PASS"]]
    res = {"plant_seed": seed, "rows": rows, "failed": failed, "stochastic_PASS": not failed,
           "draws": json.loads((RUNS / f"gate_draws_{seed}.json").read_text())}
    (RUNS / f"gate_sto_{seed}.json").write_text(json.dumps(res, indent=1, default=float))
    return res


def verdict() -> dict:
    """§0.3 for the nominal plant of the record in use (base, or F1 under --f1: §6.1 labels)."""
    fz = freeze()
    seed = fz["nominal_seed"]
    f1 = fz.get("structure") == "F1"
    det = json.loads((RUNS / f"gate_det_{seed}.json").read_text())
    cf = fz["capacity_factors"]["nominal"]

    def lab(d):
        if f1:
            d["label"] = "second look on the same validation days"
            if fz.get("delta_bound_active_at_zero"):
                d["outcome"] = "base structure, second optimisation (a FAIL by default, §6.1); was: " + d["outcome"]
        return d
    if not det["deterministic_PASS"]:
        if f1:
            return lab({"outcome": "FAIL after F1; route stop (§6.2)", "failed": det["failed"]})
        out = "FAIL; F1 triggered (§6.1)" if det["F1_trigger"] else "FAIL; route stop (F1 not triggered, §6.1)"
        return {"outcome": out, "failed": det["failed"]}
    spread = cf.get("spread_used")
    if spread not in ("KM", "Tobit"):
        return lab({"outcome": "PASS, deterministic-only (no usable spread)", "rules_failed": cf.get("rules_failed")})
    sto = json.loads((RUNS / f"gate_sto_{seed}.json").read_text())
    if not sto["stochastic_PASS"]:
        return lab({"outcome": "PASS, deterministic-only (a stochastic row failed under "
                               f"{'F-hat' if spread == 'KM' else 'F-hat_T'})", "failed": sto["failed"]})
    return lab({"outcome": "PASS" if spread == "KM" else "PASS, substitute spread"})


def main(argv=None) -> int:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job, run_batch
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["prep", "deterministic", "draws-plan", "draws", "draws-run", "stochastic", "verdict"])
    ap.add_argument("--plant", type=int, default=None)
    ap.add_argument("--day-index", type=int, default=0)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--f1", action="store_true", help="judge F1 (§6.1): F1's freeze record and bootstrap seed")
    a = ap.parse_args(argv)
    if a.f1:                                                  # F1: its own committed record and seed 7,191,302
        global FREEZE, SEED_BOOT
        FREEZE, SEED_BOOT = FREEZE_F1, SEED_BOOT_F1
    if freeze()["route"].startswith("STOP"):                 # no validation-day work after a route stop
        raise SystemExit(f"route is '{freeze()['route']}' in {FREEZE.name}: the gate must not run (§8.6 step 4)")
    commit = code_commit()
    if a.what == "prep":
        out = C.build_data(val_days(), RUNS / "val_data.npz", exit_flows=True)
        ledger.append("DP", "metanet-v4-gate", "S", "metanet_v4_gate_prep", {"code_commit": commit}, "none", 0, {},
                      {"file": str(out)}, notes="validation inputs; no model run")
        print(out)
    elif a.what == "deterministic":
        r = deterministic(a.plant)
        print(json.dumps({"plant": r["plant_seed"], "deterministic_PASS": r["deterministic_PASS"], "failed": r["failed"],
                          "F1_trigger": r["F1_trigger"]}))
        ledger.append("DP", "metanet-v4-gate", "S", "metanet_v4_gate_deterministic", {"plant": r["plant_seed"], "T_s": C.T_RUN, "code_commit": commit},
                      f"none (deterministic); validation days (F11 list); T = {C.T_RUN} s", r["n_val"], {},
                      {"PASS": r["deterministic_PASS"], "failed": r["failed"]},
                      notes=str(RUNS / f"gate_det_{r['plant_seed']}.json"))
    elif a.what == "draws-plan":
        print(json.dumps(draws_plan(a.plant)))
    elif a.what == "draws":
        print(json.dumps(draws_day(a.day_index, a.plant)))
    elif a.what == "draws-run":
        seed, _ = plant(a.plant)
        jobs = [Job(jid=f"draw_{seed}_{i:03d}", argv=["vsl_lab.jobs.metanet_gate", "draws", "--day-index", str(i),
                                                      "--plant", str(seed)] + (["--f1"] if a.f1 else []))
                for i in range(len(val_days()))]
        try:
            rep = run_batch(jobs, RUNS / f"batch_draws_{seed}_{int(time.time())}", max_workers=32, gate_ok=a.gate_ok)
        finally:
            C.verify_v3()
        print(json.dumps({"jobs": rep.n_jobs, "failed": rep.n_failed_proc, "wall_s": rep.wall_s}))
        ledger.append("DP", "metanet-v4-gate", "S", "metanet_v4_gate_draws", {"plant": seed, "draws": N_DRAWS, "T_s": C.T_RUN, "code_commit": commit},
                      f"7191301 (draws); validation days; T = {C.T_RUN} s", rep.n_jobs, {"proc_failed": rep.n_failed_proc},
                      {"wall_s": round(rep.wall_s, 1)}, notes=str(RUNS / f"gate_draw_{seed}_*.json"))
    elif a.what == "stochastic":
        r = stochastic(a.plant)
        print(json.dumps({"plant": r["plant_seed"], "stochastic_PASS": r["stochastic_PASS"], "failed": r["failed"]}))
        ledger.append("DP", "metanet-v4-gate", "S", "metanet_v4_gate_stochastic", {"plant": r["plant_seed"], "T_s": C.T_RUN, "code_commit": commit},
                      f"7191301 (draws), 7191300 (bootstrap); validation days; T = {C.T_RUN} s", len(val_days()), {},
                      {"PASS": r["stochastic_PASS"], "failed": r["failed"]},
                      notes=str(RUNS / f"gate_sto_{r['plant_seed']}.json"))
    else:
        print(json.dumps(verdict()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
