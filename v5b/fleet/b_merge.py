"""B bind check runs on m32 (V258, docs/research/protocols/drafts/bind_B_core_v2.md): no-control arms of stages S,
C0 and the ladder (NC, NCμ, the deadlock-detector controls). The control arms come with stage T.

One run: constant Poisson demand Q for WINDOW_END s (warm-up to 600 s, window 600-4,200 s by scheduled departure),
then drain; teleporting off; meter green. Counts that feed a rule are taken by vehicle id (§4): merges (a ramp-origin
vehicle's first exit from 3a_0, every step), first passages of the 3a_1 end and of the MA end (id loops read every
step). The deadlock detector reads every whole second; a run stops at a 600-s event.
Merge onset (V262): the approved 4-reading rule on the lane-0 `merge_up` speed (series field 13), an occupied interval
without a passing vehicle counting as standing; the all-lane reading stays report-only.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.fleet import control as ct, corridor, fleet as fl
from v5b.fleet.day import DRAIN_CAP, CrashSim, _bumper, _first_steps, breakdowns, code_id, contact_counts
from v5b.fleet.smoke import CFG, loop_speed

PLANT = "m32"
WARM, WINDOW_END = 600.0, 4200.0
B0 = 3 * 1602.0
SHARES = (0.25, 0.50, 0.80)
MERGE_LANE, ROAD0 = "3a_0", "3a_1"
MA_EDGE2_TAIL, MA_EDGE3_HEAD = 100.0, 300.0
DEADLOCK_X, DEADLOCK_STOP = 120.0, 600.0
STAND_V = 0.1
RAMP_STAND_V = 2.0
DESIRED_ALKS = fl.LIMIT
MU_DV = 0.5 / 3.6
ALKS_READBACK = {"accel": 2.6, "decel": 4.5, "emergencyDecel": 9.0, "minGap": 2.5, "tau": fl.ALKS_TAU}


def setup(share: float, step: float, explicit: bool = True) -> object:
    cfg = fl.apply_plant("v199", dataclasses.replace(CFG, step=step))
    fl.B_ALKS_SHARE = share
    fl.ALKS_EXPLICIT = dict(fl.ALKS_DEFAULTS) if explicit else None
    return dataclasses.replace(cfg, geom=PLANT)


def lane0_speed(n: int, occ: float, v: float | None) -> float | None:
    """V262 onset input: the lane-0 `merge_up` speed, with an interval in which the loop was occupied but no vehicle
    passed counted as standing (0), not as free."""
    if n:
        return v
    return 0.0 if occ > 0 else None


def trip_hash(rows: list, coll: list) -> str:
    """§8: SHA-1 of the sorted tripinfo rows at full precision plus the collision events."""
    h = hashlib.sha1()
    for r in sorted(rows):
        h.update(repr(r).encode())
    for c in coll:
        h.update(repr(sorted(c.items())).encode())
    return h.hexdigest()[:16]


def _trips(path: Path) -> list:
    keys = ("id", "depart", "departDelay", "arrival", "departLane", "arrivalLane", "routeLength", "timeLoss",
            "duration")
    rows = []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag == "tripinfo":
            rows.append(tuple(el.get(k) for k in keys))
            el.clear()
    return rows


def _ma_vehicles(l2: float, internal: list) -> list:
    ids = [v for v in ls.edge.getLastStepVehicleIDs("2") if ls.vehicle.getLanePosition(v) > l2 - MA_EDGE2_TAIL]
    ids += list(ls.edge.getLastStepVehicleIDs("3a"))
    ids += [v for v in ls.edge.getLastStepVehicleIDs("3") if ls.vehicle.getLanePosition(v) < MA_EDGE3_HEAD]
    for e in internal:
        ids += list(ls.edge.getLastStepVehicleIDs(e))
    return ids


def run(seed: int, share: float, q: float, step: float, arm: str, out: Path, explicit: bool = True,
        hold: dict | None = None, t_end: float = WINDOW_END) -> dict:
    """arm: 'NC' or 'NCmu'. hold (smoke only): {lane, t, dur, tail} holds one vehicle on lane within tail m of its
    end with setSpeed(0) for dur s (the §10 deadlock-detector controls)."""
    t_w0 = time.time()
    out = Path(out)
    rd = out.parent / "rd"
    rd.mkdir(parents=True, exist_ok=True)
    cfg = setup(share, step, explicit)
    d = fl.build_net(cfg)
    prof = [(0.0, t_end, q)]
    dem = fl.FleetDemand(seed, prof, cfg)
    ramp = {v.vid for v, r in zip(dem.veh, dem.route_of) if r == "ramp"}
    tag = f"b_{PLANT}_s{share:g}_q{q:g}_st{step:g}_{arm}_x{int(explicit)}_s{seed}_pid{os.getpid()}"
    rou, trip = rd / f"r_{tag}.rou.xml", rd / f"t_{tag}.xml"
    dem.write(rou)
    sim = CrashSim(d / "net.xml", rou, rd, dem, additional=[d / "add.xml"], step_length=step, seed=seed,
                   extra_args=["--tripinfo-output", str(trip)])
    loops = fl.loop_ids(PLANT)
    a_end, ma_end = "a_end_3a_1", loops["ma_end"]
    sim.start()
    fl.all_green(PLANT)
    tls_rm = ls.trafficlight.getRedYellowGreenState(corridor.METER)
    l2 = ls.lane.getLength("2_0")
    internal = [e for e in ls.edge.getIDList() if e.startswith((":m_", ":ae_"))]
    t_ins, t_merge, t_a1, t_ma, ma_lane = {}, {}, {}, {}, {}
    on3a0, entries_main, reentries = set(), 0, 0
    seen3a0 = set()
    last_a1, ev, events = 0.0, None, []
    max_w = max_c = 0.0
    status = "ok"
    coll, ser = [], []
    bin_merges = bin_ma = bin_ma0 = 0
    sched_ramp = np.zeros(int((t_end + DRAIN_CAP) // 30) + 2, int)
    for v in dem.veh:
        if v.vid in ramp:
            sched_ramp[int(v.depart // 30)] += 1
    readback_dev, n_alks = 0.0, 0
    mu = {"done": arm != "NCmu", "vid": None, "t": None, "own": None, "log": []}
    held = {"vid": None, "t": None, "done": hold is None}
    drained = False
    while True:
        sim.step()
        t = round(sim.t, 3)
        coll += [{"t": round(t, 1), "collider": c.collider, "victim": c.victim, "type": c.type, "lane": c.lane,
                  "bumper": _bumper(c.collider, c.victim), "pos": round(c.pos, 1)} for c in ls.simulation.getCollisions()]
        for vid in ls.simulation.getDepartedIDList():
            t_ins[vid] = t
            if dem.by_id[vid].cls == "alks":
                n_alks += 1
                ty = f"t.{vid}"
                got = {"accel": ls.vehicletype.getAccel(ty), "decel": ls.vehicletype.getDecel(ty),
                       "emergencyDecel": ls.vehicletype.getEmergencyDecel(ty), "minGap": ls.vehicletype.getMinGap(ty),
                       "tau": ls.vehicletype.getTau(ty)}
                readback_dev = max(readback_dev, max(abs(got[k] - ALKS_READBACK[k]) for k in got),
                                   abs(ls.vehicle.getSpeedFactor(vid) - 1.0))
        # a merge is a ramp vehicle's first step on 3a off lane 0 (or on edge 3): one that enters 3a_0 and changes
        # lane within a single step is never listed on 3a_0
        for e in ("3a", "3"):
            for vid in ls.edge.getLastStepVehicleIDs(e):
                if vid in ramp and vid not in t_merge and (e == "3" or ls.vehicle.getLaneIndex(vid) > 0):
                    t_merge[vid] = t
                    bin_merges += 1
        now = set(ls.lane.getLastStepVehicleIDs(MERGE_LANE))
        for vid in now - on3a0:
            if vid in seen3a0:
                reentries += 1
            elif vid not in ramp:
                entries_main += 1
            seen3a0.add(vid)
        on3a0 = now
        for vid in ls.inductionloop.getLastStepVehicleIDs(a_end):
            if vid not in t_a1:
                t_a1[vid] = t
            last_a1 = t
        for k, lp in enumerate(ma_end):
            for vid in ls.inductionloop.getLastStepVehicleIDs(lp):
                if vid not in t_ma:
                    t_ma[vid], ma_lane[vid] = t, k
                    bin_ma += 1
                    bin_ma0 += k == 0
        if not mu["done"] and t >= WARM:
            if mu["vid"] is None:
                for vid in ls.edge.getLastStepVehicleIDs("1"):
                    # within 1 m/s of the desired speed and faster than the cap, so the 1-s cap binds
                    sp = ls.vehicle.getSpeed(vid)
                    if dem.by_id[vid].cls == "alks" and abs(sp - DESIRED_ALKS) <= 1.0 and sp > DESIRED_ALKS - MU_DV:
                        own = ls.vehicle.getMaxSpeed(vid)
                        cap = ct.command(DESIRED_ALKS - MU_DV, sp, own, dt=step)
                        ls.vehicle.setMaxSpeed(vid, cap)
                        mu.update(vid=vid, t=t, own=own)
                        mu["log"].append({"t": t, "vid": vid, "cap": round(cap, 4),
                                          "binding": cap < ls.vehicle.getSpeed(vid)})
                        break
            elif t >= mu["t"] + 1.0 - 1e-9:
                if mu["vid"] in ls.vehicle.getIDList():
                    ls.vehicle.setMaxSpeed(mu["vid"], mu["own"])
                    mu["restore_ok"] = abs(ls.vehicle.getMaxSpeed(mu["vid"]) - mu["own"]) < 1e-9
                mu["done"] = True
        if not held["done"]:
            if held["vid"] is None and t >= hold["t"]:
                # the held vehicle must come to rest within the last 'tail' m, so pick one by its braking distance
                ln_len = ls.lane.getLength(hold["lane"])
                cand = [v for v in ls.lane.getLastStepVehicleIDs(hold["lane"])
                        if ln_len - hold["tail"] <= ls.vehicle.getLanePosition(v)
                        + ls.vehicle.getSpeed(v) ** 2 / (2 * ls.vehicle.getDecel(v)) <= ln_len - 1.0
                        and (hold["lane"] != MERGE_LANE or v in ramp)]
                if cand:
                    # setSpeed(0) alone lets a standing vehicle change lanes, which would free the lane it holds
                    held["vid"], held["t"] = max(cand, key=ls.vehicle.getLanePosition), t
                    held["lc_mode"] = ls.vehicle.getLaneChangeMode(held["vid"])
                    ls.vehicle.setLaneChangeMode(held["vid"], 0)
                    ls.vehicle.setSpeed(held["vid"], 0.0)
            elif held["vid"] is not None and t >= held["t"] + hold["dur"]:
                if held["vid"] in ls.vehicle.getIDList():
                    held["lane_at_release"] = ls.vehicle.getLaneID(held["vid"])
                    held["to_end_at_release"] = round(ls.lane.getLength(held["lane_at_release"])
                                                      - ls.vehicle.getLanePosition(held["vid"]), 2)
                    ls.vehicle.setSpeed(held["vid"], -1)
                    ls.vehicle.setLaneChangeMode(held["vid"], held["lc_mode"])
                held["done"] = True
        if abs(t - round(t)) < 1e-6:
            ids = _ma_vehicles(l2, internal)
            w, wid = max(((ls.vehicle.getWaitingTime(v), v) for v in ids), default=(0.0, None))
            c = t - last_a1
            max_w, max_c = max(max_w, w), max(max_c, c)
            m = min(w, c)
            if m > DEADLOCK_X:
                if ev is None:
                    ev = {"start": round(t - m, 1), "vid": wid, "lane": ls.vehicle.getLaneID(wid),
                          "pos": round(ls.vehicle.getLanePosition(wid), 1)}
                ev["end"] = round(t, 1)
            elif ev is not None:
                events.append(ev)
                ev = None
            if m >= DEADLOCK_STOP:
                status = "deadlocked"
                break
            if abs(t / 30.0 - round(t / 30.0)) < 1e-6:
                stand = sum(1 for e in ("r", "rj", MERGE_LANE) for v in
                            (ls.lane.getLastStepVehicleIDs(f"{e}_0") if e != MERGE_LANE else ls.lane.getLastStepVehicleIDs(e))
                            if v in ramp and ls.vehicle.getSpeed(v) < RAMP_STAND_V)
                mu_ids = loops["merge_up"]
                empty_occ = (sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in mu_ids) == 0
                             and sum(ls.inductionloop.getLastIntervalOccupancy(i) for i in mu_ids) > 0)
                ser.append((round(t, 1), bin_ma, None, int(sim.departed), len(ls.simulation.getPendingVehicles()),
                            loop_speed(mu_ids), bin_merges, stand, int(sched_ramp[int(t // 30) - 1]),
                            loop_speed(["merge_up_2_0"]), bin_ma0, bool(empty_occ),
                            int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in ma_end)),
                            lane0_speed(n0 := ls.inductionloop.getLastIntervalVehicleNumber("merge_up_2_0"),
                                        occ0 := ls.inductionloop.getLastIntervalOccupancy("merge_up_2_0"),
                                        loop_speed(["merge_up_2_0"])), round(occ0, 2), n0))
                bin_merges = bin_ma = bin_ma0 = 0
        if t >= t_end and sim.departed == sim._total and ls.vehicle.getIDCount() == 0 \
                and not ls.simulation.getPendingVehicles():
            drained = True
            break
        if t >= t_end + DRAIN_CAP - 1e-9:
            break
    if ev is not None:
        events.append(ev)
    res = sim.close(drained=drained)
    rows = _trips(trip)
    ev_coll = _first_steps(coll)
    by = {r[0]: r for r in rows}
    sched = {v.vid: v.depart for v in dem.veh}
    win = [v.vid for v in dem.veh if WARM <= v.depart < t_end]
    delay = {}
    for vid, r in by.items():
        v = dem.by_id[vid]
        delay[vid] = float(r[8]) + float(r[2]) - float(r[6]) / v.desired
    ins_delay = [t_ins[v] - sched[v] for v in t_ins]
    order = [v.vid for v in dem.veh]
    nan = float("nan")
    np.savez_compressed(out.with_suffix(".npz"), sched=np.array([sched[v] for v in order]),
                        insert=np.array([t_ins.get(v, nan) for v in order]),
                        merge=np.array([t_merge.get(v, nan) for v in order]),
                        a1=np.array([t_a1.get(v, nan) for v in order]), ma=np.array([t_ma.get(v, nan) for v in order]),
                        ma_lane=np.array([ma_lane.get(v, -1) for v in order], np.int8),
                        arrival=np.array([float(by[v][3]) if v in by else nan for v in order]),
                        delay=np.array([delay.get(v, nan) for v in order]),
                        ramp=np.array([v in ramp for v in order]), cls=np.array([fl.CLASSES.index(dem.by_id[v].cls)
                                                                                 for v in order], np.int8))
    log = sim.log_file.read_text(errors="replace")
    o = {"plant": PLANT, "arm": arm, "share": share, "q": q, "step": step, "seed": seed, "sumo_seed": seed,
         "explicit_vtype": explicit, "hold": hold, "tls_rm": tls_rm, "held": {k: held.get(k) for k in ("vid", "t", "lane_at_release", "to_end_at_release")}, "code": code_id(),
         "generated": len(dem.veh), "inserted": sim.departed, "trips": len(rows), "ramp_generated": len(ramp),
         "alks_generated": sum(v.cls == "alks" for v in dem.veh), "truck_generated": sum(v.cls == "truck" for v in dem.veh),
         "window_vehicles": len(win), "merges": len(t_merge), "ramp_trips": sum(1 for v in by if v in ramp),
         "a1_crossings": len(t_a1), "ma_crossings": len(t_ma), "main_entries_3a0": entries_main,
         "reentries_3a0": reentries, "drained": drained, "status": status if status != "ok" or drained else "undrained",
         "deadlock_events": events, "max_w": round(max_w, 1), "max_c": round(max_c, 1),
         "teleports": res["teleports"], "collisions": res["collisions"], "collision_events": ev_coll,
         **contact_counts(ev_coll), "sumo_errors": log.count("Error"),
         "emergency_braking_warnings": log.count("performs emergency braking"),
         "max_pending": res.get("max_pending"),
         "insert_delay_p95": round(float(np.percentile(ins_delay, 95)), 1) if ins_delay else None,
         "alks_readback_dev": round(readback_dev, 9), "alks_departed": n_alks, "nc_mu": mu,
         "d_all_window": round(float(np.mean([delay[v] for v in win if v in delay])), 3) if win else None,
         "breakdowns_merge": breakdowns(ser, 13), "breakdowns_merge_alllane": breakdowns(ser, 5),
         "breakdowns_lane0": breakdowns(ser, 9),
         "series": ser, "trip_hash": trip_hash(rows, ev_coll), "hash": res["hash"],
         "health_codes": sorted(res["health"]["by_code"]), "wall_s": round(time.time() - t_w0, 1),
         "sim_s": round(sim.t, 1)}
    for f in (rou, trip, sim.stat_file, sim.log_file):
        f.unlink(missing_ok=True)
    tmp = out.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(o))
    tmp.replace(out)
    return o


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="JSON: seed, share, q, step, arm, out, explicit, hold, t_end")
    j = json.loads(ap.parse_args(argv).job)
    run(j["seed"], j["share"], j["q"], j["step"], j["arm"], Path(j["out"]), j.get("explicit", True), j.get("hold"),
        j.get("t_end", WINDOW_END))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
