"""Independent re-derivation of the P1 clean-day / prevalence line from the raw run files (read only)."""
import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

RUN = "/home/catalin/work/phd/v5b1_runs/p1/v99/runs"
RES = "/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"
OUT = sys.argv[1]
EVAL = list(range(7400500, 7400600))
TUNE = list(range(7400200, 7400240))
CONDS = ("none", "slow", "block")
PIS = (0.05, 0.1, 0.25, 0.5, 1.0)
B, BSEED = 20000, 20261019


def load(key):
    try:
        with open(f"{RUN}/{key}.json") as f:
            d = json.load(f)
    except FileNotFoundError:
        return key, None
    assert d["key"] == key, key
    return key, (float(d["delay_s"]), bool(d["valid"]), int(d["teleports"]), float(d["served_ctrl_vph"]))


def fixed(g, c, q, s):
    return f"{g}_{c}_q{q}_s{s}"


def sw(N, a, inc, q, s):
    return f"{N}-{a}_{inc}_q{q}_s{s}"      # a may carry '+back'


def fa(N, g, q, s):
    return f"{N}-{g}_fa_none_q{q}_s{s}"


def mix(ds, db, dc, pi):
    return pi * (ds + db) / 2.0 + (1.0 - pi) * dc


IDX = np.random.default_rng(BSEED).integers(0, 100, size=(B, 100))


def paired(r, t):
    d = r - t
    sd, sr = np.median(d[IDX], axis=1), np.median(r[IDX], axis=1)
    rb = sd / sr
    return {"ref": float(np.median(r)), "treat": float(np.median(t)), "diff": float(np.median(d)),
            "diff_ci": [float(np.percentile(sd, 2.5)), float(np.percentile(sd, 97.5))],
            "rel": float(np.median(d) / np.median(r)),
            "rel_ci": [float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))]}


def main():
    R = json.load(open(RES))
    arms = R["tune"]["arms"]
    G, PI_ = R["G"], R["PI"]
    keys = set()
    for q in ("1600", "2000"):
        a = arms[q]
        ctrls = {a[x] for x in ("N", "FX", "FB", "PI", "AD")} | {"NC"}
        ctrls |= {g for p in a["prev"].values() for g in p.values()}
        for s in EVAL:
            keys |= {fixed(g, c, q, s) for g in ctrls for c in CONDS}
            for inc in ("slow", "block"):
                keys |= {sw(a["N"], a["ID"], inc, q, s), sw(a["N"], a["IP"][inc], inc, q, s)}
                keys.add(fa(a["N"], a["IP"][inc].replace("+back", ""), q, s))
        ad = [f"ad{e}_{a['FB']}" for e in ("0p5", "1", "2")]
        for s in TUNE:
            keys |= {fixed(g, c, q, s) for g in list(G) + list(PI_) + ad for c in CONDS}
    with ProcessPoolExecutor(8) as ex:
        res = dict(ex.map(load, sorted(keys), chunksize=500))
    missing = [k for k, v in res.items() if v is None]
    print("loaded", len(res), "missing", len(missing), missing[:10])
    json.dump({"res": res}, open(OUT, "w"))


if __name__ == "__main__":
    main()
