"""Independent loader: read every per-run JSON of seeds 7400200-239 (tuning) and 7400500-599 (eval); keep a slim
record indexed by the spec fields stored INSIDE the file (not the filename); check the filename agrees."""
import json, os, sys, pickle
from multiprocessing import Pool
RUNS = "/home/catalin/work/phd/v5b1_runs/p1/v99/runs"
F = ("pre", "post", "back", "incident", "q", "seed", "k", "d", "c", "fa", "vsl_b", "rep", "delay_s", "valid",
     "teleports", "served_ctrl_vph", "max_queue", "hash", "t_on", "t_off", "t_switch", "t_back", "onset_s",
     "duration_s", "fa_time_s", "sumo_seed", "demand_seed", "drained", "generated", "n_trips", "signal", "code_commit", "key", "ttt_ctrl_vehh")

def want(fn):
    s = int(fn.split("_s")[-1].split("_")[0].split(".")[0]) if "_s74" in fn else None
    return s is not None and (7400200 <= s <= 7400239 or 7400500 <= s <= 7400599)

def load(fn):
    with open(os.path.join(RUNS, fn)) as f:
        r = json.load(f)
    out = {k: r.get(k) for k in F}
    out["_fn"] = fn[:-5]
    return out

if __name__ == "__main__":
    fns = [f for f in os.listdir(RUNS) if f.endswith(".json")]
    sel = [f for f in fns if want(f)]
    print("files", len(fns), "selected", len(sel), file=sys.stderr)
    with Pool(8) as p:
        recs = p.map(load, sel, chunksize=500)
    bad = [r["_fn"] for r in recs if r["key"] != r["_fn"]]
    print("key!=filename", len(bad), bad[:5], file=sys.stderr)
    pickle.dump(recs, open(sys.argv[1], "wb"))
