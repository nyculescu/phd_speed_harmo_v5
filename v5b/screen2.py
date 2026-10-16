"""Screen #2 (docs/research/protocols/screen_2.md): online-calibrated green-light commit margin, Hamburg 2023.

Every constant comes from the screen text; nothing is tuned on archive outcomes.
Interpretations fixed before data (logged in the result):
- "vehicle lanes" = Thing laneType containing "KFZ"; a group = unique (trafficLightsID, signalGroupID),
  represented by its lowest primary_signal datastream id;
- every distinct (phenomenon_time, state) report is kept; it becomes known at the smallest
  received_time among the rows reporting it;
- a green start = a known report of code 3 whose previous known report is not 3; a completed green ends
  at the first later known report that is not 3;
- the truth at arrival T = the state of the last report with phenomenon_time <= T (all reports);
- quantities are in seconds (received_time ms / 1000).
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

TZ = ZoneInfo("Europe/Berlin")
EPS, DELTA, ETA = 0.05, 0.025, 1.0
M_GRID = np.round(np.arange(0.0, 20.0 + 1e-9, 0.5), 1)
D0, V_MAX, V_MIN = 200.0, 13.9, 8.3
R0, R1 = D0 / V_MAX, D0 / V_MIN
STEP_S, H0, H1, HIST_S = 60, 6, 22, 3600
GREEN = 3
SEED_GROUPS, SEED_BOOT = 7_421_001, 7_421_002
MIN_GROUPS, MAX_GROUPS, ELIG_SHARE = 20, 40, 0.80
MIN_COMMITS, P_MIN, B_BOOT = 400, 2.0, 2000
KEEP_DAYS = range(13, 25)
FIT_DAYS, EVAL_DAYS = (14, 15, 16, 17), tuple(range(18, 25))
CELLS = {"weekday": (18, 19, 20, 21, 22), "weekend": (23, 24)}
MEMBER = "data/backup/observations.csv"
COLS = ["phenomenon_time", "result_time", "received_time", "result", "datastream_id", "mqtt"]


def local_ts(day, hour=0):
    return datetime(2023, 9, day, hour, tzinfo=TZ).timestamp()


# ---------------------------------------------------------------- metadata + streaming filter
def groups_from_meta(meta_path):
    things = json.load(open(meta_path))["things"]
    best = {}
    for th in things:
        p = th["properties"]
        if "KFZ" not in (p.get("laneType") or ""):
            continue
        for ds in th.get("Datastreams", []):
            dp = ds.get("properties", {})
            if dp.get("layerName") != "primary_signal":
                continue
            key = (p.get("trafficLightsID"), dp.get("signalGroupID"))
            best[key] = min(best.get(key, 10**12), ds["@iot.id"])
    return sorted(best.values())


def stream_filter(zip_path, ids, out_npz, chunk=20_000_000):
    lo_ms, hi_ms = local_ts(KEEP_DAYS[0]) * 1000, local_ts(KEEP_DAYS[-1] + 1) * 1000
    ids = np.asarray(ids)
    keep, n_rows, n_kept = [], 0, 0
    with zipfile.ZipFile(zip_path) as zf, zf.open(MEMBER) as raw:
        f = io.TextIOWrapper(raw, encoding="ascii", newline="")
        header = f.readline().strip().split(",")
        assert header == COLS, header
        for df in pd.read_csv(f, names=COLS, chunksize=chunk, usecols=[0, 2, 3, 4],
                              dtype={"phenomenon_time": "int64", "received_time": "int64", "result": "int64",
                                     "datastream_id": "int64"}):
            n_rows += len(df)
            m = df.datastream_id.isin(ids).to_numpy() & (df.received_time.to_numpy() >= lo_ms) & (df.received_time.to_numpy() < hi_ms)
            if m.any():
                keep.append(df[m])
                n_kept += int(m.sum())
    k = pd.concat(keep, ignore_index=True)
    np.savez(out_npz, **{c: k[c].to_numpy() for c in k.columns})
    return {"rows_streamed": n_rows, "rows_kept": n_kept}


# ---------------------------------------------------------------- timelines
def timeline(p, r, recv_ms):
    """Transitions of one group: ptime (s), state, known time (s), sorted by ptime."""
    d = pd.DataFrame({"p": p, "s": r, "k": recv_ms / 1000.0})
    # keep every distinct (ptime, state) report with its earliest known time; repeats are handled on the
    # known subset in forecast(), so a late-known row can never hide an earlier-known one
    d = d.groupby(["p", "s"], sort=True, as_index=False).k.min().sort_values(["p", "k"], kind="stable")
    return d.p.to_numpy(float), d.s.to_numpy(), d.k.to_numpy(float)


def forecast(t, P, S, K):
    """Candidate green windows [(start, end), ...] from transitions known at t, or None."""
    a = np.searchsorted(P, t - HIST_S - 900.0)
    b = np.searchsorted(P, t, "right")
    sel = K[a:b] <= t
    p, s = P[a:b][sel], S[a:b][sel]
    if len(p) < 2:
        return None
    is_gs = np.r_[False, (s[1:] == GREEN) & (s[:-1] != GREEN)]
    gs_idx = np.flatnonzero(is_gs)
    if len(gs_idx) == 0:
        return None
    gs = p[gs_idx]
    recent = gs[gs >= t - HIST_S]
    if len(recent) < 2:
        return None
    C = float(np.median(np.diff(recent)))
    lens = []
    not_green = np.flatnonzero(s != GREEN)
    for i in gs_idx:
        if p[i] < t - HIST_S:
            continue
        j = np.searchsorted(not_green, i + 1)          # first known non-green report after the start
        if j < len(not_green):
            lens.append(p[not_green[j]] - p[i])
    if not lens or C <= 0:
        return None
    Lg = float(np.median(lens))
    g_last = gs[-1]
    wins = []
    if s[-1] == GREEN:
        wins.append((g_last, g_last + Lg))
    wins.append((g_last + C, g_last + C + Lg))
    return wins


def decide(t, wins, m):
    """Arrival time T for margin(s) m (array), NaN where no commit."""
    m = np.atleast_1d(np.asarray(m, float))
    T = np.full(m.shape, np.nan)
    if wins is None:
        return T
    for ws, we in wins:
        lo = np.maximum(t + R0, ws + m)
        hi = np.minimum(t + R1, we - m)
        ok = np.isnan(T) & (lo <= hi)
        T[ok] = lo[ok]
    return T


def green_at(T, P, S):
    i = np.searchsorted(P, T, "right") - 1
    return (i >= 0) & (S[np.clip(i, 0, len(S) - 1)] == GREEN)


def approach_times(days):
    return np.concatenate([np.arange(local_ts(d, H0), local_ts(d, H1), STEP_S) for d in days])


# ---------------------------------------------------------------- arms
def outcomes_grid(ts, P, S, K):
    """For each approach and each m in M_GRID: commit flag, loss flag; plus no-forecast flags."""
    com = np.zeros((len(ts), len(M_GRID)), bool)
    loss = np.zeros_like(com)
    nofc = np.zeros(len(ts), bool)
    for i, t in enumerate(ts):
        w = forecast(t, P, S, K)
        if w is None:
            nofc[i] = True
            continue
        T = decide(t, w, M_GRID)
        c = ~np.isnan(T)
        com[i] = c
        if c.any():
            loss[i, c] = ~green_at(T[c], P, S)
    return com, loss, nofc


def fixed_margin(com, loss):
    nc = com.sum(0)
    rate = np.where(nc > 0, loss.sum(0) / np.maximum(nc, 1), 0.0)
    ok = np.flatnonzero(rate <= EPS)
    return float(M_GRID[ok[0]]) if len(ok) else float(M_GRID[-1])


def cdt_step(m, loss):
    return max(0.0, m + ETA * (float(loss) - EPS))


def online(ts, P, S, K, m0):
    """Sequential CDT: m <- max(0, m + ETA*(loss - EPS)) after each commit's outcome (known at arrival)."""
    m, pend = float(m0), []
    commit = np.zeros(len(ts), bool); los = np.zeros(len(ts), bool); used = np.empty(len(ts))
    for i, t in enumerate(ts):
        pend.sort()
        while pend and pend[0][0] <= t:
            _, l = pend.pop(0)
            m = cdt_step(m, l)
        used[i] = m
        w = forecast(t, P, S, K)
        T = decide(t, w, m)[0]
        if not np.isnan(T):
            commit[i] = True
            los[i] = not green_at(np.array([T]), P, S)[0]
            pend.append((T, float(los[i])))
    return commit, los, used


