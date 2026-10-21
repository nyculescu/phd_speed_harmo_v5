"""Self-check of note claims (D): red crossings at s = 0, max queue tail over all evaluation runs, IP vs PI under
runners, largest median max queue (veh) over Table 1 arms, and the kinds of own-seed mismatches.
Usage: selfcheck.py recs.pkl mine_page.json compare_own.log"""
import json, pickle, sys, re
recs = pickle.load(open(sys.argv[1], "rb"))
M = json.load(open(sys.argv[2]))
R = json.load(open("/home/catalin/work/phd/v5b1_runs/p1b/v108/result.json"))
ev = [r for r in recs if 7400600 <= r["seed"] <= 7400699]
s0 = [r for r in ev if not r["rs"]]
print("s=0 eval runs", len(s0), "with any red crossing", sum((r["crossings"] or {}).get("r", 0) > 0 for r in s0),
      "max red_cross_share", max(r["red_cross_share"] or 0 for r in s0))
print("max max_queue_m over all eval runs", max(r["max_queue_m"] for r in ev), "avail", {r["avail_m"] for r in ev})
for c in ("block_q1600", "slow_q2000"):
    for s in ("0.1", "0.3"):
        v = M["runner_rows"][f"s{s}_{c}"]["IP_vs"]
        print(f"runners s{s} {c} IP vs " + "; ".join(f"{x} {100 * v[x]['rel']:+.1f} [{100 * v[x]['rel_ci'][0]:+.1f}, "
                                                    f"{100 * v[x]['rel_ci'][1]:+.1f}]" for x in v))
t = [(c, x, a["median_max_queue"]) for c, m in R["eval"]["table1_operating_map"].items() for x, a in m["arms"].items()]
print("largest median max queue (veh):", sorted(t, key=lambda z: -z[2])[:3])
tags = [re.sub(r"\[\d\]", "", l.split("'")[1]) for l in open(sys.argv[3]) if l.startswith("(")]
kinds = sorted({t.split(".")[-1] for t in tags})
print("own-seed mismatch count", len(tags), "field kinds", kinds)
