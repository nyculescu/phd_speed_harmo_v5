"""Screen D2 Rule 3: controller family G and the arm selections (pure; no SUMO).

G (35 controllers, in this fixed order, which also breaks ties):
- 'c<rate>': constant rate, the D1 grid (Addendum A1 of screen D1: 600, 800, 1000-2600 step 100; 19 rates);
  implemented as D1's FX: the D1 FBMeter with K_F = 0 and q = rate;
- 'f<K_F>_<n_crit>': the D1 FBMeter (Vinitsky et al. 2018 law, T = 30 s, q0 = 1500 veh/h) with
  K_F in {10, 20, 40, 70} x n_crit in {6, 8, 10, 12} (16).
'NC' (no meter, all-green) is a reference arm, not a member of G.

Switching at the incident onset (perfect detection) changes the running meter's parameters in place:
to 'c<r>' sets q = r and K_F = 0; to 'f<K>_<n>' sets K_F and n_crit and keeps the current rate q
(the feedback law continues from where the meter stands). The cycle clock and the 30-s update clock carry over.
"""
from __future__ import annotations

import numpy as np

RATES = (600.0, 800.0) + tuple(float(r) for r in range(1000, 2601, 100))   # == v5b.d1.run_screen.FX_GRID (tested)
KF_GRID = (10.0, 20.0, 40.0, 70.0)
NCRIT_GRID = (6.0, 8.0, 10.0, 12.0)
CONST = tuple(f"c{int(r)}" for r in RATES)
FEEDBACK = tuple(f"f{int(k)}_{int(n)}" for k in KF_GRID for n in NCRIT_GRID)
G = CONST + FEEDBACK
NC = "NC"


def parse(cid: str) -> tuple:
    """('const', rate) or ('fb', K_F, n_crit). Only members of G parse."""
    if cid not in G:
        raise ValueError(f"not a controller of G: {cid}")
    if cid.startswith("c"):
        return ("const", float(cid[1:]))
    k, n = cid[1:].split("_")
    return ("fb", float(k), float(n))


def meter_kwargs(cid: str) -> dict:
    """FBMeter constructor arguments for a controller run from the start of the control period."""
    p = parse(cid)
    if p[0] == "const":
        return {"K_F": 0.0, "q0": p[1]}
    return {"K_F": p[1], "n_crit": p[2]}


def switch(meter, cid: str) -> None:
    """Switch a running FBMeter to controller cid (at the incident onset)."""
    p = parse(cid)
    if p[0] == "const":
        meter.q, meter.K_F = p[1], 0.0
    else:
        meter.K_F, meter.n_crit = p[1], p[2]


def best_by_median(delays: dict, among=G) -> str:
    """The controller of `among` with the lowest median delay; ties go to the earlier one in G order.
    delays: cid -> per-seed (or pooled) delays. Controllers missing from `delays` are skipped."""
    cand = [c for c in among if c in delays and len(delays[c])]
    if not cand:
        raise ValueError("no candidate with data")
    return min(cand, key=lambda c: (float(np.median(np.asarray(delays[c], float))), G.index(c)))


def oracle_pick(per_g: dict) -> tuple:
    """OR for one seed: per_g = cid -> delay of the run 'N before onset, cid after onset'.
    Returns (cid, delay) with the lowest delay (hindsight); ties go to the earlier one in G order."""
    if not per_g:
        raise ValueError("no switch runs")
    c = min(per_g, key=lambda k: (float(per_g[k]), G.index(k)))
    return c, float(per_g[c])
