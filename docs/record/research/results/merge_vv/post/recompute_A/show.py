import json
res = json.load(open("results_A.json"))
f = lambda x: "None" if x is None else f"{x:+.2f}"
for k, v in res.items():
    if isinstance(v, dict) and "point" in v:
        if v["point"] is None:
            print(f"{k}: point None (rule median {v.get('rule_median')})"); continue
        s = f"{k}: {f(v['point'])}"
        for c in ("ci95", "ci97_5", "ci98_75"):
            if c in v:
                s += f" {c}[{f(v[c][0])},{f(v[c][1])}]"
        if "per_learner" in v:
            s += " L:" + ",".join(f"{x:.1f}" for x in v["per_learner"]) + f" med={v['rule_median']:.1f}"
        print(s)
    elif k == "standing":
        for kk, d in v.items():
            print(f"stand {kk}: mean300 {d['mean300']:.1f} mean600 {d['mean600']:.1f} med300 {d['median300']:.1f} med600 {d['median600']:.1f} cut {d['cut_mean']} ci95 [{d['cut_mean_ci95'][0]:.3f},{d['cut_mean_ci95'][1]:.3f}] zero600 {d['share_zero_600']:.2f} veh {d.get('vehicles_mean300','-')} -> {d.get('vehicles_mean600','-')}")
    else:
        print(k, v)
