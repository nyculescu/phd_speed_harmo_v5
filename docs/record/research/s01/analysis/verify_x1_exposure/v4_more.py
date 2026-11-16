"""Follow-ups: 4a/edge-3 severity by road, approach-exposure validity within nc, Kitagawa with approach exposure on 3 and 4a,
F5 4a numbers, F6 braking events, F7 per-seed correlation and its shuffled-nc null, within-arm rho."""
import json
import sys

import numpy as np

sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure")
from vlib import D, arms_for, effect, fmt, g, load, mean_ci  # noqa: E402

OUT = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure"
ST = json.load(open(f"{OUT}/v2_st.json"))["store"]
SUM = json.load(open(f"{D}/summary_rows_test.json"))
T = load()
seeds = list(range(7440840, 7440880))


def av(cell, arm, fn):
    return np.array([np.mean([fn(ST[f"{cell}|{n}|{s}"], T[f"{cell}|{n}"][s], SUM[f"{cell}|{n}|5300"][str(s)]) for n in arms_for(cell)[arm]]) for s in seeds])


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


for cell in ("X1", "X2"):
    print(f"\n===== {cell}")
    # severity and short thresholds by road (keys exist only where the counter fired)
    for arm in ("v3w", "tail", "sw", "inc"):
        out = []
        for k in ("sev3_r_4a", "sev3_r_rest", "sev3_r_ramp2", "sev3_s_hi", "sev3_s_mid", "ttc2_r_4a", "ttc15_r_4a", "ttc2_r_3", "ttc15_r_3", "ttc3_r_4a", "ttc3_r_3"):
            p = av(cell, arm, lambda st, r, sm, k=k: g(r, k))
            o = av(cell, "nc", lambda st, r, sm, k=k: g(r, k))
            out.append(f"{k} {fmt(mean_ci(p - o))} (nc med {np.median(o):.0f})")
        sev3_r3 = av(cell, arm, lambda st, r, sm: g(r, "sev3") - g(r, "sev3_r_4a") - g(r, "sev3_r_rest") - g(r, "sev3_r_ramp2"))
        sev3_r3o = av(cell, "nc", lambda st, r, sm: g(r, "sev3") - g(r, "sev3_r_4a") - g(r, "sev3_r_rest") - g(r, "sev3_r_ramp2"))
        out.append(f"sev3_r_3 (by subtraction) {fmt(mean_ci(sev3_r3 - sev3_r3o))} (nc med {np.median(sev3_r3o):.0f})")
        print(f"  {arm}: " + "; ".join(out))
    # validity of approach exposure: within nc, across seeds
    for e in ("4a", "3"):
        a = av(cell, "nc", lambda st, r, sm, e=e: st[f"app20_{e}"])
        t = av(cell, "nc", lambda st, r, sm, e=e: g(r, f"ttc3_r_{e}"))
        j = av(cell, "nc", lambda st, r, sm, e=e: st[f"vs_{e}_0"] + st[f"vs_{e}_18"])
        m = av(cell, "nc", lambda st, r, sm, e=e: st[f"vs_{e}"] - st[f"vs_{e}_0"])
        print(f"  nc within-arm Spearman ttc3_r_{e} vs app20_{e} {spearman(t, a):+.2f}; vs jam_{e} {spearman(t, j):+.2f}; vs moving veh-s {spearman(t, m):+.2f}")
    # Kitagawa on 3 and 4a with app20 as exposure (single-stratum decomposition per edge)
    for arm in ("v3w", "tail", "sw", "inc", "3e", "p333"):
        res = []
        for e in ("4a", "3"):
            rp_, ep_, tot = [], [], []
            for s in seeds:
                o = T[f"{cell}|nc"][s]
                eo = ST[f"{cell}|nc|{s}"][f"app20_{e}"]
                ro = g(o, f"ttc3_r_{e}") / max(eo, 1.0)
                acc = [0.0, 0.0, 0.0]
                for n in arms_for(cell)[arm]:
                    p = T[f"{cell}|{n}"][s]
                    ep = ST[f"{cell}|{n}|{s}"][f"app20_{e}"]
                    rp = g(p, f"ttc3_r_{e}") / max(ep, 1.0)
                    acc[0] += (rp - ro) * (ep + eo) / 2
                    acc[1] += (ep - eo) * (rp + ro) / 2
                    acc[2] += g(p, f"ttc3_r_{e}") - g(o, f"ttc3_r_{e}")
                k = len(arms_for(cell)[arm])
                rp_.append(acc[0] / k); ep_.append(acc[1] / k); tot.append(acc[2] / k)
            res.append(f"{e}: total {fmt(mean_ci(tot))} = rate {fmt(mean_ci(rp_))} + approach-exposure {fmt(mean_ci(ep_))}")
        print(f"  Kitagawa(app20) {arm}: " + " | ".join(res))
    # F5: 4a moving veh-s and rates per veh-s
    for arm in ("v3w",):
        mov = lambda st, r, sm: st["vs_4a"] - st["vs_4a_0"]
        print(f"  F5 {arm}: 4a moving(>=18 km/h) veh-s % {fmt(effect(av(cell, arm, mov), av(cell, 'nc', mov), 1), 2)}; "
              f"ttc3_r_4a/vs_4a {fmt(effect(av(cell, arm, lambda st, r, sm: g(r, 'ttc3_r_4a') / st['vs_4a']), av(cell, 'nc', lambda st, r, sm: g(r, 'ttc3_r_4a') / st['vs_4a']), -1))}; "
              f"per moving {fmt(effect(av(cell, arm, lambda st, r, sm: g(r, 'ttc3_r_4a') / (st['vs_4a'] - st['vs_4a_0'])), av(cell, 'nc', lambda st, r, sm: g(r, 'ttc3_r_4a') / (st['vs_4a'] - st['vs_4a_0'])), -1))}; "
              f"edge 3 per moving {fmt(effect(av(cell, arm, lambda st, r, sm: g(r, 'ttc3_r_3') / (st['vs_3'] - st['vs_3_0'])), av(cell, 'nc', lambda st, r, sm: g(r, 'ttc3_r_3') / (st['vs_3'] - st['vs_3_0'])), -1))}")
    # F6 braking events (summary events_ge45, all classes)
    ev = lambda st, r, sm: sum(sm[f"events_ge45_{c}"] for c in ("car", "alks", "truck"))
    for arm in ("v3w", "3e"):
        p, o = av(cell, arm, ev), av(cell, "nc", ev)
        print(f"  F6 {arm} events_ge45 effect {fmt(effect(p, o, -1))}; medians arm {np.median(p):.0f} nc {np.median(o):.0f}")
    # F7 per-seed relation and shuffled-nc null
    jam = lambda st, r, sm: sm["waves.jam_share"] if "waves.jam_share" in sm else sm["waves"]["jam_share"]
    tt = lambda st, r, sm: g(r, "ttc3")
    P_t, O_t, P_j, O_j = av(cell, "v3w", tt), av(cell, "nc", tt), av(cell, "v3w", jam), av(cell, "nc", jam)
    rho = spearman(P_t - O_t, P_j - O_j)
    rng = np.random.default_rng(1)
    null = []
    for _ in range(5000):
        pi = rng.permutation(40)
        null.append(spearman(P_t - O_t[pi], P_j - O_j[pi]))
    print(f"  F7 rho(d ttc3, d jam_share) {rho:+.3f}; shuffled-nc null median {np.median(null):+.3f} [{np.percentile(null, 2.5):+.3f}, {np.percentile(null, 97.5):+.3f}]; within-arm rho ttc3 vs jam: nc {spearman(O_t, O_j):+.2f}, v3w {spearman(P_t, P_j):+.2f}")
    # within-nc confound check: does nc's ttc3 track demand-related volume (vs) as much as jam?
    vsn = av(cell, "nc", lambda st, r, sm: r["vs"])
    psd = av(cell, "nc", lambda st, r, sm: r["passed"])
    print(f"  within-nc rho ttc3 vs vs {spearman(O_t, vsn):+.2f}; vs passed {spearman(O_t, psd):+.2f}; jam vs vs {spearman(O_j, vsn):+.2f}")

for cell in ("X1", "X2"):
    jam4a = lambda st, r, sm: st["vs_4a_0"] + st["vs_4a_18"]
    p, o = av(cell, "v3w", jam4a), av(cell, "nc", jam4a)
    print(f"{cell} v3w jam(<30 km/h) on 4a: effect % (positive = less jam) {fmt(effect(p, o, -1))}; medians {np.median(p):,.0f} vs {np.median(o):,.0f}")
