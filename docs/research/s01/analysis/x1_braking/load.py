"""Caches the measured test rows (without cfg) and the round-2 stored rows as pickles; prints only aggregates."""
import json
import pickle
from pathlib import Path

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
R2 = Path("/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl")
OUT = Path(__file__).resolve().parent

T = {}
for line in open(D / "rows_test.jsonl"):
    r = json.loads(line)
    r.pop("cfg", None)
    T[(r["name"], r["seed"])] = r
S = {}
for line in open(R2):
    r = json.loads(line)
    r.pop("cfg", None)
    S[(r["name"], r["seed"])] = r
pickle.dump(T, open(OUT / "test_rows.pkl", "wb"))
pickle.dump(S, open(OUT / "r2_rows.pkl", "wb"))
print("measured", len(T), "stored", len(S), "common", len(set(T) & set(S)))
print("qs", sorted({r["q"] for r in T.values()}))
