"""Independent recomputation from the raw JSON lines, with its own slowdown draw, compared with trainlog.json. usage: independent.py train_dir trainlog.json"""
import json
import sys

import numpy as np

d, J = sys.argv[1], json.load(open(sys.argv[2]))


def slow(seed):
    r = np.random.default_rng(seed + 910_000)
    if r.random() < 1.0 / 3.0:
        return 0.0
    r.choice(("3", "4", "5"))
    return float(r.uniform(25.0, 60.0))


bad, n = [], 0
for i in range(5):
    U = [json.loads(x) for x in open(f"{d}/C{i}_updates.jsonl")]
    E = [json.loads(x) for x in open(f"{d}/C{i}_episodes.jsonl")]
    L = J["learners"][f"C{i}"]
    for key, src in (("reward_per_decision", "r"), ("entropy", "entropy"), ("explained_variance", "ev"), ("approx_kl", "kl"), ("clip_fraction", "clipfrac")):
        a = np.mean([x[src] for x in U[450:500]])
        b = np.mean(L["ppo"][key][450:500])
        n += 1
        bad += [f"C{i} {key}: raw {a} series {b}"] if abs(a - b) > 1e-12 else []
    vl = np.mean([x["value_loss"] * x["scale"] ** 2 for x in U[:50]])
    n += 1
    bad += [f"C{i} value loss raw units"] if abs(vl - np.mean(L["ppo"]["value_loss_reward_units"][:50])) > 1e-9 else []
    for q in (4090.0, 4600.0, 5300.0):
        for e in E:
            if e["q"] != q:
                continue
            T = L["traffic"][str(int(q))]
            for k, raw in (("vehicles_into_road4", e["passed"]), ("vehicle_seconds_in_system", e["N"]), ("ttc_below_3s_merge1_lanes", e["E30"]), ("slowdown_limit_kmh", slow(e["seed"]))):
                n += 1
                if abs(T[k][e["u"]] - raw) > 1e-9:
                    bad.append(f"C{i} u{e['u']} q{q} {k}: raw {raw} series {T[k][e['u']]}")
    for u in (0, 250, 499):
        lv = np.sum([e["lv"] for e in E if e["u"] == u], axis=0).reshape(3, 4)
        for zi, z in enumerate(("upstream", "merge1", "downstream_incl_merge2")):
            for li, l in enumerate(("1.6s", "1.2s", "1.0s", "0.8s")):
                n += 1
                if abs(lv[zi, li] / lv[zi].sum() - L["levels"][f"{z}/{l}"][u]) > 1e-12:
                    bad.append(f"C{i} u{u} {z} {l}")
print("independent values compared:", n, "mismatches:", len(bad), bad[:5])
sys.exit(1 if bad else 0)
