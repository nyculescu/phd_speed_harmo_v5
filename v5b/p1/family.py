"""P1 controller families (docs/research/protocols/p1_incident_information.md §2; pure, no SUMO).

Family G (A5(a), extended once): D2's grid (v5b/d2/controllers.py) + rate 400, + K_F 120, + n_crit 14 and 16:
- 'c<rate>': constant rate, rates 400, 600, 800, 1000-2600 step 100 (20); D1's FBMeter with K_F = 0, q = rate;
- 'f<K_F>_<n_crit>': D1's FBMeter (T = 30 s, q0 = 1500) with K_F in {10, 20, 40, 70, 120} x n_crit in {6, ..., 16} (30).
G has 50 controllers in this fixed order (constants by rate, then feedback K_F-major), which also breaks ties (as D2).
A = G x {stay, back}: 100 actions; order (ties): every stay action in G order, then every back action in G order.
Switching at onset (D2-A4 d, unchanged): to 'c<r>' sets q = r and K_F = 0; to 'f<K>_<n>' sets K_F and n_crit and keeps q.

L0 arms outside G (page §2):
- PI 'p<K_P>_<K_I>_<n_crit>_e4|e5': q(k) = q(k-1) - K_P (n(k) - n(k-1)) + K_I (n_crit - n(k)), T = 30 s, other settings
  as FB. Grid: K_P in {20, 40, 70} x K_I in G's K_F values x (n_crit in G's n_crit values on the edge-4 count, or
  n_crit in {2, ..., 12} on the edge-5 count): 3 x 5 x (6 + 6) = 180 controllers;
- AD 'ad<eta>_f<K>_<n>': FB 'f<K>_<n>' (FB's tuned values) with the adaptive set point, eta in {0.5, 1, 2}.
'NC' (no meter) is a reference arm.
"""
from __future__ import annotations

import numpy as np

RATES = (400.0, 600.0, 800.0) + tuple(float(r) for r in range(1000, 2601, 100))
KF_GRID = (10.0, 20.0, 40.0, 70.0, 120.0)
NCRIT_GRID = (6.0, 8.0, 10.0, 12.0, 14.0, 16.0)
CONST = tuple(f"c{int(r)}" for r in RATES)
FEEDBACK = tuple(f"f{int(k)}_{int(n)}" for k in KF_GRID for n in NCRIT_GRID)
G = CONST + FEEDBACK
NC = "NC"
BACK = "+back"

KP_GRID = (20.0, 40.0, 70.0)
KI_GRID = KF_GRID
PI_NCRIT = {"e4": NCRIT_GRID, "e5": (2.0, 4.0, 6.0, 8.0, 10.0, 12.0)}
PI_EDGE = {"e4": "4", "e5": "5"}
PI = tuple(f"p{int(kp)}_{int(ki)}_{int(n)}_{e}" for e in ("e4", "e5") for kp in KP_GRID for ki in KI_GRID
           for n in PI_NCRIT[e])
ETA_GRID = (0.5, 1.0, 2.0)
AD_NHAT_MIN, AD_NHAT_MAX = 4.0, 20.0


def _fmt(x: float) -> str:
    return f"{x:g}".replace(".", "p")


def ad_id(eta: float, fb: str) -> str:
    if eta not in ETA_GRID or fb not in FEEDBACK:
        raise ValueError(f"AD needs eta in {ETA_GRID} and an FB controller of G: {eta}, {fb}")
    return f"ad{_fmt(eta)}_{fb}"


def parse(cid: str) -> tuple:
    """('const', rate) | ('fb', K_F, n_crit) | ('pi', K_P, K_I, n_crit, edge) | ('ad', eta, K_F, n_crit)."""
    if cid in CONST:
        return ("const", float(cid[1:]))
    if cid in FEEDBACK:
        k, n = cid[1:].split("_")
        return ("fb", float(k), float(n))
    if cid in PI:
        kp, ki, n, e = cid[1:].split("_")
        return ("pi", float(kp), float(ki), float(n), PI_EDGE[e])
    if cid.startswith("ad") and "_f" in cid:
        eta_s, fb = cid[2:].split("_", 1)
        eta = float(eta_s.replace("p", "."))
        if cid == ad_id(eta, fb):
            p = parse(fb)
            return ("ad", eta, p[1], p[2])
    raise ValueError(f"not a P1 controller: {cid}")


def is_g(cid: str) -> bool:
    return cid in G


def action(g: str, back: bool) -> str:
    if g not in G:
        raise ValueError(f"not a controller of G: {g}")
    return g + BACK if back else g


def parse_action(a: str) -> tuple:
    back = a.endswith(BACK)
    g = a[: -len(BACK)] if back else a
    if g not in G:
        raise ValueError(f"not an action of A: {a}")
    return g, back


def actions(G_=G) -> tuple:
    return tuple(G_) + tuple(g + BACK for g in G_)


A = actions(G)


def rank(a: str) -> tuple:
    g, back = parse_action(a)
    return (back, G.index(g))


def switch(meter, cid: str) -> None:
    """D2-A4 d with the extended G: switch a running FBMeter to controller cid of G."""
    p = parse(cid)
    if p[0] == "const":
        meter.q, meter.K_F = p[1], 0.0
    elif p[0] == "fb":
        meter.K_F, meter.n_crit = p[1], p[2]
    else:
        raise ValueError(f"switch targets are members of G only: {cid}")


def best_by_median(delays: dict, among) -> str:
    """The id of `among` with the lowest median of delays[id]; ties go to the earlier one in `among` (the families
    and A are listed in their tie order). Ids without data are skipped."""
    among = tuple(among)
    cand = [c for c in among if c in delays and len(delays[c])]
    if not cand:
        raise ValueError("no candidate with data")
    return min(cand, key=lambda c: (float(np.median(np.asarray(delays[c], float))), among.index(c)))


def argmin_tie(values: dict, among) -> str:
    """The id of `among` with the lowest scalar values[id]; ties to the earlier one in `among`."""
    among = tuple(among)
    cand = [c for c in among if c in values]
    if not cand:
        raise ValueError("no candidate with data")
    return min(cand, key=lambda c: (float(values[c]), among.index(c)))


def grid_edges(cid: str) -> list:
    """Grid dimensions on which a chosen controller (or action) sits at an edge (page §2: report only)."""
    if cid.endswith(BACK):
        cid = parse_action(cid)[0]
    p = parse(cid)
    if p[0] == "const":
        return [f"rate={int(p[1])}"] if p[1] in (RATES[0], RATES[-1]) else []
    if p[0] == "fb":
        out = [f"K_F={int(p[1])}"] if p[1] in (KF_GRID[0], KF_GRID[-1]) else []
        return out + ([f"n_crit={int(p[2])}"] if p[2] in (NCRIT_GRID[0], NCRIT_GRID[-1]) else [])
    if p[0] == "pi":
        e = "e4" if p[4] == "4" else "e5"
        out = [f"K_P={int(p[1])}"] if p[1] in (KP_GRID[0], KP_GRID[-1]) else []
        out += [f"K_I={int(p[2])}"] if p[2] in (KI_GRID[0], KI_GRID[-1]) else []
        return out + ([f"n_crit_{e}={int(p[3])}"] if p[3] in (PI_NCRIT[e][0], PI_NCRIT[e][-1]) else [])
    return [f"eta={p[1]:g}"] if p[1] in (ETA_GRID[0], ETA_GRID[-1]) else []
