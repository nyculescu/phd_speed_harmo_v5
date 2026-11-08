"""(b, c) Where and when the close-following difference to no control sits, in X1 and X2: the plant's 1-Hz TTC < 3 s count
(ttc3, which equals ttc_net on these rows: checked below) split by period (ttc3_p_before/taper/hold/after/rest) and by road
(ttc3_r_3/4a/ramp2/rest). Paired median difference to no control in TTC-seconds per run, 95 % CI; and the arm's mean commanded
level per road (lv_<road>, 1 Hz, all ALKS, V2V on or off)."""
import json
import pickle
import sys

import numpy as np

from common_dec import GROUPS, HERE, paired_diff, med_ci, load_table, arm_values

PER = ("before", "taper", "hold", "after", "rest")
ROADS = ("3", "4a", "ramp2", "rest")
ARMS = {"v3w": GROUPS["v3w"], "tail": GROUPS["tail"], "sw": GROUPS["sw"], "baseline-v3": GROUPS["baseline-v3"],
        "os1_15_10": ["os1_15_10"], "3E-T": ["3e"], "p333": ["p333"], "copy": ["copy"]}
LV_ROADS = ("1", "2", "3a", "3", "4a", "4", "5", "r", "rj", "r2", "rj2")


def main() -> int:
    T = pickle.load(open(HERE / "compact.pkl", "rb"))
    eq = sum(abs(r.get("ttc3", 0.0) - r["ttc_net"]) < 1e-9 for r in T.values())
    print(f"rows with ttc3 == ttc_net: {eq} of {len(T)}")
    V = {}
    for (ph, name, q, seed), r in T.items():
        if ph != "test":
            continue
        cell, arm = name.split("|")
        d = {f"p_{p}": r.get(f"ttc3_p_{p}", 0.0) for p in PER} | {f"r_{x}": r.get(f"ttc3_r_{x}", 0.0) for x in ROADS}
        V.setdefault(cell, {}).setdefault(arm, {})[seed] = d
    out, n = {"ttc3_eq_ttc_net_rows": eq}, 0
    M = load_table()
    for cell in ("X1", "X2"):
        out[cell] = {}
        nc = V[cell]["nc"]
        ncd = {f: {s: nc[s][f] for s in nc} for f in nc[next(iter(nc))]}
        out[cell]["nc_median"] = {f: float(np.median(list(x.values()))) for f, x in ncd.items()}
        for g, names in ARMS.items():
            res = {}
            for f in ncd:
                A = {s: float(np.mean([V[cell][nm][s][f] for nm in names])) for s in nc}
                res[f] = {"arm_median": float(np.median(list(A.values()))), "minus_nc": paired_diff(A, ncd[f])}
                n += 1
            res["lv"] = {rd: med_ci(arm_values(M, ("test", cell, 5300.0), names, f"lv_{rd}"))[0] for rd in LV_ROADS
                         if arm_values(M, ("test", cell, 5300.0), names, f"lv_{rd}")}
            out[cell][g] = res
    out["comparisons"] = n
    (HERE / "analysis_bc_periods.json").write_text(json.dumps(out, indent=1))
    for cell in ("X1", "X2"):
        print(f"== {cell}: nc medians (TTC-seconds) {{{', '.join(f'{k}: {v:.0f}' for k, v in out[cell]['nc_median'].items())}}}")
        for g in ARMS:
            r = out[cell][g]
            print(f"  {g:<12}" + "  ".join(f"{f[2:] if f.startswith('p_') else 'road ' + f[2:]} {r[f]['minus_nc'][0]:+.0f} [{r[f]['minus_nc'][1]:+.0f},{r[f]['minus_nc'][2]:+.0f}]" for f in r if f != "lv"))
            print(f"  {'':<12}lv " + " ".join(f"{k}:{v:.2f}" for k, v in r["lv"].items()))
    print("comparisons", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
