import json, sys
import numpy as np
R = json.load(open("/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"))
M = json.load(open(sys.argv[1]))
L0 = ("N", "FX", "FB", "PI", "AD")
mism = []; NCMP = [0]
def cmp(tag, a, b, tol=1e-9):
    NCMP[0] += 0 if isinstance(a, (list, tuple)) else 1
    if isinstance(a, (list, tuple)):
        for i, (x, y) in enumerate(zip(a, b)): cmp(f"{tag}[{i}]", x, y, tol)
        return
    if isinstance(a, str) or isinstance(a, bool) or a is None:
        if a != b: mism.append((tag, a, b))
        return
    if not np.isclose(a, b, rtol=tol, atol=tol): mism.append((tag, a, b))
def cst(tag, s_r, s_m, tol=1e-9):
    for k in ("ref", "treat", "diff", "rel", "diff_ci", "rel_ci"):
        cmp(f"{tag}.{k}", s_r[k], s_m[k], tol)
# arms
for q in ("1600", "2000"):
    ra, ma = R["tune"]["arms"][q], M["arms"][q]
    for k in L0 + ("ID",): cmp(f"arm{q}.{k}", ra[k], ma[k])
    for i in ("slow", "block"): cmp(f"arm{q}.IP.{i}", ra["IP"][i], ma["IP"][i])
    for p in ("0.1", "0.25", "0.5"):
        for k in L0: cmp(f"arm{q}.prev{p}.{k}", ra["prev"][p][k], ma["prev"][p][k])
ev = R["eval"]
for c, mc in M["cells"].items():
    for r in L0:
        cst(f"{c}.ID_vs_{r}", ev["S1"]["per_cell_stats"][c]["ID_vs"][r]["all_seeds"], mc["ID_vs"][r])
        cst(f"{c}.IP_vs_{r}", ev["cells"][c]["IP_vs_L0"][r]["all_seeds"], mc["IP_vs_L0_S1level"][r])
    cst(f"{c}.IP_vs_ID", ev["S1"]["per_cell_stats"][c]["IP_vs_ID"]["all_seeds"], mc["IP_vs_ID"])
    s2r, s2m = ev["S2"][c]["all_seeds"], mc["S2"]
    cst(f"{c}.S2.ORin_med", s2r["OR_in"]["median"], s2m["OR_in_med"]); cst(f"{c}.S2.ORin_mean", s2r["OR_in"]["mean"], s2m["OR_in_mean"])
    for Rr in ("1", "2", "4"):
        cst(f"{c}.S2.ORX{Rr}_med", s2r["ORX"][Rr]["median"], s2m[f"ORX{Rr}_med"]); cst(f"{c}.S2.ORX{Rr}_mean", s2r["ORX"][Rr]["mean"], s2m[f"ORX{Rr}_mean"])
    cst(f"{c}.S2.plateau", s2r["plateau"], s2m["plateau"])
    for k in ("x", "y", "y_hat", "plateau_holds"): cmp(f"{c}.S2.{k}", s2r[k], s2m[k])
    cst(f"{c}.TP", ev["TP"][c], mc["TP"])
    s3r, s3m = ev["S3"][c], mc["S3"]
    for lab in ("d", "c", "p"):
        a, b = s3r[f"{lab}_star"]["all_seeds"], s3m[lab]
        cmp(f"{c}.{lab}*.value", a["value"], b["value"]); cmp(f"{c}.{lab}*.flag", a["flag"], b["flag"]); cmp(f"{c}.{lab}*.bind", a["binding_arm"], b["binding"])
        cmp(f"{c}.{lab}*.ci", a["ci"], b["ci"]); cmp(f"{c}.{lab}*.gtmax", a["share_censored_gt_max"], b["share_gt_max"]); cmp(f"{c}.{lab}*.never", a["share_never_ahead"], b["share_never"])
        for r in L0:
            cmp(f"{c}.{lab}*.{r}.value", a["per_arm"][r]["value"], b["per_arm"][r]["value"]); cmp(f"{c}.{lab}*.{r}.M", a["per_arm"][r]["M"], b["per_arm"][r]["M"])
    cmp(f"{c}.comb.med", s3r["combined_row"]["median_delay_s"], s3m["combined_median"])
    cst(f"{c}.comb.vsIP", s3r["combined_row"]["vs_IP"]["all_seeds"], s3m["combined_vs_IP"])
    for r in L0: cst(f"{c}.comb.vs{r}", s3r["combined_row"]["vs_L0"][r]["all_seeds"], s3m["combined_vs_L0"][r])
    # Table 1 medians
    t1 = ev["table1_operating_map"][c]["arms"]
    for k, v in mc["median"].items():
        if k in t1: cmp(f"{c}.T1.{k}", t1[k]["median_delay_s"], v)
for q in ("1600", "2000"):
    pr, pm = ev["per_q"][q], M["per_q"][q]
    for k, v in pm["clean_median"].items(): cmp(f"clean{q}.{k}", pr["clean_day"][k]["median_delay_s"], v)
    cst(f"fa{q}", pr["false_alarm_cost"]["all_seeds"], pm["fa_cost"])
    for p in ("0.1", "0.25", "0.5"):
        a, b = pr["prevalence"][p]["f_star"]["all_seeds"], pm["f_star"][p]
        cmp(f"f*{q}.{p}.value", a["value"], b["value"]); cmp(f"f*{q}.{p}.bind", a["binding_arm"], b["binding"]); cmp(f"f*{q}.{p}.ci", a["ci"], b["ci"])
        cmp(f"f*{q}.{p}.flag", a["flag"], b["flag"])
s1 = ev["S1"]
cmp("S1a", s1["S1a_pass"], M["S1"]["S1a_pass"]); cmp("S1b", s1["S1b_pass"], M["S1"]["S1b_pass"])
cmp("S1b_cells", s1["S1b_cells_both_views"], M["S1"]["S1b_a_cells"])
cmp("S1a_cells", s1["S1a_cells_both_views"], M["S1"]["S1a_common_a_cells"])
print("mismatches:", len(mism))
for m in mism[:80]: print(m)
print("checks", M["checks"])
