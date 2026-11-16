"""Stream the confirmation rows into a flat table of scalars (read only)."""
import json, sys
import pandas as pd
src, out = sys.argv[1], sys.argv[2]
recs = []
for line in open(src):
    r = json.loads(line)
    d = {"arm": r["name"].split("|", 1)[1], "seed": r["seed"]}
    for k, v in r.items():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            d[k] = float(v)
    for key in ("m_road_ttc3", "m_road_vs", "m_road_dist", "m_road_ge45"):
        for road, x in (r.get(key) or {}).items():
            d[f"{key}|{road}"] = float(sum(x.values()) if isinstance(x, dict) else x)
            if isinstance(x, dict):
                for per, y in x.items():
                    d[f"{key}|{road}|{per}"] = float(y)
    recs.append(d)
df = pd.DataFrame(recs).fillna(0.0)
df.to_parquet(out) if out.endswith(".parquet") else df.to_pickle(out)
print(df.shape)
