"""EXPLORATORY: flow out of merge 2 before and after breakdown, S6 rows, with placebo nulls. Read-only on stored extracts."""
import pickle
import numpy as np
T = pickle.load(open('/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/floor/comp.pkl', 'rb'))
seeds = list(range(7480400, 7480640))
RNG = np.random.default_rng(20261110)
NB = 10_000

def boot_med(x):
    x = np.asarray(x, float)
    if len(x) < 5:
        return "n<5"
    idx = RNG.integers(0, len(x), (NB, len(x)))
    b = np.median(x[idx], axis=1)
    return "%+.1f [%+.1f, %+.1f] n=%d" % (np.median(x), *np.percentile(b, (2.5, 97.5)), len(x))

def series(cell, arm, mg):
    q = np.array([T[(cell, arm)][s]["minute"][f"{mg}_out"] for s in seeds], float) * 60.0
    n = np.array([T[(cell, arm)][s]["minute"][f"{mg}_acc_n"] for s in seeds], float)
    vs = np.array([T[(cell, arm)][s]["minute"][f"{mg}_acc_vs"] for s in seeds], float)
    v = np.where(n > 0, 3.6 * vs / np.maximum(n, 1), np.nan)
    return q, (v < 60.0) & ~np.isnan(v)

def onset(slow):
    return next((i for i in range(len(slow) - 1) if slow[i:i + 2].all()), None)

def recovery(slow, b):
    return next((i for i in range(b + 2, len(slow) - 1) if not slow[i:i + 2].any()), None)

for cell in ("S", "TRUCK"):
    for arm in ("nc", "p333"):
        for mg in ("m2",):
            q, slow = series(cell, arm, mg)
            nm = q.shape[1]
            B = [onset(s) for s in slow]
            nbreak = sum(b is not None for b in B)
            print(f"\n##### {cell} {arm} {mg}: runs {len(B)}, with breakdown {nbreak}, onset minute quartiles "
                  f"{np.percentile([b for b in B if b is not None], (0, 25, 50, 75, 100)) if nbreak else None}; mean flow all minutes {q.mean():.0f} veh/h")
            # pack statistic: best 5-min mean before onset against mean discharge to recovery or end
            P, L, Ls, pre_l, post_l, pre_s = [], [], [], [], [], []
            real = []
            for i, b in enumerate(B):
                if b is None or b < 5:
                    continue
                r = recovery(slow[i], b)
                end = r if r is not None else nm
                pmax = max(q[i, j:j + 5].mean() for j in range(b - 4))
                dis = q[i, b:end].mean()
                P.append(100 * (pmax - dis) / pmax)
                if b + 6 <= nm:
                    pre = q[i, b - 5:b].mean(); post = q[i, b + 1:b + 6].mean()
                    L.append(100 * (pre - post) / pre); pre_l.append(pre); post_l.append(post)
                    sus = slow[i, b + 1:b + 6].sum() >= 4
                    real.append((i, b, pre, post, sus))
                    if sus:
                        Ls.append(100 * (pre - post) / pre); pre_s.append(pre)
            print(" pack statistic (max-5 before, mean after), %:", boot_med(P))
            print(" like-for-like (5 min before, 5 min after onset+1), %:", boot_med(L), "| pre median %.0f, post median %.0f veh/h" % (np.median(pre_l), np.median(post_l)) if L else "")
            print(" same, sustained only (4 of 5 post minutes slow), %:", boot_med(Ls), "| pre median %.0f" % np.median(pre_s) if Ls else "")
            # placebo windows: 11 consecutive minutes with no slow minute; same like-for-like statistic
            plc = []     # (run, b', pre, post)
            for i in range(len(seeds)):
                for b in range(5, nm - 5):
                    if not slow[i, b - 5:b + 6].any():
                        pre = q[i, b - 5:b].mean(); post = q[i, b + 1:b + 6].mean()
                        plc.append((i, b, pre, post))
            if not plc:
                print(" no placebo windows"); continue
            pl = np.array(plc)
            d_pl = 100 * (pl[:, 2] - pl[:, 3]) / pl[:, 2]
            runs_pl = len(set(pl[:, 0]))
            # one value per run (mean over its windows), so runs stay the resampling unit
            per_run = [d_pl[pl[:, 0] == i].mean() for i in sorted(set(pl[:, 0]))]
            print(f" placebo, all free windows ({len(pl)} windows in {runs_pl} runs), per-run mean, %:", boot_med(per_run), "| pre median %.0f" % np.median(pl[:, 2]))
            # burst-matched placebo: windows whose pre flow is within 60 veh/h of the real pre flow
            ex, ex_s, mp = [], [], []
            for (i, b, pre, post, sus) in real:
                m = np.abs(pl[:, 2] - pre) <= 60.0
                if m.sum() >= 5:
                    e = 100 * (pre - post) / pre - d_pl[m].mean()
                    ex.append(e); mp.append(d_pl[m].mean())
                    if sus:
                        ex_s.append(e)
            print(" matched placebo drop (pre flow within 60 veh/h), %: median", "%.1f" % np.median(mp) if mp else None, "| matched", len(ex), "of", len(real))
            print(" real minus matched placebo, %:", boot_med(ex))
            print(" same, sustained only, %:", boot_med(ex_s))
            # pack statistic under placebo: runs with no breakdown, pseudo-onset drawn from the real onsets
            free = [i for i, b in enumerate(B) if b is None]
            ob = [b for b in B if b is not None and b >= 5]
            if len(free) >= 5 and ob:
                Pn = []
                for i in free:
                    for b in ob[:40]:
                        pmax = max(q[i, j:j + 5].mean() for j in range(b - 4)); dis = q[i, b:].mean()
                        Pn.append((i, 100 * (pmax - dis) / pmax))
                Pn = np.array(Pn)
                per = [Pn[Pn[:, 0] == i, 1].mean() for i in free]
                print(f" pack statistic on {len(free)} runs with no breakdown, pseudo-onsets from the real ones, %:", boot_med(per))
            # discharge level: mean flow in slow minutes against free minutes
            print(" mean flow in slow minutes %.0f, in free minutes %.0f veh/h; share of slow minutes %.2f" % (q[slow].mean() if slow.any() else np.nan, q[~slow].mean(), slow.mean()))
