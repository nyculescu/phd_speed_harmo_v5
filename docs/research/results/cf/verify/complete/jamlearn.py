import json, numpy as np, collections
D = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/2d269ac5-95be-4f04-801b-ec9cc9873355/scratchpad/cfv/complete/"
res = json.load(open(D + "jams_all.json")); T = collections.defaultdict(dict); G = collections.defaultdict(lambda: collections.defaultdict(dict))
for n, s, j, heads, *_ in res:
    n = n.split("|", 1)[1]; T[n][s] = j
    for g in ("event", "merge1", "merge2", "between"): G[n][g][s] = heads.get(g, 0)
seeds = sorted(T["p333"])
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
for opp in ("p333", "lr400_16_1", "3E-C_TRUCK"):
    R = np.array([T[opp][s] for s in seeds])
    print(opp, "per learner mean(v3w - rule) jams/run:", [round(float(np.mean([T[w][s] for s in seeds]) - R.mean()), 2) for w in V3W],
          "| by head group, v3w mean - rule:", {g: round(float(np.mean([[G[w][g][s] for s in seeds] for w in V3W]) - np.mean([G[opp][g][s] for s in seeds])), 2) for g in ("event", "merge1", "merge2", "between")})
