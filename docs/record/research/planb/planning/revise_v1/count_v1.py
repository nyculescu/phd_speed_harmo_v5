"""Run counts, time and cost of Plan B v1 (planning). Rental 2,600-3,050 runs/h (V475, 59 workers; a 100-worker rental is
assumed to give about the same per-run cost), $0.10-0.13 per 1,000 runs (V475), 6 % setup; laptop 1,330 runs/h by day."""
SEEDS_GATE, CARRIED, REPICK, LEARN, G = 40, 15, 8, 5, 100


def stages(C, n, workzone=False):
    K = C + 1  # conditions: the cells and S
    s = {}
    s["S1 smoke, identity (C1, C1b), T3"] = 100 + 30 + (4 if workzone else 0)
    s["S2 gates (one rung)"] = C * 3 * SEEDS_GATE + 3 * SEEDS_GATE + 2 * SEEDS_GATE + 20
    s["S3a grid re-pick"] = 69 * 20 * K + K * 20
    checks = (G - 20) // 10 + 1
    s["S4a 3E-C and 3E-D to 100 generations"] = C * 2 * (384 * G + 240 * checks) + C * 80
    cfg = 3 * 3 * 2 * (1 + C) + 1
    s["S4b ASCH"] = cfg * K * 20 + 5 * K * 20 + K * 40
    acts = 3 + C
    s["S4c MPC-F"] = 40 * 4 * K + acts * 40 * K + 30 * K * (1 + acts)
    s["S5 smoke, pick replays"] = 300
    per_cell = CARRIED + REPICK + 1 + 2 + 2 + LEARN + 1
    steady = CARRIED + C * REPICK + 1 + 2 * C + 2 + LEARN + 1
    s["S6 evaluation"] = n * (C * per_cell + steady)
    return s


for C, wz in ((2, False), (3, True)):
    for n in (120, 240):
        s = stages(C, n, wz)
        tot = sum(s.values())
        lap = s["S1 smoke, identity (C1, C1b), T3"] + s["S2 gates (one rung)"]
        rent = tot - lap
        srch = s["S4a 3E-C and 3E-D to 100 generations"]
        s56 = s["S5 smoke, pick replays"] + s["S6 evaluation"]
        print(f"cells={C} n={n}: " + ", ".join(f"{k}: {v}" for k, v in s.items()))
        print(f"  total {tot}; laptop {lap} ({lap / 1330:.1f} h); rented {rent}; searches {100 * srch / tot:.0f} %; S5+S6 {s56}")
        print(f"  rented time {rent / 3050 * 1.06:.0f}-{rent / 2600 * 1.06:.0f} h incl. 6 % setup; cost ${rent * 0.10 / 1000:.1f}-{rent * 0.13 / 1000:.1f} "
              f"(+6 %: ${rent * 0.10 / 1000 * 1.06:.1f}-{rent * 0.13 / 1000 * 1.06:.1f}); S5+S6 ${s56 * 0.10 / 1000 * 1.06:.1f}-{s56 * 0.13 / 1000 * 1.06:.1f}")
        print(f"  one futile cell's two searches: {2 * (384 * G + 240 * 9) + 80} runs, ${(2 * (384 * G + 240 * 9) + 80) * 0.10 / 1000:.1f}-{(2 * (384 * G + 240 * 9) + 80) * 0.13 / 1000:.1f}")
