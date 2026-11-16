"""V368 trace of the shot: policies and r4a1 against p333 on the three seed sets, from stored rows. usage: shot_trace.py"""
import collections
import gzip
import json
from pathlib import Path

import numpy as np

D = Path(__file__).parent


def load(name, keep=lambda r: True, key=lambda r: r["name"]):
    t = collections.defaultdict(dict)
    for line in gzip.open(D / name, "rt"):
        r = json.loads(line)
        if keep(r):
            t[key(r)][r["seed"]] = r
    return t


SETS = (("conf2 100-119", load("eval_rows.jsonl.gz", lambda r: r["q"] == 5300 and r["name"].startswith("r2m3|"), lambda r: r["name"][5:])),
        ("rule 120-139", load("rulecheck_rows.jsonl.gz")), ("shot 140-159", load("shot_rows.jsonl.gz")))


def diff(t, a, b, key):
    ds = sorted(set(t[a]) & set(t[b]))
    ref = max(float(np.median([t[b][k][key] for k in ds])), 1e-9)
    d = np.array([-(t[a][k][key] - t[b][k][key]) / ref * 100 for k in ds])
    lo, hi = np.percentile(np.median(d[np.random.default_rng(20261104).integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


for cell in ("S", "X1", "X2"):
    print("==", cell)
    for lab, t in SETS:
        pol = sorted(n.split("|")[1] for n in t if n.startswith(cell + "|d"))
        ttc = [diff(t, f"{cell}|{p}", f"{cell}|p333", "ttc_net")[0] for p in pol]
        dly = [diff(t, f"{cell}|{p}", f"{cell}|p333", "delay")[0] for p in pol]
        print(f" {lab}: policies vs p333, TTC {min(ttc)} to {max(ttc)}, delay {min(dly)} to {max(dly)}")
        if f"{cell}|r4a1" in t:
            print(f"   r4a1 vs p333: TTC {diff(t, f'{cell}|r4a1', f'{cell}|p333', 'ttc_net')}, delay {diff(t, f'{cell}|r4a1', f'{cell}|p333', 'delay')}")
