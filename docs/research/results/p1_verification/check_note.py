import sys, json, os
sys.path.insert(0, "/home/catalin/work/phd/p1_frozen_85f7d34")
import numpy as np
from v5b.p1 import analysis as an, stats as st
from v5b.d2.incidents import NONE, INCIDENTS
RUN = "/home/catalin/work/phd/v5b1_runs/p1/v99"
R = json.load(open(f"{RUN}/result.json"))
seeds = list(range(R["seeds"]["eval"][0], R["seeds"]["eval"][1] + 1))
arms = R["tune"]["arms"]
cache = {}
def load(k):
    if k not in cache:
        cache[k] = json.load(open(f"{RUN}/runs/{k}.json"))
    return cache[k]
def D(keys): return np.array([load(k)["delay_s"] for k in keys], float)
def fx(g, inc, q): return D([an.fixed(g, inc, q, s)["key"] for s in seeds])
def sw(N, a, inc, q, **kw): return D([an.sw(N, a, inc, q, s, **kw)["key"] for s in seeds])
def csw(N, a, inc, q, **kw): return D([an.canon_sw(N, a, inc, q, s, **kw)["key"] for s in seeds])
def fmt(p, pct=False):
    if pct: return "rel %.2f%% [%.2f, %.2f]  diff %.2f [%.2f, %.2f]" % (100*p["rel"], 100*p["rel_ci"][0], 100*p["rel_ci"][1], p["diff"], *p["diff_ci"])
    return "diff %.2f [%.2f, %.2f]" % (p["diff"], *p["diff_ci"])
out = {}
QS_RUN = [float(x) for x in sys.argv[1:]] or [1600.0, 2000.0]
for q in QS_RUN:
    a = arms[an.qk(q)]
    N = a["N"]
    clean = {x: fx(a[x], NONE, q) for x in ("N", "FX", "FB", "PI", "AD")}
    clean["NC"] = fx("NC", NONE, q)
    med = np.median(clean["N"])
    print(f"q{int(q)} N clean median {med:.2f}; seeds with N > 2*median: {int((clean['N'] > 2*med).sum())}/{len(seeds)}")
    for x in ("FX", "FB", "PI", "AD", "NC"):
        pm = st.paired(clean[x], clean["N"], 0.95)            # diff = median(x - N)
        pmean = st.paired(clean[x], clean["N"], 0.95, mean=True)
        print(f"  {x} - N clean: median {fmt(pm)} | mean {fmt(pmean)}")
    # IP vs PI_pi mean gain (D)
    Dn = clean["N"]
    inc_ip = {i: sw(N, a["IP"][i], i, q) for i in INCIDENTS}
    inc_id = {i: sw(N, a["ID"], i, q) for i in INCIDENTS}
    for pi_s, p in a["prev"].items():
        pi = float(pi_s)
        g = p["PI"]
        L = st.prevalence_mix(fx(g, "slow", q), fx(g, "block", q), fx(g, NONE, q), pi)
        T = st.prevalence_mix(inc_ip["slow"], inc_ip["block"], Dn, pi)
        Ti = st.prevalence_mix(inc_id["slow"], inc_id["block"], Dn, pi)
        print(f"  pi {pi}: PI_pi {g}: IP vs PI_pi median {fmt(st.paired(L, T, 0.95), True)} | mean {fmt(st.paired(L, T, 0.95, mean=True), True)}")
        print(f"            ID vs PI_pi mean {fmt(st.paired(L, Ti, 0.95, mean=True), True)}")
    # cells
    for inc in INCIDENTS:
        name = an.cell_name(inc, q)
        ip = sw(N, a["IP"][inc], inc, q); idd = sw(N, a["ID"], inc, q)
        pi_ = fx(a["PI"], inc, q); fb = fx(a["FB"], inc, q)
        print(f"  {name}: IP vs PI 95% {fmt(st.paired(pi_, ip, 0.95), True)}; IP vs FB 95% {fmt(st.paired(fb, ip, 0.95), True)}")
        print(f"     IP vs ID 95% {fmt(st.paired(idd, ip, 0.95), True)}")
        for alt in ("f40_10", "f70_8", "f40_14", "f40_16", "f70_10"):
            alt_d = sw(N, alt, inc, q) if alt != N else fx(N, inc, q)
            print(f"     IP vs ID'={alt}: {fmt(st.paired(alt_d, ip, st.LEVEL_S1), True)}")
        for d in (30.0, 60.0):
            ipd = csw(N, a["IP"][inc], inc, q, d=d)
            print(f"     IP(d={d}) vs ID: {fmt(st.paired(idd, ipd, st.LEVEL_S1), True)}")
            try:
                print(f"       IP(d) vs ID(d): {fmt(st.paired(csw(N, a['ID'], inc, q, d=d), ipd, st.LEVEL_S1), True)}")
            except FileNotFoundError as ex:
                print('       ID(d) runs missing', os.path.basename(str(ex)))
