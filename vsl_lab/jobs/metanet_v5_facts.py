"""METANET v5 real-side facts (protocol v5 §B1.1): the 22 usable calibration days only. No model output, no
validation day, no F11 field.

python -m vsl_lab.jobs.metanet_v5_facts build [--out DIR]   # -> metanet_v5_precal_facts.json + _masks.npz

Contents: real episodes per pair, t_c, heavy flags, C4, merge sections, real extents and valid flags, W_d, F_d, the
P1c sets with leave-one-day-out nulls, every qualifying-set size, the row set R, the weights ω_k, the full-precision
ρ_cr,G3 of the three D4.12 plants, and the git blob hashes of the reused v3/v4 facts files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_facts as F
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_gate as G
from vsl_lab.jobs import metanet_j5 as J
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

RUNS5 = Path("/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v5")
EV0, NB = Q.EV0, M.N_BINS
MPH = 1.609344
D412_TARGETS = (2400.0, 2100.0, 1900.0)


def _blob(path: Path) -> str:
    return subprocess.run(["git", "-C", str(C.REPO), "hash-object", str(path)], capture_output=True, text=True,
                          check=True).stdout.strip()


def loo_nulls(v: np.ndarray, mv: np.ndarray, d: int) -> tuple:
    """The gate's N1/N2 (metanet_gate.nulls) from the other calibration days (leave day d out)."""
    keep = [i for i in range(v.shape[0]) if i != d]
    x = np.where(mv[keep], v[keep], np.nan)[:, :, EV0:]
    n1 = np.array([np.nanmedian(np.where(x[:, s] >= 45 * MPH, x[:, s], np.nan)) if np.any(x[:, s] >= 45 * MPH)
                   else np.nan for s in range(x.shape[1])])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        n2 = np.nanmedian(x, axis=0)
    full2 = np.full((x.shape[1], NB), np.nan)
    full2[:, EV0:] = n2
    return n1, full2


def f_mask(W: np.ndarray, pairs: dict) -> np.ndarray:
    """F_d over model bins: 05:00-23:00 minus W_d minus ±30 min around every real episode at any event pair."""
    f = np.zeros(NB, bool)
    f[EV0:] = True
    f &= ~W
    for eps in pairs.values():
        for s, e in eps:
            f[max(0, EV0 + s - 6):min(NB, EV0 + e + 7)] = False
    return f


def d412_rho_cr() -> dict:
    """ρ_cr,G3 of the D4.12 diagnostic plants at the full-precision v4 nominal (as the recovered diagnostic script)."""
    p0 = Q.plant_params()
    cap0 = p0["vf3"] * math.exp(-1 / p0["a3"]) * p0["rc3"]
    return {"cap0_veh_h_lane": cap0, "rc3_nominal": p0["rc3"],
            **{str(int(t)): p0["rc3"] * t / cap0 for t in D412_TARGETS}}


