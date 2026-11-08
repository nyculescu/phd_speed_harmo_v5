"""Compact copy of the fields this verification uses (read only from the data folder)."""
import json, pickle, sys
from pathlib import Path
D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(__file__).parent / "rows.pkl"
KEEP_PREFIX = ("m_dec_", "ttc3", "lv", "tau_", "sev3")
KEEP = {"name", "q", "seed", "all_delay", "ttc_net", "passed", "N", "m_st_file", "m_n_alks", "collisions", "teleports", "pert_log", "E30", "out_E30"}
rows = []
for f in ("rows_test.jsonl", "rows_band.jsonl", "rows_s1.jsonl"):
    for line in open(D / f):
        r = json.loads(line)
        rows.append({k: v for k, v in r.items() if k in KEEP or k.startswith(KEEP_PREFIX)} | {"src": f})
pickle.dump(rows, open(OUT, "wb"))
print(len(rows))
