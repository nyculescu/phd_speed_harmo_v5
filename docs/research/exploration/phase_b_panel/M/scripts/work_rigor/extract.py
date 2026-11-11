"""EXPLORATORY: scalar fields from stored S6 and band rows (read-only on the rows)."""
import json, pickle, sys
S6 = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
BAND = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl'
KEYS = ("all_delay", "passed", "N", "m_planned_window", "end_stop2", "ttc_net", "collisions", "m_pending_end", "finished_pct")
out = {"s6": {}, "band": {}}
for line in open(S6):
    r = json.loads(line)
    out["s6"].setdefault(r["name"], {})[r["seed"]] = [r.get(k) for k in KEYS]
for line in open(BAND):
    r = json.loads(line)
    out["band"].setdefault((r.get("name"), r.get("q")), {})[r["seed"]] = [r.get(k) for k in KEYS]
pickle.dump({"keys": KEYS, **out}, open(sys.argv[1], "wb"))
print("s6 arms", len(out["s6"]), "band arm-levels", len(out["band"]))
