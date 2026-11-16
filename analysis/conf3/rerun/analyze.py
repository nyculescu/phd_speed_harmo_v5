"""V398: report-only analysis of the X2 replays. The statistic is the protocol's: median of paired differences over the reference's median, in %,
positive = the policy has fewer; 97.5 % percentile bootstrap, 20,000 resamples. usage: analyze.py base.jsonl long.jsonl"""
import json
import sys

import numpy as np

POL = ["d0", "d1", "d2", "d3", "d4"]
RULES = ["os1_15_10", "r4a1", "lr1000_16_2", "p333"]
HUMAN = ("hdv_car", "truck")


def load(f):
    T = {}
    for r in map(json.loads, open(f)):
        T.setdefault(r["name"].split("|")[1], {})[r["seed"]] = r
    return T


def eff(A, B, get):
    ds = sorted(set(A) & set(B))
    a, b = np.array([get(A[s]) for s in ds], float), np.array([get(B[s]) for s in ds], float)
    ref = max(np.median(b), 1e-9)
    d = (b - a) / ref * 100
    rng = np.random.default_rng(20261104)
    boot = np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1)
    lo, hi = np.percentile(boot, (1.25, 98.75))
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(A, get):
    return round(float(np.median([get(r) for r in A.values()])), 1)


def X(k, late=False):
    return lambda r: r["extra"].get(k, 0.0) + (r["extra"].get("late_" + k, 0.0) if late else 0.0)


CLS = ("alks", "hdv_car", "truck")     # followers; "ttc_other_<cls>" is the zone key for roads outside 3 and merge 2, not a follower class


def fol(classes, leaders=None, late=False):
    """TTC seconds by follower class (and leader class), from the pair keys ttc_<follower>_<leader>; class names hold underscores, so keys are matched exactly."""
    def g(r):
        e, tot = r["extra"], 0.0
        for f in CLS:
            for l in CLS + ("other",):
                if f in classes and (leaders is None or l in leaders):
                    tot += e.get(f"ttc_{f}_{l}", 0.0) + (e.get(f"late_ttc_{f}_{l}", 0.0) if late else 0.0)
        return tot
    return g


def show(title, T, get, refs=RULES + ["nc"], pols=POL):
    print(f"\n{title}")
    print("  medians: " + ", ".join(f"{a} {med(T[a], get)}" for a in pols + refs))
    for ref in refs:
        print(f"  vs {ref}: " + "; ".join(f"{p} {eff(T[p], T[ref], get)}" for p in pols))


if __name__ == "__main__":
    B, L = load(sys.argv[1]), load(sys.argv[2])
    off = [(a, s) for a in B for s, r in B[a].items() if fol(CLS)(r) != r["ttc_net"]]
    print("class pairs add up to the deciding count in", sum(len(v) for v in B.values()) - len(off), "of", sum(len(v) for v in B.values()), "runs", off[:3])
    show("A. Deciding count (ttc_net), base replays", B, lambda r: r["ttc_net"])
    show("B. TTC below 3 s on 4a_0, the accelerating lane of merge 2", B, X("ttc_4a0"))
    show("C. ...of which in its last 50 m", B, X("ttc_4a0_end50"))
    show("D. TTC below 3 s on the 4a mainline lanes", B, X("ttc_4a_main"))
    show("E. Everything except 4a_0", B, lambda r: r["ttc_net"] - X("ttc_4a0")(r))
    show("F. Followers at 5 m/s or faster", B, X("ttc_fast"))
    show("G. ALKS followers", B, fol(("alks",)))
    show("H. Human and truck followers, all leaders", B, fol(HUMAN))
    show("I. Human/truck behind an ALKS (reward charges the ALKS at half weight)", B, fol(HUMAN, ("alks",)))
    show("J. Human/truck behind human/truck (no reward term)", B, fol(HUMAN, HUMAN))
    for z in ("m2", "r3", "other"):
        show(f"K. Human/truck followers in zone {z}", B, X(f"ttc_{z}_hdv_car"))
    print("\nL. Share of TTC seconds with an ALKS follower (medians): " + ", ".join(f"{a} {round(float(np.median([fol(('alks',))(r) / max(r['ttc_net'], 1) for r in B[a].values()])), 3)}" for a in POL + RULES + ["nc"]))
    print("\nM. Long runs: snapshot at 1,800 s against the stored deciding count")
    same = sum(L[a][s]["snap"].get("E30") == B[a][s]["ttc_net"] for a in L for s in L[a] if s in B.get(a, {}))
    print(f"  identical up to 1,800 s in {same} of {sum(len(v) for v in L.values())} runs")
    show("N. Long: TTC below 3 s in 1,800-3,000 s", L, lambda r: r["extra"].get("late_ttc_all", 0.0))
    show("O. Long: TTC below 3 s, whole 300-3,000 s", L, lambda r: r["extra"].get("ttc_all", 0.0) + r["extra"].get("late_ttc_all", 0.0))
    show("P. Long: all-vehicle delay, vehicle-seconds, whole run", L, lambda r: r["all_delay"])
    show("Q. Long: vehicles into road 4, whole run (negative = policy passes more)", L, lambda r: r["passed"])
    show("R. Long: vehicle-seconds in system 1,800-3,000 s", L, lambda r: r["N"] - r["snap"]["N"])
    print("\nS. Long: backlog at 1,800 s (live + pending vehicles), and flow per minute in the last 10 minutes (medians)")
    for a in POL + RULES + ["nc"]:
        bl = np.median([r["snap"]["live"] + r["snap"]["pending"] for r in L[a].values()])
        tail = np.median([np.mean(r["flow_min"][-10:]) for r in L[a].values()])
        print(f"  {a}: backlog {bl:.0f}, last 10 min {tail:.1f} veh/min")
