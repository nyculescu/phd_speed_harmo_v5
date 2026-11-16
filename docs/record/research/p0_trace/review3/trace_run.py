"""One instrumented run_one call for the protocol review; reads SUMO state only. usage: trace_run.py NAME CTL COND SEED OUT"""
import collections as C
import json
import sys
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.fleet import b_env as be, plant_sweep as ps

REPO = Path("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
sys.path.insert(0, str(REPO / "docs/research/phase3"))
from runs import COND, H10  # noqa: E402

name, ctl, cond, seed, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), Path(sys.argv[5])
P0D = json.load(open(REPO / "docs/research/baseline_v2/plant_p0d.json"))
CTL = {"nc": {}, "p333": {"cav_rule": [3, 3, 3], "env": H10}}[ctl]
X = COND[cond]
cfg = {**P0D, "geom": "r2m3", "ctrl": {**CTL, "env": {**CTL.get("env", {}), **({"perturb": X} if X else {})}}}

SLOW, T0, DUR, TAPER = X["edge"], X["times"], X["dur"], X["taper"]
UP = {"4": "4a", "3": "3a"}[SLOW]
FREE = be.FREE_MAX_SPEED
V0 = 100.0 / 3.6
ENV = {"e": None}


def period(t):
    for t0 in T0:
        if t0 <= t < t0 + TAPER + 1:
            return "taper"
        if t0 + TAPER + 1 <= t <= t0 + DUR:
            return "hold"
        if t0 + DUR < t <= t0 + DUR + 120:
            return "post"
    return "calm"


def in_ttc_window(t):
    return 400 <= t < 500 or any(t0 <= t <= t0 + DUR + 120 for t0 in T0)


step_b = C.Counter()  # (period, class, threshold, phase) -> steps
cause_b = C.Counter()  # (period, class, threshold, cause) -> steps
cause_road = C.Counter()  # (period, class, road, cause) -> steps at 3 m/s²
full_ev = []
ttc_ph = C.Counter()  # (period, phase) -> count
ttc_rec = []
expo = C.Counter()  # (period, lane, speed bin, class) -> vehicle-s
tau_ev = []
tau_up_t, pend_tau, pend_ttc = {}, {}, {}
last_lead, lead_change = {}, {}
prev_a = {}
traces = {}
pick_done = set()
orig_set_tau = ls.vehicle.setTau


def cls_of(env, v):
    return "alks" if v in env.alks_all else env.dem.by_id[v].cls


def idm(s, gap, dv, tau, v0):
    """SUMO's IDM acceleration with this time gap; gap is bumper to bumper."""
    sstar = max(0.0, s * tau + s * dv / (2.0 * (2.6 * 4.5) ** 0.5)) + 2.5
    return 2.6 * (1.0 - (s / max(v0, 1e-6)) ** 4 - (sstar / max(gap, 1e-6)) ** 2)


def set_tau(v, x):
    env = ENV["e"]
    t = env.sim.t
    old = env.v2v_cur.get(v, be.ALKS_TAU0)
    if t > env.warm and x != old:
        s = ls.vehicle.getSpeed(v)
        lead = ls.vehicle.getLeader(v, 200.0)
        gap = lead[1] + ls.vehicle.getMinGap(v) if lead and lead[0] else None
        dv = s - ls.vehicle.getSpeed(lead[0]) if gap is not None else None
        v0 = ls.lane.getMaxSpeed(ls.vehicle.getLaneID(v)) if not ls.vehicle.getRoadID(v).startswith(":") else V0
        kind = "off" if x == be.ALKS_TAU0 and v not in env.on else ("up" if x > old else "down")
        why = None
        if kind == "off":
            why = "not_alks_lead" if env.v2v_lead.get(v) is None else "new_alks_lead"
        rec = {"t": round(t, 1), "per": period(t), "old": old, "new": x, "kind": kind, "why": why, "lane": ls.vehicle.getLaneID(v), "s": round(s, 2), "gap": None if gap is None else round(gap, 2), "dv": None if dv is None else round(dv, 2),
               "a0": round(ls.vehicle.getAcceleration(v), 2), "a_old": None if gap is None else round(idm(s, gap, dv, old, v0), 2), "a_new": None if gap is None else round(idm(s, gap, dv, x, v0), 2), "min_a": 0.0, "s1": None}
        tau_ev.append(rec)
        if x > old:
            tau_up_t[v] = t
            pend_tau[v] = (rec, t)
    orig_set_tau(v, x)


ls.vehicle.setTau = set_tau
orig_step = be.MergeEnv._sim_step


