from lib import *
import re, json, pickle
from a2 import DS, T, Q
pol = re.compile(r"^[a-z]\d(u\d+)?$")
print("rule vs p333 delay, pooled sets (positive = rule has less delay than p333)")
for c in ("X1", "X2"):
    out = []
    for r in sorted({n.split("|")[1] for s in T for (n, q) in T[s] if n.startswith(c + "|") and not pol.match(n.split("|")[1])}):
        if r in ("p333", "nc"): continue
        A, B = {}, {}
        for s in T:
            if (f"{c}|{r}", Q) in T[s]:
                A |= T[s][(f"{c}|{r}", Q)]; B |= T[s][(f"{c}|p333", Q)]
        e = eff(A, B); out.append((e[0], f"{r} {e[0]:+.1f} [{e[1]:+.1f}, {e[2]:+.1f}] n={e[3]}"))
    print(c, "; ".join(x[1] for x in sorted(out, reverse=True)))
for c in ("x1", "x2"):
    fj = json.load(open(RUNS + f"round2/cma3e_{c}/final.json"))
    print(c, "candidate keys", [k for k in fj["candidates"][0] if k not in ("params", "x")])
    for cand in fj["candidates"]:
        print("  ", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in cand.items() if k not in ("params", "x", "per_level")}, json.dumps(cand.get("per_level"))[:300])
    bj = json.load(open(RUNS + f"round2/cma3e_{c}/best.json"))
    print("  best.json:", {k: (v if not isinstance(v, (list, dict)) else "...") for k, v in bj.items()}, "history len", len(bj["history"]), "last hist", json.dumps(bj["history"][-1])[:300])
# route shares
res = pickle.load(open("b1.pkl", "rb"))
S = load(FILES["s01test"])
for c in ("X1", "X2"):
    r = S[(f"{c}|p333", Q)]
    n2 = np.mean([sum(x["m_minute"]["m2_ramp_in"]) for x in r.values()]); n1 = np.mean([sum(x["m_minute"]["m1_ramp_in"]) for x in r.values()]); m2 = np.mean([sum(x["m_minute"]["m2_main_in"]) for x in r.values()])
    print(c, "p333 mean vehicles entering 4a from ramp 2:", round(n2), "from road 3:", round(m2), "entering 3a from ramp 1:", round(n1), "passed", np.mean([x["passed"] for x in r.values()]))
