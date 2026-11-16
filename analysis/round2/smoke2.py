"""Round 2 smoke (round_2.md, check 5): one run per arm kind on the smoke seed, traced and untraced in separate processes. The traced row
must equal the untraced row on every key but name and cfg (V386), and the trace must show that the run carries its inputs. Imports only
v5b2, so it runs inside any snapshot. usage: smoke2.py JOB_JSON OUT_JSON WORKERS"""
import json
import multiprocessing as mp
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor

import numpy as np

SKIP = {"name", "cfg"}


def run(a: tuple):
    """(kind, trace, name, cfg, q, seed, rd, extra) -> (row, trace summary)."""
    kind, trace, name, cfg, q, seed, rd, extra = a
    import torch
    from v5b2.freeway import environments as be, train_per_cav as ct, evaluate as ps
    torch.set_num_threads(1)
    info = defaultdict(Counter)
    obs = []
    if trace and kind == "sw":
        call = ct.ZoneSwitch.__call__
        ind_rule, ind_pol = be.OwnState(**extra["own_state"]), ct.Greedy(extra["pt"])

        def sw_call(self, o):
            ids, lo, g, due = o
            up = lo[:, 0] * 1000.0 < self.x_from
            r_rule, r_pol = ind_rule(o), ind_pol((ids, lo, g, due & ~up))     # built independently of the arm's own objects
            out = call(self, o)
            for v, u in zip(ids, up):
                if v in out:
                    side = "up" if u else "down"
                    info["side"][side] += 1
                    info[f"from_own_{side}"][int(out[v] == (r_rule if u else r_pol).get(v))] += 1
            return out
        ct.ZoneSwitch.__call__ = sw_call
    if trace and kind == "3e":
        call3 = be.ZoneOwnState.__call__

        def z_call(self, o):
            out = call3(self, o)
            z = be.zone_of_3e(o[1][:, 0] * 1000.0, o[1][:, 2])
            lo, P = o[1], extra["zones"]     # the rule written out by hand from 3E's definition
            for k, (v, zi) in enumerate(zip(o[0], z)):
                p = P[int(zi)]
                want = p["level"] if (lo[k, 4] * (100.0 / 3.6) < p["th"] and lo[k, 15] * 40.0 >= p["crowd"]) else p["free"]
                info["zone"][int(zi)] += 1
                info["own_value"][int(out[v] == want)] += 1
            return out
        be.ZoneOwnState.__call__ = z_call
    if trace and kind == "tail":
        callt = ct.TailMean.__call__
        ref = ct.Greedy(extra["u500"])

        def t_call(self, o):
            out = callt(self, o)
            g = ref(o)
            for v in out:
                info["differs_from_u500"][int(out[v] != g[v])] += 1
            if o[3].any() and len(obs) < 1000:
                obs.append(o[1][o[3]].copy())
            return out
        ct.TailMean.__call__ = t_call
    if trace and kind == "ahead":
        callg = ct.Greedy.__call__

        def g_call(self, o):
            if o[3].any():
                obs.append(o[1][o[3]].copy())
            return callg(self, o)
        ct.Greedy.__call__ = g_call
    if trace and kind == "1b":
        apply0 = be.CavEnv._apply

        def apply(self, action):
            n0 = len(getattr(self, "masked", ()))
            apply0(self, action)
            info["decisions"]["n"] += len(action)
            info["masked"]["n"] += len(getattr(self, "masked", ())) - n0
        be.CavEnv._apply = apply
    row = ps.run_one((name, cfg, q, seed, rd))
    summ = {k: dict(v) for k, v in info.items()}
    if obs:
        X = np.concatenate(obs)
        summ["n_inputs"] = int(X.shape[1])
        if kind == "ahead":
            summ["ahead_sd"] = [float(X[:, j].std()) for j in extra["cols"]]
            summ["ahead_share_1"] = [float((X[:, j] == 1.0).mean()) for j in extra["cols"]]
        if kind == "tail":
            np.save(extra["obs_out"], X[:1000])
    return row, summ


def main(job_f: str, out_f: str, workers: int) -> int:
    job = json.load(open(job_f))
    args = [(j["kind"], t, j["name"], j["cfg"], j["q"], j["seed"], job["rd"], j.get("extra", {})) for j in job["runs"] for t in (False, True)]
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        res = list(ex.map(run, args))
    out, ok = {}, True
    for k in range(0, len(res), 2):
        (plain, _), (tr, summ) = res[k], res[k + 1]
        j = job["runs"][k // 2]
        diff = [x for x in plain if x not in SKIP and json.loads(json.dumps(tr)).get(x) != json.loads(json.dumps(plain))[x]]
        out[j["name"]] = {"kind": j["kind"], "traced_equals_untraced": not diff, "differing": diff[:8], "trace": summ}
        ok &= not diff
    json.dump(out, open(out_f, "w"), indent=1)
    print(json.dumps(out)[:2000], flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], int(sys.argv[3])))
