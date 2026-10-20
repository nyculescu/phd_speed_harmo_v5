"""P1b action set (p1b_addendum.md B3, R1; pure, no SUMO). Controllers, grids and parsing are P1's (v5b/p1/family.py).

- G_PI(q) = the N_GPI = 10 PI controllers (P1's PI grid) with the lowest pooled (slow + block) median delay on the P1b
  tuning seeds, per q; ties in P1's PI order. Fixed before evaluation.
- A(q) = (G u G_PI(q)) x {stay, back} = 120 actions. Order (= tie order, R1 "G, then G_PI"): every stay action of G,
  every back action of G (P1's A, unchanged), then every stay action of G_PI(q), then every back action of G_PI(q).
- Plans switch from N (a member of G) into any controller of G u PI (v5b/p1b/meters.P1bMeter.set_law).
"""
from __future__ import annotations

import numpy as np

from v5b.p1 import family as fam

N_GPI = 10
BACK = fam.BACK


def is_plan(cid: str) -> bool:
    return cid in fam.G or cid in fam.PI


def actions(G_, GPI_=()) -> tuple:
    if any(g not in fam.PI for g in GPI_):
        raise ValueError(f"G_PI must hold PI controllers: {GPI_}")
    return fam.actions(G_) + (fam.actions(GPI_) if GPI_ else ())


def parse_action(a: str) -> tuple:
    back = a.endswith(BACK)
    g = a[: -len(BACK)] if back else a
    if not is_plan(g):
        raise ValueError(f"not an action of A: {a}")
    return g, back


def top_pi(pooled: dict, PI_, n: int = N_GPI) -> tuple:
    """The n ids of PI_ with the lowest median of pooled[id] (ties: PI_ order); ids without data are skipped."""
    PI_ = tuple(PI_)
    cand = [c for c in PI_ if c in pooled and len(pooled[c])]
    if len(cand) < n:
        raise ValueError(f"only {len(cand)} PI controllers with data, need {n}")
    return tuple(sorted(cand, key=lambda c: (float(np.median(np.asarray(pooled[c], float))), PI_.index(c)))[:n])
