import json, re
M = json.load(open("mine.json"))
TAB = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/map_all/tables.md"
NM = {"no control": "nc", "3E-T": "3e", "3E-X1": "3ex1", "3E-X2": "3ex2", "v3w (arm)": "v3w", "tail (arm)": "tail", "sw (arm)": "sw"}
sec3 = False; cell = None; n = bad = 0
for line in open(TAB):
    if line.startswith("## (3)"): sec3 = True
    if line.startswith("## (4)"): sec3 = False
    if not sec3: continue
    h = re.match(r"### (X1|X2) at 5,300", line) or re.match(r"### B at ([\d,]+) veh/h", line)
    if h:
        g = h.group(1)
        cell = f"{g}|5300" if g in ("X1", "X2") else f"B|{g.replace(',', '')}"; continue
    p = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(p) == 8 and p[0] in NM or (len(p) == 8 and p[0] in M.get(cell, {}).get("med", {})):
        nm = NM.get(p[0], p[0])
        for m, s in zip(("delay", "cf", "flow", "b3", "b45"), p[1:6]):
            n += 1
            mine = M[cell]["med"][nm][m]
            if abs(mine - float(s)) > (0.6 if m == "delay" else 0.06):
                bad += 1; print("DIFF", cell, nm, m, s, mine)
print("median cells", n, "mismatch", bad)