def patched_step(self):
    ENV["e"] = self
    orig_step(self)
    env, t = self, self.sim.t
    if t <= env.warm + 1e-9:
        return
    per, ph = period(t), int(round((t % 1.0) * 10)) % 10
    ids = ls.vehicle.getIDList()
    window = in_ttc_window(t)
    slow_v = env.pert.slow_v
    for v in ids:
        a = ls.vehicle.getAcceleration(v)
        if v in pend_tau:
            rec, t1 = pend_tau[v]
            rec["min_a"] = min(rec["min_a"], round(a, 2))
            if t - t1 >= 1.0 - 1e-6:
                rec["s1"] = round(ls.vehicle.getSpeed(v), 2)
                del pend_tau[v]
        if v in pend_ttc:
            for i, tend in pend_ttc[v]:
                ttc_rec[i]["min_a2"] = min(ttc_rec[i]["min_a2"], round(a, 2))
            pend_ttc[v] = [x for x in pend_ttc[v] if x[1] > t]
            if not pend_ttc[v]:
                del pend_ttc[v]
        if a <= -3.0:
            cl = cls_of(env, v)
            s, road = ls.vehicle.getSpeed(v), ls.vehicle.getRoadID(v)
            if cl == "alks" and t - tau_up_t.get(v, -99.0) <= 1.0:
                cause = "tau_up"
            elif road == SLOW and per == "taper":
                cause = "limit_taper"
            elif road == SLOW and per == "hold" and s > slow_v * env.dem.by_id[v].sf + 0.5:
                cause = "limit_over"
            elif road == UP and per in ("taper", "hold") and ls.lane.getLength(ls.vehicle.getLaneID(v)) - ls.vehicle.getLanePosition(v) < 150.0 and s > slow_v:
                cause = "limit_approach"
            elif cl == "alks" and env.smooth_cap.get(v, FREE) < FREE - 1.0:
                cause = "cap"
            else:
                lead = ls.vehicle.getLeader(v, 200.0)
                cause = "lead" if lead and lead[0] and lead[1] / max(s, 1.0) <= 3.0 else "free"
            for th in (3.0, 4.5, 7.0, 8.99):
                if a <= -th:
                    step_b[f"{per}|{cl}|{th}|{ph}"] += 1
                    cause_b[f"{per}|{cl}|{th}|{cause}"] += 1
            cause_road[f"{per}|{cl}|{road}|{cause}"] += 1
            if cl == "alks" and a <= -8.99 and prev_a.get(v, 0.0) > -8.99:
                full_ev.append({"t": round(t, 1), "per": per, "road": road, "lane": ls.vehicle.getLaneID(v), "s": round(s, 2), "cause": cause})
        prev_a[v] = a
    if window:
        for v in ids:
            lead = ls.vehicle.getLeader(v, 200.0)
            if lead and lead[0]:
                dv = ls.vehicle.getSpeed(v) - ls.vehicle.getSpeed(lead[0])
                if dv > 0 and (lead[1] + ls.vehicle.getMinGap(v)) / dv < 3.0:
                    ttc_ph[f"{per}|{ph}"] += 1
    for t0 in T0:
        if abs(t - t0) < 1e-6:
            on = [v for v in ls.edge.getLastStepVehicleIDs(SLOW)]
            for want in ("alks", "hdv_car"):
                c = [v for v in on if cls_of(env, v) == want and ls.vehicle.getLanePosition(v) < 400.0]
                c.sort(key=lambda v: ls.vehicle.getLanePosition(v))
                for v in c[:2]:
                    traces.setdefault(f"{want}:{v}:{t0}", [])
    if any(t0 <= t <= t0 + TAPER + 6 for t0 in T0):
        live = set(ids)
        for key, tr in traces.items():
            c, v, t0 = key.split(":")
            if float(t0) <= t <= float(t0) + TAPER + 6 and v in live:
                tr.append((round(t, 1), round(ls.vehicle.getSpeed(v), 2), round(ls.vehicle.getAcceleration(v), 2), round(slow_v, 2), ls.vehicle.getRoadID(v)))


be.MergeEnv._sim_step = patched_step


def wrap_net(orig):
    def f(self):
        r = orig(self)
        env, t = self, self.sim.t
        per = period(t)
        for v in ls.vehicle.getIDList():
            s = ls.vehicle.getSpeed(v)
            lane = ls.vehicle.getLaneID(v)
            cl = cls_of(env, v)
            expo[f"{per}|{lane}|{min(int(s // 5), 6)}|{cl}"] += 1
            lead = ls.vehicle.getLeader(v, 200.0)
            cur = lead[0] if lead and lead[0] else None
            if last_lead.get(v) != cur:
                lead_change[v] = t
            last_lead[v] = cur
            if not cur:
                continue
            gap = lead[1] + ls.vehicle.getMinGap(v)
            sl = ls.vehicle.getSpeed(cur)
            dv = s - sl
            if dv > 0 and gap / dv < 3.0:
                sp = env.dem.by_id[v]
                tau = env.v2v_cur.get(v, be.ALKS_TAU0) if v in env.alks_all else (sp.tau if sp.tau is not None else 1.0)
                ttc_rec.append({"t": round(t), "per": per, "lane": lane, "pos": round(ls.vehicle.getLanePosition(v), 1), "s": round(s, 2), "gap": round(gap, 2), "dv": round(dv, 2), "cf": cl, "cl": cls_of(env, cur), "tau": tau, "a": round(ls.vehicle.getAcceleration(v), 2), "al": round(ls.vehicle.getAcceleration(cur), 2),
                                "sl": round(sl, 2), "lanel": ls.vehicle.getLaneID(cur), "tup_f": round(t - tau_up_t.get(v, -99.0), 1), "tup_l": round(t - tau_up_t.get(cur, -99.0), 1), "lc": round(t - lead_change.get(v, -99.0), 1), "min_a2": 0.0})
                pend_ttc.setdefault(v, []).append((len(ttc_rec) - 1, t + 2.0))
        return r
    return f


be.MergeEnv._net_stats = wrap_net(be.MergeEnv._net_stats)
be.CavEnv._net_stats = wrap_net(be.CavEnv._net_stats)

rd = str(out.parent / "rd")
row = ps.run_one((name, cfg, 5300.0, seed, rd))
row = {k: v for k, v in row.items() if k not in ("cfg", "flow_min", "v20_min")}
out.write_text(json.dumps({"row": row, "step_b": step_b, "cause_b": cause_b, "cause_road": cause_road, "full_ev": full_ev, "ttc_ph": ttc_ph, "ttc_rec": ttc_rec, "expo": expo, "tau_ev": tau_ev, "traces": traces}))
print("done", name, flush=True)
