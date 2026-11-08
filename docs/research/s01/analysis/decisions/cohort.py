"""(b) Time structure, by proxy. The pack keeps no decision or level time series (m_dec_level_s is a run total, m_minute holds
merge and ramp series only), but its side file keeps each ALKS's decision counts and level-seconds, and vehicle ids are
main.<i> in departure order. The departure times are rebuilt from the seed exactly as fleet.FleetDemand draws them
(rng(seed), exponential gaps at 3600/q over [0, 1800) s, rounded up to 0.1 s; no simulation). Each ALKS is then binned by
departure time; X1 and X2 share seeds and therefore vehicles, so a bin's X1 - X2 difference is paired by seed."""
import json
import math
import sys
from pathlib import Path

import numpy as np

from common_dec import GROUPS, HEADWAYS, B, SEED_RNG, HERE

DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st")
T_END, STEP, BIN = 1800.0, 0.1, 60.0
ARMS = {"v3w": GROUPS["v3w"], "baseline-v3": GROUPS["baseline-v3"], "os1_15_10": ["os1_15_10"], "3E-T": ["3e"], "p333": ["p333"]}
SEEDS = list(range(7_440_840, 7_440_880))


def departs(seed: int, q: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out, t = [], 0.0
    while True:
        t += rng.exponential(3600.0 / q)
        if t >= T_END:
            break
        out.append(round(math.ceil(t / STEP - 1e-9) * STEP, 3))
    return np.array(out)


def per_bin(f: Path, dep: np.ndarray) -> dict:
    z = np.load(f)
    idx = np.array([int(s.split(".")[1]) for s in z["dec_ids"]])
    if idx.max() >= len(dep):
        raise SystemExit(f"{f.name}: vehicle index {idx.max()} beyond {len(dep)} rebuilt departures")
    d, L = z["dec"].astype(float), z["dec_level_s"].astype(float)
    b = (dep[idx] // BIN).astype(int)
    nb = int(T_END // BIN)
    out = {}
    for k in range(nb):
        m = b == k
        on = L[m, :4].sum()
        out[k] = {"n": int(m.sum()), "share3": L[m, 3].sum() / on if on else np.nan,
                  "gap_on": float((L[m, :4].sum(0) * np.array(HEADWAYS)).sum() / on) if on else np.nan,
                  "changes": d[m, 1].mean() if m.any() else np.nan, "reversals": d[m, 4].mean() if m.any() else np.nan,
                  "share0": L[m, 0].sum() / on if on else np.nan}
    return out, idx


def boot(d: np.ndarray) -> tuple:
    d = d[~np.isnan(d)]
    if len(d) < 5:
        return (np.nan, np.nan, np.nan, len(d))
    rng = np.random.default_rng(SEED_RNG)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (B, len(d)))], axis=1), (2.5, 97.5))
    return (float(np.median(d)), float(lo), float(hi), len(d))


def main() -> int:
    q = 5300.0
    dep = {s: departs(s, q) for s in SEEDS}
    check = {"n_departures_median": float(np.median([len(x) for x in dep.values()])), "expected": q * T_END / 3600.0}
    V = {}
    max_idx_gap = []
    for arm, names in ARMS.items():
        for cell in ("X1", "X2"):
            for s in SEEDS:
                bins = []
                for n in names:
                    pb, idx = per_bin(DATA / f"{cell}__{n}__{q:.0f}__{s}.npz", dep[s])
                    bins.append(pb)
                    max_idx_gap.append(len(dep[s]) - 1 - int(idx.max()))
                V[(arm, cell, s)] = {k: {f: float(np.nanmean([b[k][f] for b in bins])) if not all(np.isnan(b[k][f]) for b in bins) else np.nan
                                         for f in ("share3", "gap_on", "changes", "reversals", "share0")} | {"n": bins[0][k]["n"]} for k in bins[0]}
    check["last_index_minus_max_ALKS_index_p50_max"] = [float(np.median(max_idx_gap)), int(np.max(max_idx_gap))]
    res, n_cmp = {}, 0
    for arm in ARMS:
        res[arm] = {}
        for k in range(int(T_END // BIN)):
            row = {}
            for f in ("share3", "gap_on", "changes", "reversals", "share0"):
                x1 = np.array([V[(arm, "X1", s)][k][f] for s in SEEDS])
                x2 = np.array([V[(arm, "X2", s)][k][f] for s in SEEDS])
                row[f] = {"X1": float(np.nanmedian(x1)), "X2": float(np.nanmedian(x2)), "X1-X2": boot(x1 - x2)}
                n_cmp += 1
            row["n_alks_median"] = float(np.median([V[(arm, "X1", s)][k]["n"] for s in SEEDS]))
            res[arm][f"{int(k * BIN)}-{int((k + 1) * BIN)}"] = row
    (HERE / "cohort.json").write_text(json.dumps({"check": check, "bins": res, "comparisons": n_cmp}, indent=1))
    print("check", check, "paired bin comparisons", n_cmp)
    for arm in ARMS:
        print(f"== {arm}: departure bin | n ALKS | share3 X1, X2, X1-X2 [CI] | changes/veh X1, X2, X1-X2 [CI]")
        for lab, r in res[arm].items():
            a, c = r["share3"], r["changes"]
            print(f"  {lab:>10} {r['n_alks_median']:5.0f}  {a['X1']:.3f} {a['X2']:.3f} {a['X1-X2'][0]:+.3f} [{a['X1-X2'][1]:+.3f},{a['X1-X2'][2]:+.3f}]"
                  f"   {c['X1']:5.2f} {c['X2']:5.2f} {c['X1-X2'][0]:+.2f} [{c['X1-X2'][1]:+.2f},{c['X1-X2'][2]:+.2f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
