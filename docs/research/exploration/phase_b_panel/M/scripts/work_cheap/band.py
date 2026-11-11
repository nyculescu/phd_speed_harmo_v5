"""EXPLORATORY: band rows (read-only): is the band steady, and what p333 shows by level."""
import json
import numpy as np
P = '/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl'
T = {}; cfg = {}; pert = {}
for line in open(P):
    r = json.loads(line)
    n = r["name"].split("|", 1)[1]
    if n not in ("p333", "nc", "os1_15_10", "3e"):
        continue
    cfg[n] = json.dumps(r["cfg"].get("ctrl"))[:260]
    pl = r.get("pert_log")
    pert.setdefault(n, []).append(json.dumps(pl)[:120] if pl is not None else None)
    T.setdefault((n, r["q"]), {})[r["seed"]] = {k: r.get(k) for k in ("all_delay", "end_stop2", "end_stop", "delay_ramp2", "finished_pct", "passed", "m_planned_window", "tau_on_n", "tau_on_match", "tau_mismatch")}
    keys = sorted(r)
for n in cfg:
    print(n, cfg[n]); print("   pert_log sample:", pert[n][:2])
print("keys with pend/queue/road:", [k for k in keys if "pend" in k or "queue" in k or "road" in k or "ins" in k][:40])
for q in sorted({q for _, q in T}):
    s = sorted(T[("p333", q)])
    a = lambda n, k: np.array([T[(n, q)][x][k] for x in s], float)
    d = (a("p333", "all_delay") - a("os1_15_10", "all_delay")) / np.median(a("p333", "all_delay")) * 100
    dn = (a("p333", "all_delay") - a("nc", "all_delay")) / np.median(a("p333", "all_delay")) * 100
    print(q, "seeds", s[0], s[-1], len(s), "p333 all_delay med %.0f; end_stop2 med %.1f; finished %% med %.1f; os1_15_10 vs p333 %% med %+.2f sd %.2f; nc vs p333 med %+.1f sd %.1f" % (np.median(a("p333", "all_delay")), np.median(a("p333", "end_stop2")), np.median(a("p333", "finished_pct")), np.median(d), d.std(ddof=1), np.median(dn), dn.std(ddof=1)))
