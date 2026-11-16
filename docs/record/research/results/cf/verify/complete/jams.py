"""Jam count per (arm, seed) from stored CF space-time files, with C1's helper (read_c1.jams_of); no simulation."""
import json, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, "/home/catalin/work/phd/wt/c1c/docs/research/c1")
import read_c1
ROWS = Path("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl")
ST = Path("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/st")
KEEP = ("name", "seed", "m_st_file", "m_st_dt", "m_st_dx", "m_offsets", "steps")
def one(r):
    try:
        j, heads, vs = read_c1.jams_of(r, ST)
        return r["name"], r["seed"], j, heads, vs, None
    except BaseException as e:
        return r["name"], r["seed"], None, {}, None, repr(e)[:200]
if __name__ == "__main__":
    lim = int(sys.argv[1]); out = sys.argv[2]
    rows = []
    with ROWS.open() as f:
        for i, line in enumerate(f):
            if i >= lim: break
            rows.append(json.loads(line))
    t = time.time()
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(one, rows, chunksize=20))
    del rows
    json.dump(res, open(out, "w"))
    print(len(res), "rows", round(time.time() - t, 1), "s; errors", sum(1 for x in res if x[5]), [x[5] for x in res if x[5]][:3])
