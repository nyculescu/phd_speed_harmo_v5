"""IP's tuning runner-up per cell (descriptive): main-run evaluation of the second-best tuning action, vs ID and vs
each L0 arm (S1 level, page draws). Shows how much S1b / 'IP vs L0' depend on a near-tie in the IP choice.
Usage: ip_alt.py recs.pkl mine_page.json"""
import json, pickle, sys
import numpy as np
recs = pickle.load(open(sys.argv[1], "rb"))
M = json.load(open(sys.argv[2]))
IX = {(r["pre"], r["post"], bool(r["back"]), r["incident"], float(r["q"]), int(r["seed"])): r["delay_s"] for r in recs
      if 7400600 <= r["seed"] <= 7400699 and r["k"] == 0 and not r["rs"] and not r["d"] and not r["c"] and not r["fa"]}
B, L = 20_000, 1 - 0.05 / 8
I = np.random.default_rng(20261019).integers(0, 100, size=(B, 100))
S = range(7400600, 7400700)


def paired(r, t):
    d = r - t
    bd, br = np.median(d[I], axis=1), np.median(r[I], axis=1)
    lo, hi = 50 * (1 - L), 50 * (1 + L)
    return (f"{100 * np.median(d) / np.median(r):+.1f} [{np.percentile(bd / br, lo) * 100:+.1f}, "
            f"{np.percentile(bd / br, hi) * 100:+.1f}] dlo {np.percentile(bd, lo):+.1f}")


for q in ("1600", "2000"):
    a = M["arms"][q]
    for inc in ("slow", "block"):
        alt = a["IP_top3_tuning"][inc][1][0]
        sw = lambda p: np.array([IX[(a["N"], p.replace("+back", ""), p.endswith("+back"), inc, float(q), s)] for s in S])
        fx = lambda g: np.array([IX[(g, None, False, inc, float(q), s)] for s in S])
        t = sw(alt)
        print(f"{inc}_q{q}: IP {a['IP'][inc]} runner-up {alt}: median {np.median(t):.1f}; vs ID {paired(sw(a['ID']), t)}; "
              + "; ".join(f"vs {x} {paired(fx(a[x]), t)}" for x in ("FB", "PI")))
