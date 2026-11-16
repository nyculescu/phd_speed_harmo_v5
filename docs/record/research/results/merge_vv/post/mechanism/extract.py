"""Post hoc, descriptive: one compact per-run table from the V&V screen rows (no reading is decided here).

usage: extract.py ROWS ST_DIR OUT.pkl [ARM,ARM,...]"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROADS = ("3a", "ramp1", "4a", "ramp2", "1", "2", "3", "4", "5", "junction", "other")
PERIODS = ("before", "taper", "hold", "after", "rest")
SPEED_ROADS = ("1", "2", "3a", "3", "4a", "ramp1", "ramp2")
CONG = 50.0 / 3.6     # post hoc: a 50-m by 10-s cell below 50 km/h counts as congested
E1_END, E2_END = 3000.0, 3498.3
WARM = 300.0     # MergeEnv default; the field has 150 bins of 10 s = the 1,500-s episode


def st_edge1(f: Path, dx: float, dt: float, warm: float, onset: float, dur: float) -> dict:
    """Edge-1 queue from the space-time field: congested cells on edge 1 per time bin, by period, and the most upstream one."""
    z = np.load(f)
    v, n = z["v"].astype(float), z["n"].astype(float)
    assert v.shape[0] * dt == 1500.0, v.shape
    sp = np.where(n > 0, v / np.maximum(n, 1e-9), np.nan)
    nx1 = int(E1_END // dx)
    t = warm + (np.arange(sp.shape[0]) + 0.5) * dt
    per = np.where(t < onset, "before", np.where(t < onset + 20.0, "taper", np.where(t < onset + dur, "hold",
                   np.where(t < onset + dur + 120.0, "after", "rest"))))
    e1 = sp[:, :nx1]
    cong = np.nan_to_num(e1 < CONG, nan=0).astype(bool)
    ncong = cong.sum(axis=1)
    # queue reach: the most upstream congested cell of the run of congested cells that touches the edge-1 end
    reach = np.zeros(sp.shape[0])
    for k in range(sp.shape[0]):
        j = nx1 - 1
        while j >= 0 and cong[k, j]:
            j -= 1
        reach[k] = (nx1 - 1 - j) * dx
    out = {}
    for p in PERIODS:
        m = per == p
        out[f"e1cong_{p}"] = float(ncong[m].sum()) if m.any() else 0.0     # cell-bins (50 m x 10 s) congested
        out[f"e1reach_max_{p}"] = float(reach[m].max()) if m.any() else 0.0
        out[f"e1reach_mean_{p}"] = float(reach[m].mean()) if m.any() else 0.0
        e1v = e1[m]
        out[f"e1v_{p}"] = float(np.nanmean(e1v)) if m.any() and np.isfinite(e1v).any() else np.nan
    e2 = sp[:, nx1:int(E2_END // dx)]
    out["e2v_before"] = float(np.nanmean(e2[per == "before"])) if (per == "before").any() else np.nan
    return out


def main(rows: str, st: str, out: str, arms: str = "") -> None:
    keep = set(arms.split(",")) if arms else None
    recs = []
    with open(rows) as fh:
        for line in fh:
            if keep is not None and line[:200].split('"name": "', 1)[-1].split('"', 1)[0].split("|", 1)[-1] not in keep:
                continue
            r = json.loads(line)
            cell, arm = r["name"].split("|", 1)
            d = {"cell": cell, "arm": arm, "seed": int(r["seed"]), "ttc_net": float(r["ttc_net"]), "main": float(r.get("vv_ttc3_main", 0)),
                 "enc": float(r.get("vv_enc", 0)), "all_delay": float(r["all_delay"]), "passed": float(r["passed"]), "N": float(r["N"]),
                 "end_stop": float(r.get("end_stop", 0)), "end_stop2": float(r.get("end_stop2", 0)), "merges": float(r.get("vv_merges", 0)),
                 "onset": float(r["pert_log"][0][1]), "dur": float(r["pert_log"][0][2]), "veh_n": (r.get("c1_t0") or {}).get("veh_n")}
            for x in ("3a_0", "4a_0"):
                d[f"stand_s_{x}"] = float(r.get("vv_stand_s", {}).get(x, 0))
                d[f"stand_n_{x}"] = float(r.get("vv_stand_n", {}).get(x, 0))
            ttc = r.get("m_road_ttc3", {})
            extra = set(ttc) - set(ROADS)
            d["unknown_roads"] = ",".join(sorted(extra))
            for g in ROADS:
                for p in PERIODS:
                    d[f"t|{g}|{p}"] = float(ttc.get(g, {}).get(p, 0))
            for p in PERIODS:
                d[f"p_{p}"] = float(r.get(f"ttc3_p_{p}", 0.0))
            vs, dist = r.get("m_road_vs", {}), r.get("m_road_dist", {})
            for g in SPEED_ROADS:
                for p in PERIODS:
                    d[f"vs|{g}|{p}"] = float(vs.get(g, {}).get(p, 0.0))
                    d[f"dist|{g}|{p}"] = float(dist.get(g, {}).get(p, 0.0))
            lanes = r.get("vv_lanes", {})
            d["len_1_0"], d["len_2_0"], d["len_3a_0"], d["len_4a_0"] = (lanes.get(x) for x in ("1_0", "2_0", "3a_0", "4a_0"))
            d["offsets"] = json.dumps(r.get("m_offsets"))
            d["lanes_other"] = json.dumps({k: round(v, 2) for k, v in sorted(lanes.items()) if not k.startswith(("3a_", "4a_"))})
            f = Path(st) / Path(r["m_st_file"]).name
            d |= st_edge1(f, r["m_st_dx"], r["m_st_dt"], WARM, d["onset"], d["dur"])
            d["st_file"] = f.name
            d["st_dx"], d["st_dt"] = r["m_st_dx"], r["m_st_dt"]
            recs.append(d)
    df = pd.DataFrame(recs)
    df.to_pickle(out)
    print(len(df), "rows;", df.groupby("cell").size().to_dict())


if __name__ == "__main__":
    main(*sys.argv[1:5])