def build(out: Path) -> dict:
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    sids = [s["id"] for s in net.stations]
    qa = np.array([s in I.Q_A for s in sids])
    ev = {d: F.day_events(d) for d in days}
    nd = len(days)
    Wm, Fm, Pm = (np.zeros((nd, len(sids), NB), bool) for _ in range(3))
    per = {}
    for i, d in enumerate(days):
        e = ev[d]
        pairs = {k: v_ for k, v_ in I.event_pairs(d).items() if v_}
        W = I.congestion_window(d)
        Fd = f_mask(W, pairs)
        Wm[i], Fm[i] = W[None, :], Fd[None, :]
        rsp = {s: I.event_station(d, s)["v"] for s in I.EVENT_STATIONS}
        rvl = {s: bool(I.event_station(d, s)["valid"]) for s in I.EVENT_STATIONS}
        active = bool(e["B1"] or e["B2"])
        rec = {"B1": e["B1"], "B2": e["B2"], "censor": {str(k): v_ for k, v_ in e["censor"].items()},
               "B1_long": e["B1_long"], "B2_long": e["B2_long"], "first": e["first"], "heavy_first": e["heavy_first"],
               "pairs": {f"{u}->{w}": eps for (u, w), eps in pairs.items()}, "valid": rvl,
               "merge": [F.merge_section(d, k, e) for k in ("B1", "B2")],
               "W_bins": int(W.sum()), "F_bins": int(Fd.sum())}
        if e["B1_long"] and e["B1_long"]["heavy"] or e["B2_long"] and e["B2_long"]["heavy"]:
            rk = "B1" if e["B1"] else "B2"
            rec["r_ext"] = G.extent(rsp, rvl, G.UPST[rk], [tuple(x) for x in list(e["B1"]) + list(e["B2"])])
        if active:
            n1, n2 = loo_nulls(data["v"], data["mv"], i)
            win = np.zeros(NB, bool)
            for s, e_ in list(e["B1"]) + list(e["B2"]):
                win[max(0, EV0 + s - 6):min(NB, EV0 + e_ + 7)] = True
            m = data["mv"][i] & qa[:, None] & win[None, :] & np.isfinite(n2) & np.isfinite(n1)[:, None]
            Pm[i] = m
            rec["P1c_null_N1"] = V.nrmse(np.broadcast_to(n1[:, None], m.shape), data["v"][i], m)
            rec["P1c_null_N2"] = V.nrmse(n2, data["v"][i], m)
            if rec["P1c_null_N1"] is not None and rec["P1c_null_N2"] is not None:
                rec["P1c_N1_minus_N2"] = rec["P1c_null_N1"] - rec["P1c_null_N2"]
        per[d] = rec
    np.savez_compressed(out / "metanet_v5_precal_masks.npz", days=np.array(days), stations=np.array(sids),
                        W=Wm, F=Fm, P1c=Pm)
    # qualifying sets (anchored on real data) and the row set R
    heavy = {k: [d for d in days if ev[d][k + "_long"] and ev[d][k + "_long"]["heavy"]] for k in ("B1", "B2")}
    both = [d for d in days if d in heavy["B1"] and d in heavy["B2"]]
    both_q = [d for d in both if all(per[d]["merge"])]
    hv_any = [d for d in days if d in heavy["B1"] or d in heavy["B2"]]
    act = [d for d in days if ev[d]["B1"] or ev[d]["B2"]]
    p1c_days = [d for d in act if "P1c_N1_minus_N2" in per[d]]
    N = {}
    for kk, k in ((1, "B1"), (2, "B2")):
        N[f"P3-{kk}"] = nd
        N[f"X-{kk}"] = sum(1 for d in days if not ev[d][k])
        N[f"P4-{kk}"] = sum(len(ev[d][k]) for d in days)
        N[f"P5a-{kk}"] = N[f"P7a-{kk}"] = len(heavy[k])
    p5c_kept = len(both) >= 6
    N["P5c"] = len(both_q) if p5c_kept else 0
    N["P7b"] = N["P7c"] = len(hv_any)
    for r in ("P8g", "P1a_h", "P1b_h", "P1a_ff", "P1b_ff"):
        N[r] = nd
    N["P1c_h"] = len(p1c_days)
    R = [r for r, n in N.items() if n > 0]
    w = {r: 1.0 for r in R}
    omega = {}
    for kk, k in ((1, "B1"), (2, "B2")):
        if f"X-{kk}" not in R:
            continue
        actk = [dict(e=len(ev[d][k]), heavy=d in heavy[k], both=d in both_q) for d in days if ev[d][k]]
        U, om = J.parity_omega(actk, {"P3": N[f"P3-{kk}"], "P4": N[f"P4-{kk}"], "P5a": N[f"P5a-{kk}"],
                                      "P7a": N[f"P7a-{kk}"], "P5c": max(N["P5c"], 1), "X": N[f"X-{kk}"]},
                               keep_p5c=p5c_kept)
        omega[k] = {"U": U, "omega": om}
        w[f"X-{kk}"] = om
    facts = {"protocol": "docs/plans/day_pattern_metanet_protocol_v5.md", "days": days, "per_day": per,
             "qualifying": {"heavy": heavy, "both": both, "both_q": both_q, "heavy_any": hv_any, "active": act,
                            "P1c_days": p1c_days, "P5c_kept": p5c_kept},
             "N": N, "rows": R, "weights": w, "parity": omega,
             "P1c_days_N1_minus_N2_below_0.02": sum(1 for d in p1c_days if per[d]["P1c_N1_minus_N2"] < 0.02),
             "P1c_days_N1_minus_N2_below_0": sum(1 for d in p1c_days if per[d]["P1c_N1_minus_N2"] < 0),
             "d412_rho_cr_G3": d412_rho_cr(),
             "masks_npz_sha256": hashlib.sha256((out / "metanet_v5_precal_masks.npz").read_bytes()).hexdigest(),
             "calib_data_sha256": hashlib.sha256((C.RUNS / "calib_data.npz").read_bytes()).hexdigest(),
             "reused_facts_blobs": {"v3": _blob(C.FACTS), "v4": _blob(C.FACTS_V4)}}
    (out / "metanet_v5_precal_facts.json").write_text(json.dumps(facts, indent=1, default=float))
    return facts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["build"])
    ap.add_argument("--out", default=str(RUNS5))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from vsl_lab.jobs import metanet_v5_calibrate as V5
    V5.pre_batch_checks()                                      # the cache the facts freeze = the committed manifest
    with V5.stage("metanet-v5-facts", "metanet_v5_facts_build", {"out": str(out), "code_commit": V5.code_commit()}) as st:
        f = build(out)
        st.result = {"rows": len(f["rows"]), "omega_2": f["weights"].get("X-2")}
    print(json.dumps({"rows": f["rows"], "N": f["N"], "parity": f["parity"],
                      "P1c_low": [f["P1c_days_N1_minus_N2_below_0.02"], f["P1c_days_N1_minus_N2_below_0"]]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
