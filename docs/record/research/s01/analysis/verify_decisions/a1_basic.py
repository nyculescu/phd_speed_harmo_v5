import numpy as np
from collections import Counter, defaultdict
from base import *
rows, T = load()
print("rows", len(rows), "groups", len(T))
cells = Counter((c, q) for (c, a, q) in T); print(sorted(cells.items()))
# which arms have dec
hasdec = defaultdict(lambda: [0, 0])
for r in rows:
    a = r["name"].split("|")[1]; hasdec[a][0] += 1; hasdec[a][1] += bool(r.get("m_dec_totals"))
print("arms without full dec:", {a: v for a, v in hasdec.items() if v[0] != v[1]})
# conf_med check against summary json for a sample
import json
S = json.load(open("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/summary_rows_test.json"))
mx = 0; n = 0; mxs = 0; mxr = 0
for r in rows:
    if r["src"] != "rows_test.jsonl": continue
    d = derived(r)
    if d is None: continue
    sm = S[f"{r['name']}|{r['q']:.0f}"][str(r["seed"])]["dec"]
    if sm["conf_q"] is not None:
        mx = max(mx, abs(sm["conf_q"][1] - d["conf_med"]))
    mxs = max(mxs, abs(sm["level_share_on"][-1] - d["share3"])); mxr = max(mxr, abs((sm["reversal_share"] or 0) - (0 if np.isnan(d["rev_share"]) else d["rev_share"])))
    n += 1
print("summary vs own derived, test rows:", n, "max |conf_med diff|", mx, "max |share3 diff|", mxs, "max |rev diff|", mxr)
# lv (env's applied level, zone x level) vs m_dec_level_s; ttc3 vs ttc_net
bad_lv = bad_ttc = nlv = 0
for r in rows:
    if r.get("m_dec_totals"):
        nlv += 1
        lv = np.array(r["lv"]).reshape(3, 4).sum(0)
        bad_lv += not np.array_equal(lv, np.array(r["m_dec_level_s"]))
    bad_ttc += abs(g(r, "ttc3") - g(r, "ttc_net")) > 1e-9
print("lv==m_dec_level_s mismatches", bad_lv, "of", nlv, "; ttc3!=ttc_net", bad_ttc, "of", len(rows))
# p333 per cell/level
print("\np333 share at index 3 (0.8 s), want share 3, reversals, excess, changes/ALKS, tau_on_match/n")
for (c, a, q), tab in sorted(T.items()):
    if a != "p333": continue
    D = [derived(r) for r in tab.values()]
    sh = np.array([d["share3"] for d in D])
    print(f"  {c} {q:.0f} n={len(D)} share3 med {np.median(sh):.4f} range {sh.min():.3f}-{sh.max():.3f}; want3 min {min(d['want3'] for d in D):.4f};"
          f" rev max {max(d['reversals'] for d in D)}; excess max {max(r['m_dec_excess'] for r in tab.values())}; chg/ALKS med {np.median([d['chg_pv'] for d in D]):.3f};"
          f" on_s/veh med {np.median([d['on_s']/d['veh'] for d in D]):.1f}; tau match {min(g(r,'tau_on_match')/g(r,'tau_on_n') for r in tab.values()):.4f};"
          f" asked/ALKS {np.median([d['asked_pv'] for d in D]):.1f}")
# all arms share3 X1 for context, and other rule arms' share3 in band 4500
print("\nshare3 median per arm (X1 5300, X2 5300):")
for a in sorted({a for (c, a, q) in T if c == "X1"}):
    if a == "nc": continue
    x1 = [derived(r)["share3"] for r in T[("X1", a, 5300.0)].values()]
    x2 = [derived(r)["share3"] for r in T[("X2", a, 5300.0)].values()]
    print(f"  {a:14s} X1 {np.median(x1):.3f}  X2 {np.median(x2):.3f}  asked/ALKS X1 {np.median([derived(r)['asked_pv'] for r in T[('X1', a, 5300.0)].values()]):.1f}")
