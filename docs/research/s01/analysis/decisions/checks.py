"""Which arms carry decision fields, whether the pack's level-seconds equal the environment's own count, and what p333's
decision fields hold (read only)."""
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")


def main() -> int:
    T = pickle.load(open(HERE / "compact.pkl", "rb"))
    has = defaultdict(lambda: [0, 0])
    lv_eq = defaultdict(lambda: [0, 0])
    for (ph, name, q, seed), r in T.items():
        arm = name.split("|")[1]
        has[arm][0] += 1
        has[arm][1] += bool(r.get("m_dec_totals"))
        if "m_dec_level_s" in r and len(r.get("lv", [])) == 12:
            lv_eq[arm][0] += 1
            lv_eq[arm][1] += r["m_dec_level_s"] == np.asarray(r["lv"]).reshape(3, 4).sum(0).tolist()
    out = {"rows_with_dec": {a: v for a, v in sorted(has.items())}, "level_s_eq_lv": {a: v for a, v in sorted(lv_eq.items())}}
    print("arm: rows, rows with non-empty m_dec_totals")
    print({a: v for a, v in sorted(has.items())})
    print("arm: rows with lv, rows where m_dec_level_s == lv summed over zones")
    print({a: v for a, v in sorted(lv_eq.items())})

    # p333: decision fields per cell and level
    rep = {}
    for (ph, name, q, seed), r in T.items():
        if not name.endswith("|p333"):
            continue
        k = f"{name.split('|')[0]}|{q:.0f}"
        L = np.asarray(r["m_dec_level_s"], float)
        D = r["m_dec_totals"]
        rep.setdefault(k, []).append({"share3": L[3] / L.sum(), "share0": L[0] / L.sum(), "share1": L[1] / L.sum(), "share2": L[2] / L.sum(),
                                      "want3": r["m_dec_want"][3] / sum(r["m_dec_want"]), "reversals": D["reversals"], "excess": r["m_dec_excess"],
                                      "changed_per_veh": D["changed"] / r["m_dec_vehicles"], "on_s_per_veh": L.sum() / r["m_dec_vehicles"],
                                      "climb_on_s_per_veh": L[:3].sum() / r["m_dec_vehicles"], "v2v_on": L.sum() / (L.sum() + r["m_dec_off_s"]),
                                      "conf_sum": sum(r["m_dec_conf"]), "entropy": r["m_dec_entropy_mean"], "ignored_share": D["ignored"] / D["asked"],
                                      "applied_share": D["changed"] / D["asked"], "tau_on_match": r.get("tau_on_match", 0) / max(r.get("tau_on_n", 1), 1)})
    print("\np333 per cell|level: medians over seeds (min-max for share3)")
    summ = {}
    for k in sorted(rep):
        X = rep[k]
        s = {f: float(np.median([x[f] for x in X if x[f] is not None])) if any(x[f] is not None for x in X) else None for f in X[0]}
        s["share3_min"], s["share3_max"], s["n"] = float(min(x["share3"] for x in X)), float(max(x["share3"] for x in X)), len(X)
        summ[k] = s
        print(k, {f: (round(v, 4) if isinstance(v, float) else v) for f, v in s.items()})
    out["p333"] = summ

    # Per-vehicle check of the climb on one p333 run per phase: seconds at levels 0-2 with V2V on, and the last level
    vv = {}
    for f in ("X1__p333__5300__7440840.npz", "B__p333__6000__7440880.npz", "B__p333__3500__7440900.npz", "B__os1_15_10__4500__7440880.npz"):
        z = np.load(DATA / "st" / f)
        d, L = z["dec"], z["dec_level_s"]
        last = d[:, 5]
        vv[f] = {"vehicles": int(len(d)), "last_level_counts": np.bincount(last, minlength=4).tolist(), "reversals": int(d[:, 4].sum()),
                 "on_s_lvl0_2_p50_p95_max": [float(np.percentile(L[:, :3].sum(1), p)) for p in (50, 95, 100)],
                 "on_s_lvl3_p50": float(np.median(L[:, 3])), "off_s_p50": float(np.median(L[:, 4])),
                 "share3_pooled": float(L[:, 3].sum() / L[:, :4].sum()),
                 "share3_vehicles_at_last3": float(L[last == 3, 3].sum() / max(L[last == 3, :4].sum(), 1))}
        print(f, vv[f])
    out["p333_vehicles"] = vv
    (HERE / "checks.json").write_text(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
