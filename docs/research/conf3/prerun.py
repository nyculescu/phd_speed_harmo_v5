"""Pre-run gates on seeds 7,440,065-074, fixed in the protocol. usage: prerun.py out_dir workers stored_policy.pt. Exit 1: a gate failed, it goes to the author."""
import sys
from pathlib import Path

from common import Q, SEEDS_CHECK, cfg, effect, load, med, val
from v5b.fleet import plant_sweep as ps

ARMS = {"nc": {}, "p333": {"cav_rule": [3, 3, 3]}, "dup333": {"pattern": [3, 3, 3, 3, 3]}, "r4a1": {"road_levels": {"4a": 1}}, "lr1000_10": {"local_rule": {"r": 1000, "th": 10}},
        "z31333": {"pattern": [3, 1, 3, 3, 3]}, "a4": {"adaptive_4a": {"r": 1000, "th": 10, "level": 1, "road_level": 1}}, "os": {"own_state": {"level": 1, "th": 10, "crowd": 0}}}

def ps_row_differs(a: dict, b: dict) -> bool:
    return any(a.get(k) != b.get(k) for k in ("passed", "delay", "ttc_net", "N", "b3_step"))


if __name__ == "__main__":
    out, w, pol = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    c = {f"{x}|{n}": cfg(k, x) for x in ("S", "X1", "X2") for n, k in {**ARMS, "policy": {"pt": pol}}.items()}
    ps.matrix(c, (Q,), SEEDS_CHECK, out / "prerun.jsonl", w, str(out / "rd"))
    T = load(out / "prerun.jsonl")
    bad = []
    for x in ("S", "X1", "X2"):
        nc = T[(f"{x}|nc", Q)]
        print(f"== {x}; no control delay {med(nc, 'delay'):.1f}, all-vehicle {med(nc, 'all_delay'):.0f}, flow {med(nc, 'passed'):.0f}, TTC {med(nc, 'ttc_net'):.0f}, moving events {med(nc, 'alks_full_moving'):.1f}", flush=True)
        for n in (*ARMS, "policy"):
            A = T[(f"{x}|{n}", Q)]
            b, s, t, h = med(A, "brake_net"), max(med(A, "b3_step"), 1.0), med(A, "ttc_net"), max(med(A, "ttc_half"), 1.0)
            ev, em = med(A, "alks_full_moving"), max(val(r, "tau_mismatch") for r in A.values())
            share = sum(val(r, "tau_on_match") for r in A.values()) / max(sum(val(r, "tau_on_n") for r in A.values()), 1.0)
            print(f" {n}: delay {med(A, 'delay'):.1f}, flow {med(A, 'passed'):.0f}, TTC {t:.0f}, 1-Hz/step {b / s:.3f}, TTC whole/half {t / h:.3f}, moving events {ev:.1f}, creep {med(A, 'alks_full_creep'):.1f}, b7 step {med(A, 'b7_step'):.1f}, tau mismatch {em:.0f}, on-level share {share:.3f}, collisions {sum(val(r, 'collisions') for r in A.values()):.0f}", flush=True)
            if n == "policy":
                continue     # a trace-only arm: trained on P0
            if abs(b / s - 1.0) > 0.05:
                bad.append((x, n, "1-Hz against step braking", round(b / s, 3)))
            if h > 50 and abs(t / h - 1.0) > 0.05:
                bad.append((x, n, "TTC whole against half second", round(t / h, 3)))
            if ev > med(nc, "alks_full_moving") + 5:
                bad.append((x, n, "moving full-emergency events", ev))
            if em > 0:
                bad.append((x, n, "tau differs from the commanded value", em))
        if T[(f"{x}|p333", Q)] and any(ps_row_differs(T[(f"{x}|p333", Q)][k], T[(f"{x}|dup333", Q)][k]) for k in SEEDS_CHECK):
            bad.append((x, "duplicate rules differ"))
        print(f" T1, T2 report, against no control: p333 delay {effect(T[(f'{x}|p333', Q)], nc, 'delay', pct=(2.5, 97.5))}, flow {effect(T[(f'{x}|p333', Q)], nc, 'passed', 1, pct=(2.5, 97.5))}", flush=True)
    print("GATES FAILED" if bad else "gates pass", bad, flush=True)
    sys.exit(1 if bad else 0)
