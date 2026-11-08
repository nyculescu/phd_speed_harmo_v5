"""(a), (b), (e): paired 95 % CIs for braking metrics, policies (v3w, tail, sw, baseline-v3) against nc, 3E-T, 3E-X1/X2, p333, os1_15_10,
plus each rule against nc for context. Effect = -median(P - O) / median(O) x 100 (positive = P has less); diff = median(P - O) in units.
Writes stats_all.tsv (every comparison) and prints the v3w lines."""
from common_x import OUT, POLICIES, RULES, arm, diff_ci, effect95, load_T, med

METRICS = [
    # absolute counts
    "ev45_all", "ev45_car", "ev45_alks", "ev45_truck", "ev4_all", "ev4_car", "ev4_alks", "ev5_alks", "ev5_car", "ev9_alks",
    "ev_all", "ev_car", "ev_alks", "lt5_steps_alks", "lt5_steps_car",
    "b3_step", "b45_step", "b7_step", "alks_b3_step", "alks_b45_step", "alks_b7_step", "human_b45_step", "human_b3_step",
    "free_brake_alks_step", "alks_full_moving", "alks_full_creep",
    # exposure
    "passed", "km_all", "km_car", "km_alks", "all_delay", "ttc_net",
    # normalised
    "ev45_all_per_km", "ev45_car_per_km", "ev45_alks_per_km", "ev4_all_per_km", "ev4_car_per_km", "ev4_alks_per_km", "ev5_alks_per_km",
    "ev45_all_per_served", "ev45_car_per_served", "ev45_alks_per_served", "ev4_all_per_served", "ev5_alks_per_served",
    "b45_step_per_km", "alks_b45_step_per_km", "human_b45_step_per_km", "b45_step_per_served", "alks_b45_share",
    # cascades
    "cshare_car", "cshare_alks", "cshare_all", "casc_car", "casc_alks",
]
EXPOSURE = {"passed": 1, "km_all": 1, "km_car": 1, "km_alks": 1}     # sign +1: more is "better" (more served)

T = load_T()
lines = ["cell\tP\tO\tmetric\tmedP\tmedO\teffect_pct\tlo\thi\tdiff\tdlo\tdhi"]
n_comp = 0
for cell in ("X1", "X2"):
    rules = RULES[cell]
    pairs = [(p, o) for p in POLICIES for o in rules] + [(o, "nc") for o in rules if o != "nc"]
    A = {g: arm(T, cell, g) for g in (*POLICIES, *rules)}
    for p, o in pairs:
        for m in METRICS:
            mo = med(A[o], m)
            e = effect95(A[p], A[o], m, sign=EXPOSURE.get(m, -1)) if abs(mo) > 1e-9 else (float("nan"),) * 3
            d = diff_ci(A[p], A[o], m)
            lines.append("\t".join([cell, p, o, m, f"{med(A[p], m):.6g}", f"{mo:.6g}", *[f"{x:.2f}" for x in e], *[f"{x:.6g}" for x in d]]))
            n_comp += 1
(OUT / "stats_all.tsv").write_text("\n".join(lines) + "\n")
print("comparisons (cell x pair x metric):", n_comp, "pairs per cell:", len(pairs))
show = ["ev45_all", "ev45_car", "ev45_alks", "ev4_all", "ev4_car", "ev4_alks", "ev5_alks", "ev9_alks", "lt5_steps_alks", "b45_step", "alks_b45_step",
        "human_b45_step", "b7_step", "alks_b7_step", "free_brake_alks_step", "alks_full_moving", "passed", "km_all", "ev45_all_per_km", "ev45_car_per_km",
        "ev45_alks_per_km", "ev4_car_per_km", "ev4_alks_per_km", "ev5_alks_per_km", "ev45_all_per_served", "ev45_car_per_served", "ev45_alks_per_served",
        "alks_b45_step_per_km", "human_b45_step_per_km", "cshare_car", "cshare_alks", "cshare_all"]
for ln in lines[1:]:
    f = ln.split("\t")
    if f[1] == "v3w" and f[2] in ("nc", "3e") and f[3] in show:
        print(f"{f[0]} v3w vs {f[2]:4s} {f[3]:24s} medP {float(f[4]):10.4g} medO {float(f[5]):10.4g}  eff {f[6]:>7}% [{f[7]:>7}, {f[8]:>7}]  diff {float(f[9]):9.4g} [{float(f[10]):9.4g}, {float(f[11]):9.4g}]")
