"""Independent sign check: direction of res vs incumbent (validation X1) and v3w vs incumbent (test T1 X1). Aggregates only."""
import json, statistics as st
from collections import defaultdict
OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
def load(f):
    T = defaultdict(dict)
    for line in open(f):
        r = json.loads(line)
        T[r["name"]][r["seed"]] = r
    return T
def g(r, k):
    v = r.get(k); return 0.0 if v is None else float(v)
def arm(T, names):
    seeds = sorted(set.intersection(*(set(T[n]) for n in names)))
    return {s: {k: sum(g(T[n][s], k) for n in names) / len(names) for k in ("all_delay", "ttc_net")} for s in seeds}
def cmp(A, B, k, label):
    ds = sorted(set(A) & set(B))
    mA, mB = st.median(A[s][k] for s in ds), st.median(B[s][k] for s in ds)
    pd = st.median(A[s][k] - B[s][k] for s in ds)
    nless = sum(A[s][k] < B[s][k] for s in ds)
    print(f"{label} {k}: median A {mA:.1f}, median B {mB:.1f}, paired median(A-B)/medB = {100*pd/mB:+.2f} %, seeds A<B {nless}/{len(ds)}")
V = load(f"{OUT}/val/validation.jsonl")
val = json.load(open(f"{OUT}/val/validation.json"))
ch, inc = val["chosen"]["res"], val["incumbent_chosen"]
for c in ("X1", "X2"):
    R = arm(V, [f"{c}|r{i}u{ch[str(i)] if str(i) in ch else ch[i]}" for i in range(5)])
    I = arm(V, [f"{c}|d{i}u{inc[str(i)] if str(i) in inc else inc[i]}" for i in range(5)])
    cmp(R, I, "all_delay", f"val {c} res vs incumbent")
    O = {s: {k: g(r, k) for k in ("all_delay", "ttc_net")} for s, r in V[f"{c}|os1_15_10"].items()}
    cmp(R, O, "ttc_net", f"val {c} res vs os1_15_10")
    ch2 = val["chosen"]["attr"]
    Aa = arm(V, [f"{c}|a{i}u{ch2[str(i)] if str(i) in ch2 else ch2[i]}" for i in range(5)])
    cmp(Aa, O, "ttc_net", f"val {c} attr vs os1_15_10")
Tt = load(f"{OUT}/test/test.jsonl")
for c in ("X1", "X2"):
    W = arm(Tt, [f"{c}|w{i}" for i in range(5)]); I = arm(Tt, [f"{c}|d{i}" for i in range(5)])
    cmp(W, I, "all_delay", f"test {c} v3w vs incumbent"); cmp(W, I, "ttc_net", f"test {c} v3w vs incumbent")
