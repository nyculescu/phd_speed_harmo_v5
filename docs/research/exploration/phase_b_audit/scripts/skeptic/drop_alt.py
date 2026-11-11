"""EXPLORATORY skeptic check of plant_choice.md section B: alternative breakdown definitions and the power of the before/after test.
Stored S6 extract (floor/comp.pkl), cell S, 5,300 veh/h, 240 seeds. Runs are the bootstrap unit; 95 % percentile, 10,000 resamples, RNG 20261110."""
import pickle
import numpy as np
T = pickle.load(open('/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/floor/comp.pkl', 'rb'))
seeds = list(range(7480400, 7480640))
NB = 10_000
def boot_med(x, rng):
    x = np.asarray(x, float)
    if len(x) < 5:
        return f"n={len(x)} (<5)"
    b = np.median(x[rng.integers(0, len(x), (NB, len(x)))], axis=1)
    return "%+.1f [%+.1f, %+.1f] n=%d" % (np.median(x), *np.percentile(b, (2.5, 97.5)), len(x))
def load(cell, arm):
    g = lambda k: np.array([T[(cell, arm)][s]["minute"][k] for s in seeds], float)
    q = g("m2_out") * 60.0
    qin = (g("m2_main_in") + g("m2_ramp_in")) * 60.0
    sp = lambda p: np.where(g(p + "_n") > 0, 3.6 * g(p + "_vs") / np.maximum(g(p + "_n"), 1), np.nan)
    return q, qin, sp("m2_acc"), sp("m2_up"), g("m2_acc_n") / 60.0
def first_run(mask, k):
    return next((i for i in range(len(mask) - k + 1) if mask[i:i + k].all()), None)
DEFS = {"A report: 4a < 60 km/h, 2 min": lambda va, vu: ((va < 60), 2),
        "B strict: 4a < 50 km/h, 3 min": lambda va, vu: ((va < 50), 3),
        "C spillback: upstream of merge 2 < 60 km/h, 2 min": lambda va, vu: ((vu < 60), 2),
        "D deep: 4a < 40 km/h, 2 min": lambda va, vu: ((va < 40), 2)}
for cell in ("S",):
    for arm in ("nc", "p333"):
        q, qin, va, vu, n4a = load(cell, arm)
        nm = q.shape[1]
        print(f"\n##### {cell} {arm}: mean out-flow {q.mean():.0f}, mean in-flow {qin.mean():.0f} veh/h; 4a speed median {np.nanmedian(va):.0f}, upstream speed median {np.nanmedian(vu):.0f} km/h; vehicles on 4a first 5 min {n4a[:, :5].mean():.1f}, last 5 min {n4a[:, -5:].mean():.1f}")
        for name, fn in DEFS.items():
            rng = np.random.default_rng(20261110)
            slow, k = fn(np.nan_to_num(va, nan=999.0), np.nan_to_num(vu, nan=999.0))
            B = [first_run(s, k) for s in slow]
            real = [(i, b) for i, b in enumerate(B) if b is not None and 5 <= b and b + 6 <= nm]
            L = [100 * (q[i, b - 5:b].mean() - q[i, b + 1:b + 6].mean()) / q[i, b - 5:b].mean() for i, b in real]
            # placebo: 11 minutes with no slow minute under the same definition
            pl = np.array([(i, b, q[i, b - 5:b].mean(), q[i, b + 1:b + 6].mean()) for i in range(len(seeds)) for b in range(5, nm - 5) if not slow[i, b - 5:b + 6].any()])
            ex = []
            if len(pl):
                dpl = 100 * (pl[:, 2] - pl[:, 3]) / pl[:, 2]
                for (i, b), l in zip(real, L):
                    m = np.abs(pl[:, 2] - q[i, b - 5:b].mean()) <= 60.0
                    if m.sum() >= 5:
                        ex.append(l - dpl[m].mean())
            # is the post-onset flow arrival-limited? out minus in over the 5 post minutes, and the queue on 4a
            st = [q[i, b + 1:b + 6].mean() - qin[i, b + 1:b + 6].mean() for i, b in real]
            post = [q[i, b + 1:b + 6].mean() for i, b in real]; pre = [q[i, b - 5:b].mean() for i, b in real]
            print(f" {name}: runs with onset {sum(b is not None for b in B)}, usable (onset minute 5-19) {len(real)}, placebo windows {len(pl)} in {len(set(pl[:, 0])) if len(pl) else 0} runs")
            print(f"    before minus after, %: {boot_med(L, rng)} | minus matched placebo: {boot_med(ex, rng)}")
            if real:
                print(f"    pre flow median {np.median(pre):.0f}, post flow median {np.median(post):.0f} veh/h; post out minus in, veh/h: {boot_med(st, rng)}")
        # power: how large a discharge loss could the p333 test see? post flow against the saturated throughput quoted in an_delay_floor.md:43
        sat = {"nc": 5342.0, "p333": 5544.0}[arm]
        print(f" demand 5,300 against saturated throughput {sat:.0f} veh/h (an_delay_floor.md:43, 6 seeds at 7,000): demand is {100 * 5300 / sat:.1f} % of it;"
              f" a discharge capacity cut by up to {100 * (1 - 5300 / sat):.1f} % would still pass the whole demand, so the before/after flow test cannot see it")
        # free 5-min flows above the saturated throughput (max-type evidence, biased upward; shown with its share only)
        rng = np.random.default_rng(20261110)
        slowA = np.nan_to_num(va, nan=999.0) < 60
        free5 = np.array([q[i, j:j + 5].mean() for i in range(len(seeds)) for j in range(nm - 4) if not slowA[i, j:j + 5].any()])
        if len(free5):
            print(f" free 5-min windows (no minute of 4a below 60 km/h): {len(free5)}; flow median {np.median(free5):.0f}, p95 {np.percentile(free5, 95):.0f}, max {free5.max():.0f} veh/h; share above the saturated throughput {100 * np.mean(free5 > sat):.1f} %")
