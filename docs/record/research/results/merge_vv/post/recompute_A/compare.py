"""Key-by-key comparison of recomputer A's numbers (results_A.json, nulls_A.json) with the committed reader's v3.json."""
import json
import numpy as np
A = json.load(open("results_A.json")); N = json.load(open("nulls_A.json"))
V = json.load(open("/home/catalin/work/phd/v5b1_runs/vv_remote/vv_screen/v3.json"))
rows = []

def cmp(label, mine, theirs):
    d = None if mine is None or theirs is None else abs(mine - theirs)
    rows.append((label, mine, theirs, d))

def edge(label, a, v, mine_lo="ci97_5", their_lo=("lo", "hi")):
    cmp(label + " pt", a["point"], v["pt"])
    cmp(label + " lo", a[mine_lo][0], v[their_lo[0]]); cmp(label + " hi", a[mine_lo][1], v[their_lo[1]])
    if "ci95" in a and "lo95" in v:
        cmp(label + " lo95", a["ci95"][0], v["lo95"]); cmp(label + " hi95", a["ci95"][1], v["hi95"])

for r in ("lr400_16_1", "grid_lr400_13_1"):
    edge(f"V2 0.1s {r}", A[f"V2_edge_0.1s|{r}"], V["v2"][r]["edge_01s"])
    edge(f"V2 1Hz {r}", A[f"V2_edge_1Hz|{r}"], V["v2"][r]["edge_1hz"])
    cmp(f"V2 diff {r} pt", A[f"V2_diff|{r}"]["point"], V["v2"][r]["diff"]["pt"])
    cmp(f"V2 diff {r} lo95", A[f"V2_diff|{r}"]["ci95"][0], V["v2"][r]["diff"]["lo95"]); cmp(f"V2 diff {r} hi95", A[f"V2_diff|{r}"]["ci95"][1], V["v2"][r]["diff"]["hi95"])
    edge(f"V3a rep {r}", A[f"V3a_ttc_net_300|{r}"], V["v3a"]["replication"][r])
    cmp(f"V3a rep {r} null", N[f"V3a_ttc_net_300|{r}|97.5"]["rate"], V["v3a"]["replication"][r]["null"]["rate"])
    edge(f"V3a main {r}", A[f"V3a_main_300|{r}"], V["v3a"]["main_lane"][r])
    cmp(f"V3a main {r} null", N[f"V3a_main_300|{r}|97.5"]["rate"], V["v3a"]["main_lane"][r]["null"]["rate"])
    edge(f"V3b holds {r}", A[f"V3b_ttc_net_600|{r}"], V["v3b"]["holds"][r])
    edge(f"V3b worse {r}", A[f"V3b_ttc_net_600|{r}"], V["v3b"]["worse"][r], mine_lo="ci98_75")
    cmp(f"V3b change {r} pt", A[f"V3b_change|{r}"]["point"], V["v3b"]["change"][r]["pt"])
    cmp(f"V3b change {r} lo95", A[f"V3b_change|{r}"]["ci95"][0], V["v3b"]["change"][r]["lo95"]); cmp(f"V3b change {r} hi95", A[f"V3b_change|{r}"]["ci95"][1], V["v3b"]["change"][r]["hi95"])
    edge(f"600 no edge1 {r}", A[f"ex_edge1_L600|{r}"], V["v3b"]["no_edge1_600"][r], mine_lo="ci95")
cmp("V3b worse lr400_16_1 null", N["V3b_ttc_net_600|lr400_16_1|98.75"]["rate"], V["v3b"]["worse"]["lr400_16_1"]["null"]["rate"])
for arm, ms in A["V2_missed_share"].items():
    cmp(f"missed share {arm} (median of runs)", ms["median_of_runs"], V["v2"]["missed_share"][arm])
# printed groups (95 %)
gm = {"merge": "g_merge", "e1": "g_edge1", "rest": "g_rest", "m1": "g_m1", "m2": "g_m2"}
for L, key in (("L300", "printed_300"), ("L600", "printed_600")):
    for r in ("lr400_16_1", "grid_lr400_13_1", "p333", "nc"):
        for g, tg in gm.items():
            a = A.get(f"group_{g}_{L}|{r}")
            v = V[key][r][tg]
            if a["point"] is None:
                rows.append((f"{key} {r} {tg} pt", "undefined (rule median 0)", v["pt"], "DEF"))
                continue
            edge(f"{key} {r} {tg}", a, v, mine_lo="ci95")
        edge(f"{key} {r} ttc_no_e1", A[f"ex_edge1_{L}|{r}"], V[key][r]["ttc_no_e1"], mine_lo="ci95")
# standing cut: the reader's form is the ratio of medians; mine in standing_variants
SV = A["standing_variants"]
for m, mm in (("merge1", "m1"), ("merge2", "m2")):
    for arm in ("v3w", "lr400_16_1", "grid_lr400_13_1", "p333", "nc"):
        k = f"{'v3w_pooled' if arm == 'v3w' else arm}|{mm}"
        cmp(f"cut {m} {arm} (median form) pt", SV[k]["cut_median"], V["v3b"]["cut"][m][arm]["cut"])
        cmp(f"cut {m} {arm} (median form) lo95", SV[k]["cut_median_ci95"][0], V["v3b"]["cut"][m][arm]["lo95"])
mx = max(d for _, _, _, d in rows if isinstance(d, float))
for lab, a, b, d in rows:
    if d == "DEF" or (isinstance(d, float) and d > 1e-9):
        print(f"{lab}: mine {a} | v3 {b} | diff {d}")
print("compared", len(rows), "values; exact (<=1e-9):", sum(isinstance(d, float) and d <= 1e-9 for _, _, _, d in rows))
json.dump([list(map(lambda x: x if not isinstance(x, np.floating) else float(x), r)) for r in rows], open("compare_A.json", "w"), indent=0)
