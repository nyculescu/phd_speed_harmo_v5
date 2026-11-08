import json, re
M = json.load(open("mine.json"))
TAB = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/map_all/tables.md"
NM = {"no control": "nc", "3E-T": "3e", "3E-X1": "3ex1", "3E-X2": "3ex2"}
MS = ["delay", "cf", "flow", "b3", "b45"]
num = lambda s: float(s.replace("−", "-").replace("+", ""))
pat = re.compile(r"^\s*([+−]?[\d.]+) \[([+−]?[\d.]+), ([+−]?[\d.]+)\] ([AR=])\s*$")
def mark(lo, hi):
    return "A" if lo > 0 else ("R" if hi < 0 else "=")
cell = arm = None
n = bad = 0
fragile = []
for line in open(TAB):
    h = re.match(r"### (X1|X2): (v3w|tail|sw) against", line)
    if h:
        cell, arm = f"{h.group(1)}|5300", h.group(2); continue
    h = re.match(r"### B at ([\d,]+) veh/h", line)
    if h and "(3)" not in line:
        cell, arm = f"B|{h.group(1).replace(',', '')}", None; continue
    if line.startswith("## (3)"):
        cell = None
    if cell is None or not line.startswith("| ") or "---" in line:
        continue
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    if parts[0] in ("Opponent", "Arm"):
        continue
    if arm is None:
        if len(parts) != 7: continue
        a, opp, vals = parts[0], parts[1], parts[2:]
    else:
        if len(parts) != 6: continue
        a, opp, vals = arm, parts[0], parts[1:]
    r = NM.get(opp, opp)
    for m, s in zip(MS, vals):
        g = pat.match(s)
        if not g:
            print("noparse", cell, a, opp, m, s); continue
        e, lo, hi, mk = num(g.group(1)), num(g.group(2)), num(g.group(3)), g.group(4)
        k = f"{a}|{r}|{m}"
        if k not in M[cell]["eff"]:
            print("MISSING in mine", cell, k); bad += 1; continue
        me = M[cell]["eff"][k]
        mm = mark(me[1], me[2])
        n += 1
        ok = all(abs(round(x, 1) - y) < 0.051 for x, y in zip(me, (e, lo, hi))) and mm == mk
        if not ok:
            bad += 1
            print("DIFF", cell, k, "theirs", e, lo, hi, mk, "mine", [round(x, 2) for x in me], mm)
        alt = [mark(x[1], x[2]) for x in M[cell]["eff_alt"][k]]
        if any(x != mm for x in alt):
            fragile.append((cell, k, [round(x, 3) for x in me], mm, alt))
print("cells compared", n, "mismatches", bad)
# coverage: did they report every pair I have?
tot = sum(len(M[c]["eff"]) for c in M)
print("my total CIs", tot)
print("fragile (mark changes under rng seeds 1,2,3):", len(fragile))
for f in fragile:
    if f[1].startswith("v3w"): print("  ", f)
print("v3w fragile only above; tail/sw fragile count", sum(1 for f in fragile if not f[1].startswith("v3w")))