# ---------------------------------------------------------------- run
def eligible(groups_tl, days=FIT_DAYS):
    hours = np.concatenate([np.arange(local_ts(d, H0), local_ts(d, H1), 3600) for d in days])
    out = []
    for g, (P, S, K) in groups_tl.items():
        hit = np.searchsorted(P, hours + 3600) - np.searchsorted(P, hours) > 0
        if hit.mean() >= ELIG_SHARE:
            out.append(g)
    return sorted(out)


def evaluate(groups_tl):
    res = {"interpretations": __doc__}
    elig = eligible(groups_tl)
    res["eligible_groups"] = len(elig)
    if len(elig) < MIN_GROUPS:
        res["outcome"] = "STOP (data)"; return res
    rng = np.random.default_rng(SEED_GROUPS)
    chosen = sorted(rng.choice(elig, size=min(MAX_GROUPS, len(elig)), replace=False).tolist())
    res["groups"] = chosen
    fit_t, ev_t = approach_times(FIT_DAYS), approach_times(EVAL_DAYS)
    ev_day = np.array([datetime.fromtimestamp(t, TZ).day for t in ev_t])
    per = {}
    for g in chosen:
        P, S, K = groups_tl[g]
        cF, lF, _ = outcomes_grid(fit_t, P, S, K)
        mF = fixed_margin(cF, lF)
        cE, lE, nofc = outcomes_grid(ev_t, P, S, K)
        iF = int(np.flatnonzero(M_GRID == mF)[0])
        cO, lO, mO = online(ev_t, P, S, K, mF)
        per[g] = dict(mF=mF, comF=cE[:, iF], lossF=lE[:, iF], comO=cO, lossO=lO, mO=mO, nofc=nofc,
                      cE=cE, lE=lE)
    rngb = np.random.default_rng(SEED_BOOT)
    res["cells"] = []
    for name, days in CELLS.items():
        dm = np.isin(ev_day, days)
        agg = {k: 0 for k in ("N", "comF", "lossF", "comO", "lossO", "passF", "passO", "nofc", "comH", "lossH", "passH")}
        clusters = []
        for g in chosen:
            x = per[g]
            # hindsight: F's rule on all evaluation days of this group
            mH_i = int(np.flatnonzero(M_GRID == fixed_margin(x["cE"], x["lE"]))[0])
            comH, lossH = x["cE"][:, mH_i], x["lE"][:, mH_i]
            for d in days:
                k = ev_day == d
                pf = int((x["comF"][k] & ~x["lossF"][k]).sum()); po = int((x["comO"][k] & ~x["lossO"][k]).sum())
                clusters.append((int(k.sum()), pf, po))
            agg["N"] += int(dm.sum()); agg["nofc"] += int(x["nofc"][dm].sum())
            for arm, c, l in (("F", x["comF"], x["lossF"]), ("O", x["comO"], x["lossO"]), ("H", comH, lossH)):
                agg["com" + arm] += int(c[dm].sum()); agg["loss" + arm] += int((c & l)[dm].sum())
                agg["pass" + arm] += int((c & ~l)[dm].sum())
        cl = np.array(clusters, float)
        Pg = 100 * (agg["passO"] - agg["passF"]) / agg["N"]
        boot = []
        for _ in range(B_BOOT):
            b = cl[rngb.integers(0, len(cl), len(cl))]
            boot.append(100 * (b[:, 2].sum() - b[:, 1].sum()) / b[:, 0].sum())
        lo, hi = np.percentile(boot, [2.5, 97.5])
        rate = {a: agg["loss" + a] / agg["com" + a] if agg["com" + a] else float("nan") for a in "FOH"}
        validO, validF = rate["O"] <= EPS + DELTA, rate["F"] <= EPS + DELTA
        gated = agg["comF"] >= MIN_COMMITS and agg["comO"] >= MIN_COMMITS
        win = gated and validO and ((not validF) or (Pg >= P_MIN and lo > 0))
        res["cells"].append({"cell": name, "days": days, **agg, "loss_rate": rate,
                             "pass_share": {a: agg["pass" + a] / agg["N"] for a in "FOH"},
                             "P_points": Pg, "P_CI95": [float(lo), float(hi)],
                             "H_vs_F_points": 100 * (agg["passH"] - agg["passF"]) / agg["N"],
                             "no_forecast_share": agg["nofc"] / agg["N"],
                             "gated": bool(gated), "validO": bool(validO), "validF": bool(validF), "WIN": bool(win)})
    res["mF"] = {str(g): per[g]["mF"] for g in chosen}
    g = [c for c in res["cells"] if c["gated"]]
    res["outcome"] = "STOP (data)" if not g else ("CONTINUE" if any(c["WIN"] for c in g) else "STOP")
    return res


def load_timelines(npz):
    z = np.load(npz)
    d = pd.DataFrame({k: z[k] for k in z.files}).sort_values(["datastream_id", "phenomenon_time"], kind="stable")
    out = {}
    for g, x in d.groupby("datastream_id", sort=True):
        out[int(g)] = timeline(x.phenomenon_time.to_numpy(), x.result.to_numpy(), x.received_time.to_numpy())
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "filter":      # filter ZIP META OUT_NPZ
        ids = groups_from_meta(sys.argv[3])
        info = stream_filter(sys.argv[2], ids, sys.argv[4])
        print(json.dumps(info | {"groups_in_meta": len(ids)}))
    elif cmd == "run":       # run NPZ OUT_JSON
        res = evaluate(load_timelines(sys.argv[2]))
        json.dump(res, open(sys.argv[3], "w"), indent=1, default=str)
        print(res["outcome"])
