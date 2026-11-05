"""Confirmatory 3 (V378): plant, conditions, seeds, rule families and the statistic, in one place."""
import gzip
import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PLANT = json.load(open(HERE / "plant_c3.json"))
H10 = {"hold": 10.0}
COND = {"S": None,
        "X1": {"kind": "slowdown", "edge": "4", "limit_kmh": 25, "dur": 120.0, "times": [600.0, 1200.0], "taper": 20.0},
        "X2": {"kind": "slowdown", "edge": "3", "limit_kmh": 30, "dur": 180.0, "times": [700.0], "taper": 20.0},
        "H1": {"kind": "truck", "cap_kmh": 50, "period": 300.0, "first": 360.0},
        "H2": {"kind": "burst", "cycle": 120.0}}
PRIMARY = ("X1", "X2")
Q = 5300.0
LEVELS = (4090.0, 4600.0, 5300.0)
SEEDS_CHECK = range(7_440_065, 7_440_075)
SEEDS_TUNE = range(7_440_160, 7_440_180)
SEEDS_TRACE = range(7_440_180, 7_440_190)
SEEDS_EVAL = range(7_440_200, 7_440_220)
SEED0, PER_WORKER, FIRST_WORKER, LEARNERS, ENVS, UPDATES, NET_SEED = 7_451_320, 520, 9, 5, 3, 500, 20261205


def families() -> dict:
    """form -> {rule: ctrl}. Levels: 0 = 1.6, 1 = 1.2, 2 = 1.0, 3 = 0.8 s."""
    f = {"uniform": {"p333" if k == 3 else f"u{k}": {"cav_rule": [k, k, k]} for k in range(4)}}
    f["zone"] = {"z" + "".join(map(str, p)): {"pattern": list(p)} for p in itertools.product((1, 3), repeat=5) if len(set(p)) > 1}
    f["on4a"] = {f"r4a{k}": {"road_levels": {"4a": k}} for k in range(3)}
    f["local"] = {f"lr{r}_{th}_{k}": {"local_rule": {"r": r, "th": th, "level": k}} for r in (400, 1000) for th in (10, 13, 16) for k in (1, 2)}
    f["adapt4a"] = {f"a4{r}_{th}_{k}": {"adaptive_4a": {"r": r, "th": th, "level": k, "road_level": k}} for r in (400, 1000) for th in (10, 13, 16) for k in (1, 2)}
    f["own"] = {f"os{k}_{th}_{c}": {"own_state": {"level": k, "th": th, "crowd": c}} for k in (1, 0) for th in (10, 15) for c in (0, 10)}
    return f


def cfg(ctrl: dict, cond: str, plant: dict | None = None) -> dict:
    x = COND[cond]
    if not ctrl:
        return {**(plant or PLANT), **({"ctrl": {"env": {"perturb": x}}} if x else {})}
    return {**(plant or PLANT), "ctrl": {**ctrl, "env": {**H10, **({"perturb": x} if x else {})}}}


def load(*files) -> dict:
    """(name, q) -> seed -> row. Plain or gzipped JSON lines."""
    T = defaultdict(dict)
    for f in files:
        with (gzip.open(f, "rt") if str(f).endswith(".gz") else open(f)) as h:
            for line in h:
                r = json.loads(line)
                T[(r["name"], r["q"])][r["seed"]] = r
    return T


def val(row: dict, key: str) -> float:
    """A counter that never fired is absent from the row."""
    v = row.get(key)
    return 0.0 if v is None else float(v)


def effect(A: dict, B: dict, key: str, sign: int = -1, pct=(1.25, 98.75)) -> tuple:
    """Median of paired differences over the reference's median, in %, higher is better; percentile bootstrap, denominator fixed."""
    ds = sorted(set(A) & set(B))
    if not ds:
        raise ValueError("no paired seeds")
    ref = max(float(np.median([val(B[k], key) for k in ds])), 1e-9)
    d = np.array([sign * (val(A[k], key) - val(B[k], key)) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261104)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), pct)
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(A: dict, key: str) -> float:
    return float(np.median([val(x, key) for x in A.values()]))


def paired_median(A: dict, B: dict, key: str) -> float:
    """Median of A minus B over paired seeds, in the metric's own units."""
    ds = sorted(set(A) & set(B))
    return float(np.median([val(A[k], key) - val(B[k], key) for k in ds]))


def collisions(A: dict) -> float:
    return float(sum(val(x, "collisions") for x in A.values()))
