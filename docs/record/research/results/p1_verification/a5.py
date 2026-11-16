import pickle, sys, json, numpy as np
sys.path.insert(0, "/home/catalin/work/phd/p1_frozen_85f7d34")
from v5b.p1 import family as fam
R = pickle.load(open(sys.argv[1], "rb"))
ARMS = json.load(open("/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"))["tune"]["arms"]
EV = list(range(7400500, 7400600))
def fk(g, inc, q, s): return f"{g}_{inc}_q{q}_s{s}"
def sk(N, a, inc, q, s):
    g, back = fam.parse_action(a); return f"{N}-{g}" + ("+back" if back else "") + f"_{inc}_q{q}_s{s}"
rng = np.random.default_rng(7); IDX = rng.integers(0, 100, size=(20000, 100))
def rel(r, t, level=1 - 0.05 / 8):
    d = r - t; bd = np.median(d[IDX], axis=1)
    return round(100 * np.median(d) / np.median(r), 1), round(float(np.quantile(bd, (1 - level) / 2)), 1)
print("S1b sensitivity: IP vs alternative ID (rel %, CI-lo of median diff, S1 level); pass(a) = rel>=10 & lo>0; (b) all >= -5")
for q, alts in ((1600, ["f70_8", "f40_10", "f40_14", "f40_16", "f40_8", "f120_8"]), (2000, ["f40_10", "f120_8", "f20_16", "f20_14"])):
    a = ARMS[str(q)]; N = a["N"]
    for idc in alts:
        out = {}
        for inc in ("slow", "block"):
            ip = np.array([R[sk(N, a["IP"][inc], inc, q, s)]["delay_s"] for s in EV])
            idd = np.array([R[sk(N, idc, inc, q, s)]["delay_s"] for s in EV])
            out[inc] = rel(idd, ip)
        print(f"  q{q} ID={idc}:", out)
# AD adapt check on eval (tuned AD) and PI q saturation
print("AD eval ad_max_dev (tuned eta):")
for q in (1600, 2000):
    for inc in ("slow", "block"):
        v = [R[fk(ARMS[str(q)]["AD"], inc, q, s)]["ad_max_dev"] for s in EV]
        print(f"  {inc}_q{q} {ARMS[str(q)]['AD']}: median {np.median(v)}, share>=2: {np.mean(np.array(v)>=2):.2f}, max {max(v)}")
print("meter q behaviour (eval, per arm): share of updates at q_min=200, at q_max=4000; median |dn| between updates; median n")
for q in (1600, 2000):
    a = ARMS[str(q)]
    for inc in ("none", "slow", "block"):
        row = {}
        for x in ("FB", "PI", "AD"):
            qs, dn, ns = [], [], []
            for s in EV:
                ml = R[fk(a[x], inc, q, s)]["meter_log"]
                qs += [e[2] for e in ml]; n_ = [e[1] for e in ml]; ns += n_
                dn += list(np.abs(np.diff(n_)))
            qs = np.array(qs)
            row[x] = (round(float(np.mean(qs <= 200.001)), 2), round(float(np.mean(qs >= 3999.999)), 2), float(np.median(dn)), float(np.median(ns)))
        print(f"  {inc}_q{q}:", row)
