"""Run counts, time and cost of Plan B v0 (planning). Rates: rental A 2,450-3,050 runs/h measured (V475), $0.10-0.13 per
1,000 runs; rental B about 6,400 runs/h derived from V461's search timing; laptop 1,330 runs/h by day (V425-V426)."""
CELLS, SEEDS_GATE, OPP_CARRIED, REPICK, LEARN = 3, 40, 15, 8, 5


def stages(G, n=120, cells_cma=3):
    s = {}
    s["S1 smoke, identity, T3"] = 100
    rung1 = CELLS * 3 * SEEDS_GATE + 3 * SEEDS_GATE + 2 * SEEDS_GATE + 20   # nc, p333, 3E-T per cell; S; placebo; traces
    rung2 = CELLS * 3 * SEEDS_GATE + CELLS * 0 + 3 * SEEDS_GATE              # at most: every cell's rung 2 and S on those seeds
    s["S2 gates (both rungs at most)"] = rung1 + rung2
    s["S3a grid re-pick"] = 69 * 20 * (CELLS + 1) + 2 * 20
    s["S3b pilot"] = CELLS * (OPP_CARRIED + REPICK + 1 + LEARN + 1) * 30
    checks = (G - 20) // 10 + 1
    s["S4a 3E searches"] = cells_cma * 2 * (384 * G + 240 * checks) + cells_cma * 80
    s["S4b ASCH"] = 72 * (CELLS + 1) * 20 + 5 * (CELLS + 1) * 20
    s["S4c MPC-F"] = 40 * (CELLS + 1) * 2 + 30 * (CELLS + 1) * 7
    s["S5 smoke, pick replays"] = 300
    per_cell = OPP_CARRIED + REPICK + 1 + 2 + 2 + LEARN + 1
    steady = OPP_CARRIED + CELLS * REPICK + 1 + 2 * CELLS + 2 + LEARN + 1
    s["S6 evaluation"] = n * (CELLS * per_cell + steady)
    return s


for G in (40, 100):
    s = stages(G)
    tot = sum(s.values())
    srch = s["S4a 3E searches"]
    rest = tot - srch
    print(f"G={G}")
    for k, v in s.items():
        print(f"  {k}: {v}")
    print(f"  total {tot}, searches {100 * srch / tot:.0f} %")
    print(f"  all on rental A: {tot / 3050:.0f}-{tot / 2450:.0f} h, ${tot * 0.10 / 1000:.1f}-{tot * 0.13 / 1000:.1f}")
    print(f"  searches on rental B: {srch / 6400:.0f} h; rest on rental A: {rest / 3050:.1f}-{rest / 2450:.1f} h")
print("S6 at n=80:", stages(40, n=80)["S6 evaluation"], "runs")
pk = stages(40)
print("stop at pilot:", sum(v for k, v in pk.items() if k[:3] in ("S1 ", "S2 ", "S3a", "S3b")))
