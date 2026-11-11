"""EXPLORATORY: is the imposed slowdown the same event in every arm of a seed? Round 2 test rows, X1 and X2. Summary only."""
import pickle, json, collections
A2 = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit2/"
T = pickle.load(open(A2 + "r2t.pkl", "rb"))
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
for cell in ("X1", "X2"):
    seeds = sorted(T[(cell, "p333")])
    p0 = T[(cell, "p333")][seeds[0]]["pert"]
    print(cell, "type", type(p0).__name__, "len", len(p0) if hasattr(p0, "__len__") else None)
    ev = p0[0] if isinstance(p0, list) and p0 else p0
    print("  fields of one event:", sorted(ev) if isinstance(ev, dict) else type(ev).__name__, "| cell_spec keys:", sorted((T[(cell, "p333")][seeds[0]].get("cell_spec") or {})))
    keys = sorted(ev) if isinstance(ev, dict) else []
    for arm in ["nc", "os0_10_10"] + L:
        if (cell, arm) not in T:
            continue
        same = collections.Counter(); n_ev = []
        for s in seeds:
            a, b = T[(cell, "p333")][s]["pert"], T[(cell, arm)][s]["pert"]
            n_ev.append((len(a), len(b)))
            same["whole log equal"] += json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
            for k in keys:
                va = [e.get(k) for e in a] if isinstance(a, list) else None; vb = [e.get(k) for e in b] if isinstance(b, list) else None
                same[k] += va == vb
        print(f"  {cell} {arm:10s} against p333, seeds with equal value of {len(seeds)}: " + ", ".join(f"{k} {v}" for k, v in same.items()) + f" | events per run p333/arm: {collections.Counter(n_ev).most_common(3)}")
