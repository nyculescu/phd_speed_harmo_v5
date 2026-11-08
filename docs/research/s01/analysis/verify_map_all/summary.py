import json
from collections import Counter
M = json.load(open("mine.json"))
mk = lambda lo, hi: "A" if lo > 0 else ("R" if hi < 0 else "=")
order = ["X1|5300", "X2|5300", "B|3500", "B|4500", "B|5000", "B|5250", "B|5500", "B|6000", "B|7000"]
for a in ("v3w", "tail", "sw"):
    cnt = {m: Counter() for m in ("delay", "cf", "flow", "b3", "b45")}
    both = []
    for c in order:
        if a not in M[c]["arms"]: continue
        Rs = []
        for r in M[c]["rules"]:
            mm = {m: mk(*M[c]["eff"][f"{a}|{r}|{m}"][1:]) for m in cnt}
            for m in cnt: cnt[m][mm[m]] += 1
            if mm["delay"] == "R" and mm["cf"] == "R": both.append((c, r))
            Rs += [f"{r}({m})" for m in cnt if mm[m] == "R"]
            ties = [m for m in ("delay", "cf") if mm[m] == "="]
        print(a, c, "R:", Rs)
    print(a, "counts", {m: dict(v) for m, v in cnt.items()}, "both-R", both)
# ranges
c = "X1|5300"
rules = [r for r in M[c]["rules"] if r != "nc"]
for m in ("delay", "cf", "flow"):
    vals = sorted((M[c]["eff"][f"v3w|{r}|{m}"][0], r) for r in rules)
    print("X1 v3w vs rules", m, "min", vals[0], "max", vals[-1])
