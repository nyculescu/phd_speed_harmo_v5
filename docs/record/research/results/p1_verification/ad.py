import sys, json
sys.path.insert(0, "/home/catalin/work/phd/p1_frozen_85f7d34")
import numpy as np
from v5b.p1 import analysis as an, stats as st
RUN = "/home/catalin/work/phd/v5b1_runs/p1/v99"
R = json.load(open(f"{RUN}/result.json"))
seeds = range(R["seeds"]["eval"][0], R["seeds"]["eval"][1] + 1)
a = R["tune"]["arms"]["2000"]
D = lambda g: np.array([json.load(open(f"{RUN}/runs/{an.fixed(g,'none',2000.0,s)['key']}.json"))["delay_s"] for s in seeds])
n = D(a["N"]); 
for x in ("AD","FB"): print(x, repr(st.paired(D(a[x]), n, 0.95)["diff"]))
