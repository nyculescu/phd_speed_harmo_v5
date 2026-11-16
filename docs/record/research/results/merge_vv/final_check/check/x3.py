# Wall time per arm from the stored rows, to check the cost line's use of CF's all-arm rate; also the keys an identity check must exclude.
import json, collections, statistics as st
src = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
w = collections.defaultdict(list); N = collections.defaultdict(list); first = None
with open(src) as f:
    for line in f:
        r = json.loads(line)
        if first is None: first = {k: (v if not isinstance(v, (dict, list)) else type(v).__name__) for k, v in r.items() if k in ("wall_s", "files", "commit", "c1_t0", "pert_log", "cell_spec", "ctrl_sha256", "arm", "cell", "learner", "steps")}; first["c1_t0_full"] = r.get("c1_t0")
        w[r["name"].split("|")[1]].append(r["wall_s"]); N[r["name"].split("|")[1]].append(r["N"])
vv = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500", "lr400_16_1", "grid_lr400_13_1", "p333", "nc"]
tot = sum(sum(v) for v in w.values()); n = sum(len(v) for v in w.values())
print("all arms: runs %d, sum wall %.0f h, mean wall %.1f s/run -> runs per hour on 30 workers if wall adds up: %.0f" % (n, tot / 3600, tot / n, 30 * 3600 / (tot / n)))
tv = sum(sum(w[a]) for a in vv); nv = sum(len(w[a]) for a in vv)
print("VV's 9 arms: mean wall %.1f s/run (ratio to all-arm mean %.3f)" % (tv / nv, (tv / nv) / (tot / n)))
for a in vv: print("  %-18s mean wall %.1f s, mean N (vehicle-seconds at 1 Hz) %.0f" % (a, st.mean(w[a]), st.mean(N[a])))
print("first row meta:", first)
