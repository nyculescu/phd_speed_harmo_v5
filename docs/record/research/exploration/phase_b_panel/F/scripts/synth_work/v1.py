import json
J = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json"))
T = J["cells"]["TRUCK"]
def r(x):
    return [round(t, 2) for t in x] if isinstance(x, list) else round(x, 2)
def show(tag, e):
    print(tag, "effect", r(e["effect"]), "ci95", r(e["ci95"]), "ci_m", r(e["ci_m"]), "medP", e.get("median_P"), "medO", e.get("median_O"))
ro = T["map_report_only"]
for o in ("3E-C_TRUCK", "p333", "os0_10_10"):
    for k in ("jam_share", "jams", "congested_km_mean", "congested_km_max", "congested_share", "osc_kmh", "events_ge45", "b45_step", "ttc15", "ttc2", "sev3", "robust_braking", "ttc3_lc_share", "flow", "collisions", "alks_full_moving", "alks_past_limit"):
        if k in ro[o]:
            try:
                show(f"TRUCK ro {o} {k}", ro[o][k])
            except Exception as ex:
                print("TRUCK ro", o, k, "keys", sorted(ro[o][k]) if isinstance(ro[o][k], dict) else ro[o][k])
m = T["map"]
print("n opponents in map", len(m))
lows = sorted((m[o]["cf"]["ci_m"][0], o, m[o]["cf"]["effect"]) for o in m)
print("lowest cf lower bounds", [(round(a, 2), o, round(e, 2)) for a, o, e in lows[:4]])
dl = sorted((m[o]["delay"]["ci_m"][0], o, m[o]["delay"]["effect"]) for o in m)
print("lowest delay lower bounds", [(round(a, 2), o, round(e, 2)) for a, o, e in dl[:5]])
print("3E-C flow", {k: r(v) for k, v in m["3E-C_TRUCK"]["flow"].items()})
pl = m["3E-C_TRUCK"]["per_learner"]
for L, v in pl.items():
    print(L, {k: (r(v[k]["effect"]), r(v[k]["ci_m"])) for k in ("delay", "cf") if k in v} if isinstance(v, dict) else v)
S = J["S"]
print("S keys", sorted(S))
Sm = S["map"]
print("n S map", len(Sm))
cnt = [(o, round(Sm[o]["cf"]["effect"], 2), r(Sm[o]["cf"]["ci_m"])) for o in Sm if Sm[o]["cf"]["ci_m"][0] <= 0 or Sm[o]["cf"]["effect"] < 10]
print("S: K1 fires against", cnt)
dS = [(o, round(Sm[o]["delay"]["effect"], 2), r(Sm[o]["delay"]["ci_m"])) for o in Sm if Sm[o]["delay"]["ci_m"][0] <= -2]
print("S: delay lb <= -2 against", len(dS), dS)
dS1 = [o for o in Sm if Sm[o]["delay"]["ci_m"][0] <= -1]
print("S: delay lb <= -1 against", len(dS1))
print("top keys", sorted(J))
print("must_carry" in J, [k for k in J if "carry" in k])
