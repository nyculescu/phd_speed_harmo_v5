# Stored E30 rows: what the plant already holds on merges. Exploratory, before protocol approval.
import sys, json
import numpy as np
arms = ("E30|nc", "E30|lr400_16_1", "E30|p333", "E30|w1u500")
acc = {a: dict(m1=np.zeros(10), m2=np.zeros(10), n=0, es=[], es2=[], pm=[], v3a1=[], v4a1=[], halt=[], med1=[], med2=[], m1n=[], m2n=[], ramp_in1=[], ramp_in2=[], r4a=[], ttc=[]) for a in arms}
with open(sys.argv[1]) as f:
    for line in f:
        if not any(f'"name": "{a}"' in line for a in arms):
            continue
        r = json.loads(line)
        A = acc[r["name"]]
        h1, h2 = np.array(r["m_mergepos_m1"], float), np.array(r["m_mergepos_m2"], float)
        A["m1"] += h1; A["m2"] += h2; A["n"] += 1
        A["m1n"].append(h1.sum()); A["m2n"].append(h2.sum())
        for h, k in ((h1, "med1"), (h2, "med2")):
            c = np.cumsum(h) / h.sum(); j = int(np.searchsorted(c, 0.5)); lo = c[j - 1] if j else 0.0
            A[k].append((j + (0.5 - lo) / (c[j] - lo)) / 10.0)
        A["es"].append(r["end_stop"]); A["es2"].append(r["end_stop2"]); A["pm"].append(r.get("pass_merging", 0.0)); A["halt"].append(r["halt_3a_0"])
        A["v3a1"].append(r["nv_3a_1"] / max(r["n_3a_1"], 1)); A["v4a1"].append(r["nv_4a_1"] / max(r["n_4a_1"], 1))
        mm = r["m_minute"]
        A["ramp_in1"].append(sum(mm["m1_ramp_in"])); A["ramp_in2"].append(sum(mm["m2_ramp_in"]))
        A["r4a"].append(r.get("ttc3_r_4a", 0.0)); A["ttc"].append(r["ttc_net"])
        if A["n"] == 1:
            print(r["name"], "m_minute keys:", sorted(mm)[:30], "minutes:", len(mm["m1_out"]), "m_planned_window", r.get("m_planned_window"), "steps", r["steps"], "veh", r["c1_t0"])
for a, A in acc.items():
    md = lambda x: round(float(np.median(x)), 2)
    print("==", a, "runs", A["n"])
    for k, h in (("m1 (3a)", A["m1"]), ("m2 (4a)", A["m2"])):
        print("  leave-lane-0 position, share per tenth of the lane,", k, np.round(h / h.sum(), 3).tolist(), "per run", round(h.sum() / A["n"], 1))
    print("  per-run median position share m1/m2 (interpolated in 10 bins), median over runs:", md(A["med1"]), md(A["med2"]), "; p10-p90 over runs m2:", np.round(np.quantile(A["med2"], [.1, .9]), 2).tolist())
    print("  counted leave events per run m1/m2:", md(A["m1n"]), md(A["m2n"]), "; ramp vehicles entering 3a/4a per run:", md(A["ramp_in1"]), md(A["ramp_in2"]))
    print("  end_stop (3a) vehicle-seconds per run median/mean:", md(A["es"]), round(float(np.mean(A["es"])), 1), "; end_stop2 (4a):", md(A["es2"]), round(float(np.mean(A["es2"])), 1), "; pass_merging:", md(A["pm"]), "; halt_3a_0:", md(A["halt"]))
    print("  mean speed m/s, main lane next to the acceleration lane: 3a_1", md(A["v3a1"]), " 4a_1", md(A["v4a1"]), "; ttc_net", md(A["ttc"]), "ttc3_r_4a", md(A["r4a"]))
