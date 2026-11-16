import json
M = json.load(open("mine.json"))
order = ["X1|5300", "X2|5300", "B|3500", "B|4500", "B|5000", "B|5250", "B|5500", "B|6000", "B|7000"]
def dom(a, b):  # a dominates b (minimise both)
    return a[0] <= b[0] and a[1] <= b[1] and (a[0] < b[0] or a[1] < b[1])
for c in order:
    md = M[c]["med"]; rules = M[c]["rules"]
    for incl in (False, True):
        rs = [r for r in rules if incl or r != "nc"]
        pts = {r: (md[r]["delay"], md[r]["cf"]) for r in rs}
        fr = [r for r in rs if not any(dom(pts[o], pts[r]) for o in rs if o != r)]
        if incl: continue
        print(c, "front(rules only):", fr)
        for a in M[c]["arms"]:
            p = (md[a]["delay"], md[a]["cf"])
            by = [r for r in rs if dom(pts[r], p)]
            over = [r for r in fr if dom(p, pts[r])]
            pos = "inside" if by else ("beyond" if over else "on")
            # paired: rule - arm medians
            pby = [r for r in rs if (M[c]["pmed"][f"{a}|{r}|delay"] <= 0 and M[c]["pmed"][f"{a}|{r}|cf"] <= 0 and (M[c]["pmed"][f"{a}|{r}|delay"] < 0 or M[c]["pmed"][f"{a}|{r}|cf"] < 0))]
            pover = [r for r in fr if (M[c]["pmed"][f"{a}|{r}|delay"] >= 0 and M[c]["pmed"][f"{a}|{r}|cf"] >= 0 and (M[c]["pmed"][f"{a}|{r}|delay"] > 0 or M[c]["pmed"][f"{a}|{r}|cf"] > 0))]
            ppos = "inside" if pby else ("beyond" if pover else "on")
            print(f"   {a}: point {pos} by={by} over={over} | paired {ppos} by={pby} over={pover} | med d={p[0]:.0f} cf={p[1]:.1f}")
    # best rule per metric
    best = {}
    for m in ("delay", "cf", "flow", "b3", "b45"):
        f = max if m == "flow" else min
        rr = [r for r in rules if r != "nc"]
        b1 = f(rules, key=lambda r: md[r][m]); b2 = f(rr, key=lambda r: md[r][m])
        ties = [r for r in rr if md[r][m] == md[b2][m]]
        best[m] = (b1, round(md[b1][m], 1), ties, round(md[b2][m], 1))
    print("   best:", best)
    print("   rule meds:", {r: (round(md[r]["delay"]), round(md[r]["cf"], 1)) for r in rules})
