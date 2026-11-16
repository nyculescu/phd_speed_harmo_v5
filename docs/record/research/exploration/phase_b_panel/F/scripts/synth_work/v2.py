import json
J = json.load(open("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json"))
T = J["cells"]["TRUCK"]
def r(x):
    return [round(t, 2) for t in x] if isinstance(x, list) else (round(x, 2) if isinstance(x, (int, float)) else x)
m = T["map"]
pl = m["3E-C_TRUCK"]["per_learner"]
for L, v in pl.items():
    print(L, type(v).__name__, (sorted(v) if isinstance(v, dict) else v))
    if isinstance(v, dict):
        print("   ", {k: r(x) if not isinstance(x, dict) else {a: r(b) for a, b in x.items()} for k, x in v.items()})
plo = m["os0_10_10"]["per_learner"]
print("os0 per learner", {L: ({k: r(x) if not isinstance(x, dict) else {a: r(b) for a, b in x.items()} for k, x in v.items()} if isinstance(v, dict) else v) for L, v in plo.items()})
S = J["S"]
print("S keys", sorted(S))
Sm = S["map"]
print("n S map", len(Sm))
cnt = [(o, round(Sm[o]["cf"]["effect"], 2), r(Sm[o]["cf"]["ci_m"])) for o in Sm if Sm[o]["cf"]["ci_m"][0] <= 0 or Sm[o]["cf"]["effect"] < 10]
print("S: K1 fires against", cnt)
dS = [(o, round(Sm[o]["delay"]["effect"], 2), r(Sm[o]["delay"]["ci_m"])) for o in Sm if Sm[o]["delay"]["ci_m"][0] <= -2]
print("S: delay lb <= -2 against", len(dS), [x[0] for x in dS])
dS1 = [o for o in Sm if Sm[o]["delay"]["ci_m"][0] <= -1]
print("S: delay lb <= -1 against", len(dS1))
print("top keys", sorted(J))
ro = T["map_report_only"]
for o in ("3E-C_TRUCK", "p333"):
    for k in ("collisions", "alks_full_moving"):
        e = ro[o][k]
        print(o, k, {a: r(b) for a, b in e.items()})
print("nc keys", sorted(T.get("no_control", {}))[:30])
