"""V240 report-only additions to the E1-lite report; lite_report and its rule stay as frozen at 8eb212c.

    python -m v5b.fleet.e1_lite_extra --freeze fz_lite.json --out L2_extra.json [--n 20]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from v5b.fleet import e1
from v5b.fleet import e1_analysis as ea

N_BLOCK = 10
# Share of full-day NC delay carried by 13:00-20:00 departures (stage-0 days 7,430,040-049, V239).
SLICE_SHARE = 0.858
EDGE_LANES = (":m_0_0",)


def all_braking(log: Path) -> int | None:
    if not log.exists():
        return None
    return sum("performs emergency braking" in ln for ln in log.read_text(errors="replace").splitlines())


def _eff(nc, x) -> dict:
    e = ea.effect(nc, x)
    return {"rel": e["rel"], "rel_ci": e["rel_ci"], "diff": e["diff"], "diff_ci": e["diff_ci"], "sign": e["sign"],
            "mean_rel": e["mean"]["rel"], "mean_rel_ci": e["mean"]["rel_ci"], "harm": ea.harm_label(e)}


def null_floor(X: np.ndarray, part: np.ndarray | None = None, R: int = 20000, seed: int = 11) -> dict:
    """Best-arm rel under the null: arms centred at their medians (only the `part` columns if given), then one random
    sign per seed for all flipped arms, which keeps the cross-arm correlation. X is seeds × arms in rel units."""
    rng = np.random.default_rng(seed)
    cols = np.ones(X.shape[1], bool) if part is None else part
    Xc = X.copy()
    Xc[:, cols] -= np.median(X[:, cols], axis=0)
    sg = rng.choice((-1.0, 1.0), size=(R, X.shape[0]))
    Y = np.repeat(Xc[None], R, axis=0)
    Y[:, :, cols] *= sg[:, :, None]
    best = np.median(Y, axis=1).max(axis=1)
    return {"mean": float(best.mean()), "p95": float(np.percentile(best, 95)), "P_ge_0.10": float((best >= 0.10).mean())}


def extra(fz: dict, n: int = 20, root: Path = e1.ROOT) -> dict:
    seeds = e1.main_seeds(N_BLOCK) + (e1.fresh_seeds(N_BLOCK) if n > N_BLOCK else [])
    keys = ["nc/base", *e1.grid(fz)]
    runs = {k: [e1._day(root / "L", "R", *k.split("/"), s) for s in seeds] for k in keys}
    if any(d is None for v in runs.values() for d in v):
        return {"incomplete": True}
    dirs = {k: [e1.out_dir(root / "L", "R", *k.split("/"), s) for s in seeds] for k in keys}
    nc = runs["nc/base"]
    dnc = np.array([d["d_all"] for d in nc])
    pm = lambda d: d["served"]["pm"]["main"] + d["served"]["pm"]["ramp"]  # noqa: E731
    out = {"n": len(seeds), "codes": sorted({d["code"] for v in runs.values() for d in v}),
           "stop_file": (root / "STOP.txt").exists(), "nc_valid": all(e1.valid(d) for d in nc),
           "nc": {"ttt_w_h": float(np.median([d["ttt_w_h"] for d in nc])), "served_pm": float(np.median([pm(d) for d in nc])),
                  "braking_all": [all_braking(p / f"sumo_s{s}.log") for p, s in zip(dirs["nc/base"], seeds)],
                  "braking_m00": [e1.braking_by_lane(p / f"sumo_s{s}.log", EDGE_LANES) for p, s in zip(dirs["nc/base"], seeds)],
                  "ramp_wait_max_s": float(np.median([d["ramp_merge"]["wait_max_s"] for d in nc]))},
           "arms": {}}
    X = []
    for k in keys[1:]:
        x = runs[k]
        dx = np.array([d["d_all"] for d in x])
        X.append((dnc - dx) / np.median(dnc))
        npz_nc = [p / f"conflicts_s{s}.npz" for p, s in zip(dirs["nc/base"], seeds)]
        npz_x = [p / f"conflicts_s{s}.npz" for p, s in zip(dirs[k], seeds)]
        a = {"all": _eff(dnc, dx), "flags": e1.flags(nc, x, npz_nc, npz_x, "R"),
             "served_pm": float(np.median([pm(d) for d in x])),
             "served_pm_diff": ea.effect(np.array([pm(d) for d in x], float), np.array([pm(d) for d in nc], float))["diff_ci"],
             "braking_all": [all_braking(p / f"sumo_s{s}.log") for p, s in zip(dirs[k], seeds)],
             "braking_m00": [e1.braking_by_lane(p / f"sumo_s{s}.log", EDGE_LANES) for p, s in zip(dirs[k], seeds)],
             "allowed_mismatch": sum((d["alks"] or {}).get("allowed_mismatch", 0) for d in x)}
        if n > N_BLOCK:
            a["L1"] = _eff(dnc[:N_BLOCK], dx[:N_BLOCK])
            a["L2"] = _eff(dnc[N_BLOCK:], dx[N_BLOCK:])
        if x[0]["meter"]:
            m = [d["meter"] for d in x]
            a["meter_waits_over_240"] = [mm["waits_over_240"] for mm in m]
            a["meter_wait_max_s"] = float(np.median([mm["wait_max_s"] for mm in m]))
        a["full_day_rel_approx"] = a["all"]["rel"] * SLICE_SHARE
        out["arms"][k] = a
    X = np.array(X).T
    ma = np.array([k.startswith("ma/") for k in keys[1:]])
    out["noise_floor"] = {"global_null": null_floor(X), "partial_null_alinea": null_floor(X, ma),
                          "sd_paired_rel": {k: float(s) for k, s in zip(keys[1:], X.std(axis=0, ddof=1))}}
    out["edge"] = {}
    for fam in ("ma", "c_short", "c_long"):
        fk = {k: np.array([d["d_all"] for d in runs[k]]) for k in keys[1:] if e1.variant(k) == fam}
        best = max(fk, key=lambda k: np.median(dnc - fk[k]))
        out["edge"][fam] = {"best": best, "next_setpoint": ea.edge_fires(dnc, fk, best, False)}
    c = ea.calibrate(nc)
    out["slice_loop_tests"] = {"tests": c.get("tests"), "n_onset": c.get("n_onset"), "o_cr": c.get("o_cr")}
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args(argv)
    r = extra(json.loads(Path(a.freeze).read_text()), a.n)
    Path(a.out).write_text(json.dumps(r, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print("incomplete" if r.get("incomplete") else f"written {a.out}: n {r['n']}, codes {r['codes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
