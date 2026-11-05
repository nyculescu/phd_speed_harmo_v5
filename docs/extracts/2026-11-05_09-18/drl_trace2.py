"""For the teaching page: per-decision rows of a stored policy, and the reward terms of fixed levels on the same seed. Not a result. usage: drl_trace2.py cond arm out_prefix"""
import json
import sys
from collections import defaultdict

import libsumo as ls
import numpy as np
import torch

sys.path.insert(0, "docs/research/conf3")
from common import COND, PLANT
from v5b.fleet import b_env as be, c_train as ct, plant_sweep as ps

SEED = 7_419_640
POL = "docs/research/phase3/shot_policies/C1_final.pt"
REF = json.load(open("/home/catalin/work/phd/v5b1_runs/conf3/smoke_env.json"))["plant"]["ref"]

if __name__ == "__main__":
    cond, arm, out = sys.argv[1], sys.argv[2], sys.argv[3]
    torch.set_num_threads(1)
    plant = {**ps.to_plant(PLANT), "ref": REF}
    kw = {"cav": True, "decision": 5.0, "hold": 10.0, "alks_asl": 0.5, "ref_delay": True, "share": 0.5, "levels": (5300.0,), "seeds": [SEED], "run_dir": f"/home/catalin/work/phd/v5b1_runs/phase3/scratch/drl/rd/{cond}_{arm}", "report_net": True, "plant": plant,
          "w_flow": 0.4, "w_safety": 10.0}
    if COND[cond]:
        kw["perturb"] = COND[cond]
    env = be.make(**kw)
    ck = torch.load(POL, map_location="cpu")
    net = ct.Net(ck["n_local"], ck["n_act"])
    net.load_state_dict(ck["net"])
    scale = ck["scale"]
    o, _ = env.reset()
    terms = defaultdict(float)
    cur = {}
    sec0 = env._second

    def sec():
        c0 = env.ep["collisions"]
        r = sec0()
        new_c = env.ep["collisions"] - c0
        n = 0
        for v, (sp, near, q, ttc, ft, fh, hard) in env.stats.items():
            if v not in env.alks_all:
                continue
            own, nr, fl = be.W_CAV_OWN * (min(sp / be.fl.LIMIT, 1.0) - 1.0), be.W_CAV_NEAR * (min(near / be.fl.LIMIT, 1.0) - 1.0), env.w_flow * min(q / be.Q_REF, 1.5)
            saf = ttc + hard + 0.5 * (ft + fh)
            terms["own"] += own; terms["near"] += nr; terms["flow"] += fl; terms["safety"] += saf; terms["n"] += 1
            terms["ttc_s"] += ttc; terms["hard_s"] += hard; terms["fol_s"] += 0.5 * (ft + fh)
            c = cur.get(v)
            if c is not None:
                c[0] += own; c[1] += nr; c[2] += fl; c[3] += -env.w_safety * saf; c[4] += 1
            n += 1
        live = ls.vehicle.getIDList()
        terms["sh_flow"] += n * (env.flow_ema / (env.q / 3600.0) - 1.0)
        terms["sh_speed"] += n * ((sum(ls.vehicle.getSpeed(x) for x in live) / max(len(live), 1)) / be.fl.LIMIT - 1.0)
        terms["sh_n"] += n * (-env.w_n * ((len(live) + len(ls.simulation.getPendingVehicles())) / env._ref()[2] - 1.0))
        terms["coll"] += n * new_c
        return r

    env._second = sec
    rows = []
    open_row = {}
    rsum = defaultdict(lambda: [0.0, 0])

    def close(v):
        k = open_row.pop(v, None)
        if k is None:
            return
        c, rs = cur.pop(v), rsum.pop(v, [0.0, 0])
        n = max(c[4], 1)
        rows[k][-6:] = [rs[0] / max(rs[1], 1), c[0] / n, c[1] / n, c[2] / n, c[3] / n, c[4]]

    while True:
        ids, lo, gl, due = o
        act = {}
        if due.any():
            names = [x for x, d in zip(ids, due) if d]
            if arm == "policy":
                tl = torch.from_numpy(lo[due])
                tg = torch.from_numpy(np.repeat(gl[None], int(due.sum()), 0))
                with torch.no_grad():
                    p = torch.softmax(net.actor(tl), 1).numpy()
                    val = net.value(tl, tg).numpy() * scale
                a = p.argmax(1)
                for v, row, pr, ai, va in zip(names, lo[due], p, a, val):
                    close(v)
                    act[v] = int(ai)
                    open_row[v] = len(rows)
                    cur[v] = [0.0, 0.0, 0.0, 0.0, 0]
                    rows.append([round(env.sim.t), int(v.split(".")[-1]), int(v in env.ramp)] + row.tolist() + gl.tolist() + pr.tolist() + [int(ai), float(va), 0.0, 0.0, 0.0, 0.0, 0.0, 0])
            else:
                act = {v: int(arm) for v in names}
        o2, rew, _, trunc, info = env.step(act)
        for v, x in rew.items():
            if v in open_row:
                rsum[v][0] += x
                rsum[v][1] += 1
        o = o2
        if trunc:
            break
    for v in list(open_row):
        close(v)
    ep = info["ep"]
    env.close()
    res = {"cond": cond, "arm": arm, "seed": SEED, "terms": dict(terms), "ep": {k: ep[k] for k in ("passed", "arrived", "N", "E30", "out_E30", "brake3", "out_b3", "collisions", "alks_s", "v2v_s", "changes", "reversals", "mean_v")}, "lv": ep.get("lv")}
    json.dump(res, open(out + ".json", "w"))
    if rows:
        np.save(out + ".npy", np.array(rows, dtype=np.float32))
    print("done", cond, arm, len(rows), res["ep"]["passed"], flush=True)
