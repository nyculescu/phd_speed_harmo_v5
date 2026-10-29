"""Layer B crash rule (V163-V167, V173): conflict-driven, seeded crashes.

Encounter = one follower-leader pair with rear-end TTC below u in consecutive whole seconds. Its crash chance is
p(m) = min(1, k * w(m)), m = its lowest TTC so far; w = (u - m) / u ('linear', main) or 1 ('constant', sensitivity).
Only human followers (HDV car, truck) can crash ('human', main); 'all' is the sensitivity arm.
CRN: each encounter draws one uniform from (seed, follower, leader, start time); the crash happens the first time
p(running minimum) reaches it, so the same encounter in two arms has the same outcome. The blockage duration,
U(30, 60) min, comes from the same draw sequence.
k is set on crash-free no-control reference days so that the mean over days of P(>= 1 crash) is the target (25 %).
Until the first crash a day is crash-free, so this matches the probability of at least one crash exactly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from v5b.fleet import fleet as fl

U_MAIN = 1.5
TARGET = 0.25
HUMAN = ("hdv_car", "truck")
DURATION = (1800.0, 3600.0)
STREAM = 9001


def weight(m, u: float, shape: str):
    m = np.asarray(m, dtype=float)
    if shape == "constant":
        return np.ones_like(m)
    return np.clip((u - m) / u, 0.0, 1.0)


def p_crash(m, k: float, u: float, shape: str):
    return np.minimum(1.0, k * weight(m, u, shape))


def draws(seed: int, follower: int, leader: int, t_start: float) -> tuple:
    """(uniform for the crash decision, blockage duration in s), the same in every arm."""
    r = np.random.default_rng(np.random.SeedSequence([seed, STREAM, follower, leader, int(round(t_start * 10))]))
    return float(r.random()), float(r.uniform(*DURATION))


def encounters(z, u: float, who: str) -> np.ndarray:
    """Lowest TTC of every encounter in one day's conflict record (V167 day runner output)."""
    human = np.isin(z["cls"], [fl.CLASSES.index(c) for c in HUMAN])
    m = z["ttc"] < u
    if who == "human":
        m &= human[z["follower"]]
    t, f, l, ttc = z["t"][m], z["follower"][m], z["leader"][m], z["ttc"][m]
    order = np.lexsort((t, l, f))
    t, f, l, ttc = t[order], f[order], l[order], ttc[order]
    if not len(t):
        return np.array([])
    new = np.ones(len(t), bool)
    new[1:] = (f[1:] != f[:-1]) | (l[1:] != l[:-1]) | (t[1:] - t[:-1] > 1.0 + 1e-3)
    gid = np.cumsum(new) - 1
    out = np.full(gid[-1] + 1, np.inf)
    np.minimum.at(out, gid, ttc)
    return out


def p_day(mins: np.ndarray, k: float, u: float, shape: str) -> float:
    return float(1.0 - np.prod(1.0 - p_crash(mins, k, u, shape)))


def calibrate(days: list, u: float, shape: str, target: float = TARGET) -> dict:
    if not any(len(m) for m in days):
        return {"k": None, "u": u, "shape": shape, "encounters_per_day": 0.0, "p_day_mean": 0.0}
    lo, hi = 0.0, 1.0
    while np.mean([p_day(m, hi, u, shape) for m in days]) < target and hi < 1e6:
        hi *= 2
    for _ in range(80):
        k = (lo + hi) / 2
        if np.mean([p_day(m, k, u, shape) for m in days]) < target:
            lo = k
        else:
            hi = k
    k = (lo + hi) / 2
    pd = [p_day(m, k, u, shape) for m in days]
    lam = [float(p_crash(m, k, u, shape).sum()) for m in days]
    return {"k": k, "u": u, "shape": shape, "encounters_per_day": float(np.mean([len(m) for m in days])),
            "p_day_mean": float(np.mean(pd)), "p_day_range": [round(min(pd), 4), round(max(pd), 4)],
            "expected_crashes_per_day": float(np.mean(lam)),
            "p_max": max((float(p_crash(m, k, u, shape).max()) for m in days if len(m)), default=None)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    files = sorted(Path(a.runs).glob("conflicts_s*.npz"))
    zs = [np.load(f) for f in files]
    res = {"runs": a.runs, "days": len(zs), "target": TARGET, "arms": {}}
    for who in ("human", "all"):
        for u in (1.0, 1.5, 3.0):
            days = [encounters(z, u, who) for z in zs]
            for shape in ("linear", "constant"):
                res["arms"][f"{who}_u{u:g}_{shape}"] = calibrate(days, u, shape)
    Path(a.out).write_text(json.dumps(res, indent=1))
    for name, r in res["arms"].items():
        print(name, {x: (round(v, 6) if isinstance(v, float) else v) for x, v in r.items() if x not in ("u", "shape")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


class CrashProcess:
    """Live Layer B state for one run: open encounters, crashed vehicles and their release times."""

    def __init__(self, seed: int, k: float, u: float = U_MAIN, shape: str = "linear", who: str = "human"):
        self.seed, self.k, self.u, self.shape, self.who = seed, k, u, shape, who
        self.active = {}       # (follower idx, leader idx) -> [t start, t last, uniform, duration]
        self.release = {}      # vehicle id -> release time
        self.events = []

    def blocked(self, vid: str) -> bool:
        return vid in self.release

    def observe(self, t: float, f: int, l: int, f_vid: str, l_vid: str, f_cls: str, ttc: float) -> bool:
        """One second of an encounter; True when it turns into a crash now."""
        if ttc >= self.u or (self.who == "human" and f_cls not in HUMAN) or f_vid in self.release \
                or l_vid in self.release:
            return False
        e = self.active.get((f, l))
        if e is None or t - e[1] > 1.0 + 1e-3:
            e = [t, t, *draws(self.seed, f, l, t), ttc]
            self.active[(f, l)] = e
        e[1], e[4] = t, min(e[4], ttc)
        if p_crash(e[4], self.k, self.u, self.shape) < e[2]:
            return False
        self.release[f_vid] = self.release[l_vid] = t + e[3]
        self.events.append({"t": t, "follower": f_vid, "leader": l_vid, "follower_cls": f_cls, "min_ttc": round(e[4], 3),
                            "duration_s": round(e[3], 1), "other_crash_active": len(self.release) > 2})
        del self.active[(f, l)]
        return True

    def due(self, t: float) -> list:
        out = [v for v, tr in self.release.items() if tr <= t]
        for v in out:
            del self.release[v]
        return out

    def prune(self, t: float) -> None:
        self.active = {key: e for key, e in self.active.items() if t - e[1] <= 1.0 + 1e-3}


def first_crash(z, seed: int, k: float, u: float = U_MAIN, shape: str = "linear", who: str = "human") -> dict | None:
    """Replay a crash-free day's conflict record through the rule: the first crash a live run must reproduce."""
    p = CrashProcess(seed, k, u, shape, who)
    cls = [fl.CLASSES[c] for c in z["cls"]]
    for t, f, l, ttc in zip(z["t"], z["follower"], z["leader"], z["ttc"]):
        if p.observe(float(t), int(f), int(l), f"main.{f}", f"main.{l}", cls[f], float(ttc)):
            return p.events[0]
    return None
