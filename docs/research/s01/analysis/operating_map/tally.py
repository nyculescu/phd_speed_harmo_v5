"""Tally of opmap.json: per (P, O), comparisons on the six main metrics with P better / O better (95 % CI excludes 0) / neither."""
import json
R = json.load(open("opmap.json"))
MAIN = ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "finished_pct")
T = {}
for c in R["cmp"]:
    if c["key"] not in MAIN:
        continue
    t = T.setdefault((c["P"], c["O"]), {"P_better": [], "O_better": [], "neither": 0})
    lo, hi = c["eff"][1], c["eff"][2]
    if lo > 0:
        t["P_better"].append(f'{c["setting"]}:{c["key"]}')
    elif hi < 0:
        t["O_better"].append(f'{c["setting"]}:{c["key"]}')
    else:
        t["neither"] += 1
for (p, o), t in T.items():
    print(f"{p} vs {o}: P better {len(t['P_better'])}, O better {len(t['O_better'])}, neither {t['neither']}; O better at {t['O_better']}")
for c in R["cmp"]:
    if c["key"] == "finished_pct" and c["O"] == "p333" and c["setting"] in ("5000",):
        print("finished_pct pp", c["P"], c["setting"], [round(x, 3) for x in c["abs"]], "medP", round(c["medP"], 2), "medO", round(c["medO"], 2))
json.dump({f"{p}|{o}": t for (p, o), t in T.items()}, open("tally.json", "w"), indent=1)
