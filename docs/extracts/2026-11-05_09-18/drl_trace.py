"""For the teaching page: what one stored policy sees, does and earns on a used seed. Not a result. usage: drl_trace.py cond out.json"""
import json
import sys
from collections import defaultdict

import libsumo as ls
import numpy as np
import torch

sys.path.insert(0, "docs/research/conf3")
from common import COND, PLANT
from v5b.fleet import b_env as be, c_train as ct, plant_sweep as ps

SEED, GAMMA, LAM = 7_419_640, 0.933, 0.967
POL = "docs/research/phase3/shot_policies/C1_final.pt"
REF = json.load(open("/home/catalin/work/phd/v5b1_runs/conf3/smoke_env.json"))["plant"]["ref"]


def x_road(env, v):
    """_x writes xlast, which the observation reads inside a junction; restore it so that tracing does not change the run."""
    had, old = v in env.xlast, env.xlast.get(v)
    x = float(env._x(v))
    if had:
        env.xlast[v] = old
    else:
        env.xlast.pop(v, None)
    return x


if __name__ == "__main__":
    cond, out = sys.argv[1], sys.argv[2]
    torch.set_num_threads(1)
    plant = {**ps.to_plant(PLANT), "ref": REF}
    kw = {"cav": True, "decision": 5.0, "hold": 10.0, "alks_asl": 0.5, "ref_delay": True, "share": 0.5, "levels": (5300.0,), "seeds": [SEED], "run_dir": "/home/catalin/work/phd/v5b1_runs/phase3/scratch/drl/rd", "report_net": True, "plant": plant,
          "w_flow": 0.4, "w_safety": 10.0}
    if COND[cond]:
        kw["perturb"] = COND[cond]
    env = be.make(**kw)
    ck = torch.load(POL, map_location="cpu")
    net = ct.Net(ck["n_local"], ck["n_act"])
    net.load_state_dict(ck["net"])
    scale = ck["scale"]
    params = {"actor": sum(p.numel() for p in net.actor.parameters()), "critic": sum(p.numel() for p in net.critic.parameters()), "scale": scale}
    o, _ = env.reset()
    tr, done = {}, []
    sec_rows = defaultdict(list)
    terms = defaultdict(float)
    per_road = defaultdict(lambda: [0.0, 0.0, 0.0])
    heat = defaultdict(lambda: [0.0, 0.0])
    examples = []
    sec0 = env._second

    def sec():
        r = sec0()
        t = env.sim.t
        for v, (sp, near, q, ttc, ft, fh, hard) in env.stats.items():
            if v not in env.alks_all:
                continue
            try:
                road = ls.vehicle.getRoadID(v)
                a = ls.vehicle.getAcceleration(v)
                tau = ls.vehicle.getTau(v)
            except Exception:
                continue
            own, nr, fl = be.W_CAV_OWN * (min(sp / be.fl.LIMIT, 1.0) - 1.0), be.W_CAV_NEAR * (min(near / be.fl.LIMIT, 1.0) - 1.0), env.w_flow * min(q / be.Q_REF, 1.5)
            safe = -env.w_safety * (ttc + hard + 0.5 * (ft + fh))
            terms["own"] += own; terms["near"] += nr; terms["flow"] += fl; terms["safety"] += safe; terms["n"] += 1
            terms["ttc_s"] += ttc; terms["hard_s"] += hard; terms["fol_s"] += 0.5 * (ft + fh)
            terms["on_s"] += v in env.on
            sec_rows[v].append((round(t), round(x_road(env, v), 1), round(sp, 2), round(a, 2), round(tau, 2), env.lvl.get(v, 0), int(v in env.on), round(near, 2), round(q, 3), int(ttc), int(hard), ft + fh, road))
            if not road.startswith(":"):
                pr = per_road[road]
                pr[0] += env.lvl.get(v, 0); pr[1] += 1; pr[2] += v in env.on
        terms["shared_flow"] += env.flow_ema / (env.q / 3600.0) - 1.0
        live = ls.vehicle.getIDList()
        terms["shared_speed"] += (sum(ls.vehicle.getSpeed(x) for x in live) / max(len(live), 1)) / be.fl.LIMIT - 1.0
        terms["shared_n"] += -env.w_n * ((len(live) + len(ls.simulation.getPendingVehicles())) / env._ref()[2] - 1.0)
        terms["secs"] += 1
        return r

    env._second = sec
    while True:
        ids, lo, gl, due = o
        act = {}
        if due.any():
            tl = torch.from_numpy(lo[due])
            tg = torch.from_numpy(np.repeat(gl[None], int(due.sum()), 0))
            with torch.no_grad():
                p = torch.softmax(net.actor(tl), 1).numpy()
                val = net.value(tl, tg).numpy() * scale
            a = p.argmax(1)
            for v, row, pr, ai, va in zip((x for x, d in zip(ids, due) if d), lo[due], p, a, val):
                act[v] = int(ai)
                t = tr.setdefault(v, {"t": [], "lo": [], "p": [], "a": [], "v": [], "r": [], "k": []})
                if t["r"] and t["k"][-1]:
                    t["r"][-1] /= t["k"][-1]
                t["t"].append(round(env.sim.t)); t["lo"].append([round(float(x), 3) for x in row]); t["p"].append([round(float(x), 3) for x in pr]); t["a"].append(int(ai)); t["v"].append(round(float(va), 3)); t["r"].append(0.0); t["k"].append(0)
                xb, sb = int(np.floor(float(row[0]) * 1000.0 / 100.0)), int(float(row[4]) * be.fl.LIMIT // 2)
                h = heat[(xb, sb)]
                h[0] += float(ai); h[1] += 1
        ids0 = set(ids)
        o2, rew, _, trunc, info = env.step(act)
        for v, x in rew.items():
            t = tr.get(v)
            if t is not None:
                t["r"][-1] += x
                t["k"][-1] += 1
        o = o2
        if trunc:
            break
    glob_last = o[2]
    env.close()
    res = {"cond": cond, "seed": SEED, "params": params, "terms": dict(terms), "per_road": {k: v for k, v in per_road.items()}, "heat": [[k[0], k[1], v[0] / v[1], v[1]] for k, v in heat.items()], "ep": {k: info["ep"][k] for k in ("passed", "alks_s", "v2v_s", "changes", "reversals", "ignored", "commands")}, "lv": info["ep"].get("lv")}
    # long trips through both merges, with their full decision history
    best = []
    for v, t in tr.items():
        rows = sec_rows.get(v, [])
        if v in env.ramp or len(t["t"]) < 12 or not rows or rows[0][1] > -3000 or rows[-1][1] < 2900:
            continue
        r = list(t["r"])
        if t["k"][-1]:
            r[-1] /= t["k"][-1]
        rr, vv = np.array(r, dtype=np.float32), np.array(t["v"], dtype=np.float32)
        adv = ct.gae(rr, vv, float(vv[-1]), GAMMA, LAM)
        best.append({"v": v, "n_moves": int(np.sum(np.diff(t["a"]) != 0)), "t": t["t"], "lo": t["lo"], "p": t["p"], "a": t["a"], "value": t["v"], "r": [round(float(x), 3) for x in rr], "adv": [round(float(x), 3) for x in adv], "sec": rows})
    best.sort(key=lambda b: (-b["n_moves"], b["t"][0]))
    res["trips"] = best[:12]
    res["n_trips"] = len(best)
    json.dump(res, open(out, "w"))
    print("done", len(best), params, flush=True)
