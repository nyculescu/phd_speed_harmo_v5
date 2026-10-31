"""No-control reference days for the fleet plant (V167): capacity, Layer A safety and conflict records.

Day = 24 hourly Poisson rates: ADT x the UK motorway weekday shares (V166 (f), WebTRIS, 10 sites, Tue-Thu autumn 2025),
then drain until empty (cap 2 h). BN4 zipper 100 m (or bn4x, 3 km longer entry, V169), step 0.1 s, the V156-V164
fleet (each CAV class on SUMO's ACC / CACC or on IDM), all green.
Every whole second, each vehicle's same-lane leader comes from getLeader; rear-end TTC = (gap + follower minGap) /
closing speed when the follower is faster. Every TTC below TTC_KEEP is stored (t, follower, leader, TTC, speeds), so the
1.0 / 1.5 / 3.0 s thresholds and the EVT fit (V166 (c)) can be computed afterwards. The SSM device is not used (V166 (a)).
Breakdowns: 'up' loop speed (vehicle-weighted over lanes; intervals without vehicles count as free) below half the
limit for 4 consecutive 30-s intervals; recovery after 4 intervals above.
Pre-queue flow = highest 5-min rolling exit flow in the hour before breakdown; QDF = mean exit flow from 5 min after
breakdown to recovery (the V139 rule adapted to a day with two peaks).
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, SUMO_BIN, clean_sumo_env
from v5b.fleet import control as ct, corridor, fleet as fl, merge as mg
from v5b.fleet.calib import HUMAN_SHARES
from v5b.fleet.crash import CrashProcess
from v5b.fleet.incident import PassingZone
from v5b.fleet.merge import CourtesyGap, RampMerge
from v5b.fleet.smoke import CFG, loop_speed
from v5b.p1c import plant as pl
from v5b.p1c.calibrate import _cpu_util
from v5b.p1c.episode import Sim

# share of daily traffic per hour, 00-01 to 23-24 (%)
UK_WEEKDAY = (0.61, 0.51, 0.52, 0.65, 1.08, 2.35, 5.32, 7.23, 6.71, 6.02, 5.61, 5.70,
              5.89, 6.10, 6.60, 7.21, 7.75, 7.41, 5.70, 4.00, 2.80, 1.96, 1.40, 0.89)
ADT = 20_000
TTC_KEEP = 3.0
LEADER_RANGE = 200.0
DRAIN_CAP = 7200.0


def profile(adt: float = ADT) -> list:
    tot = sum(UK_WEEKDAY)
    return [(3600.0 * h, 3600.0 * (h + 1), adt * s / tot) for h, s in enumerate(UK_WEEKDAY)]


def _first_steps(coll: list) -> list:
    """One row per collision: SUMO reports a pair again on every step while it overlaps. The row keeps the smallest
    bumper distance over the event's steps (None if any step had none)."""
    seen, out, row = {}, [], {}
    for c in coll:
        k = (c["collider"], c["victim"])
        if k not in seen or c["t"] - seen[k] > 1.0:
            row[k] = dict(c)
            out.append(row[k])
        elif "bumper" in c:
            b0, b1 = row[k].get("bumper"), c["bumper"]
            row[k]["bumper"] = None if b0 is None or b1 is None else min(b0, b1)
        seen[k] = c["t"]
    return out


def _bumper(collider: str, victim: str) -> float | None:
    """Collider front to victim back in m, when SUMO sees the victim as the collider's leader (V211)."""
    lead = ls.vehicle.getLeader(collider, 50.0)
    if lead and lead[0] == victim:
        return round(lead[1] + ls.vehicle.getMinGap(collider), 3)
    return None


def contact_counts(events: list) -> dict:
    """V211: a SUMO collision is a physical contact unless its bumper distance stayed above 0; no distance counts as
    contact."""
    contact = sum(1 for e in events if e.get("bumper") is None or e["bumper"] <= 0)
    return {"contacts": contact, "mingap_intrusions": len(events) - contact}


def breakdowns(ser: list, k: int = 2) -> list:
    """Breakdown episodes from the loop speed in series field k (2: 'up' loops; 5: 'merge_up' on ramp32)."""
    t = np.array([x[0] for x in ser])
    q = np.array([x[1] for x in ser]) * 120.0
    v = np.array([np.nan if x[k] is None else x[k] for x in ser], dtype=float)
    slow = np.nan_to_num(v, nan=fl.LIMIT) < 0.5 * fl.LIMIT
    roll = np.convolve(q, np.ones(10) / 10, mode="valid")
    ends = t[9:]
    out, i, n = [], 0, len(t)
    while i <= n - 4:
        if not slow[i:i + 4].all():
            i += 1
            continue
        tb, j = t[i], i + 4
        while j <= n - 4 and not (~slow[j:j + 4]).all():
            j += 1
        tr = t[j] if j <= n - 4 else t[-1]
        cand = roll[(ends > tb - 3600) & (ends <= tb)]
        m = (t >= tb + 300) & (t <= tr)
        pre = float(cand.max()) if cand.size else None
        qdf = float(q[m].mean()) if m.any() else None
        out.append({"t_break": float(tb), "t_recover": float(tr), "min": round((tr - tb) / 60, 1), "pre": pre,
                    "qdf": qdf, "drop": (1 - qdf / pre) if pre and qdf else None})
        i = j + 4
    return out


class CrashSim(Sim):
    """episode.Sim with teleporting off, so crashed vehicles stay where they stopped (V163)."""

    def start(self) -> None:
        self.log_file = self.run_dir / f"sumo_pid{os.getpid()}.log"
        self.stat_file = self.run_dir / f"stats_pid{os.getpid()}.xml"
        args = [SUMO_BIN, "-n", str(self.net_file), "-r", str(self.route_file), "--step-length", str(self.dt),
                "--seed", str(self.seed), "--route-steps", "0", "--time-to-teleport", "-1",
                "--collision.action", "warn", "--collision.check-junctions", "true",
                "--no-step-log", "true", "--duration-log.disable", "true",
                "--log", str(self.log_file), "--statistic-output", str(self.stat_file)]
        if self.additional:
            args += ["-a", ",".join(self.additional)]
        ls.start(args + self.extra_args)
        self.loaded += ls.simulation.getLoadedNumber()
        self._started = True
        self._wall0 = time.time()


def _crash(vids: tuple) -> None:
    for vid in vids:
        ls.vehicle.setLaneChangeMode(vid, 0)
        ls.vehicle.setDecel(vid, ls.vehicle.getEmergencyDecel(vid))
        ls.vehicle.setSpeed(vid, 0.0)


WINDOWS = {"am": (7 * 3600.0, 10 * 3600.0), "pm": (15 * 3600.0, 20 * 3600.0), "day": (0.0, 24 * 3600.0)}


def _controllers(ctrl: dict | None, bank, dem, cp) -> tuple:
    """V213 §3. ctrl["meter"] = {law: alinea | pi | fixed, loop, setpoint, k_r | k_p, k_i (veh/h per %) | rate,
    overrides}; ctrl["alks"] = {loop, zone: short | long, setpoint, k_i, b_min, fixed_b}; ctrl["cascade"]: the ALKS
    rule waits for the meter to saturate (§3.4)."""
    if not ctrl:
        return None, None, None
    if bank is None:
        raise ValueError("E1 controllers exist only on ramp32")
    meter = alks = gate = None
    if "meter" in ctrl:
        c = ctrl["meter"]
        law = ct.MeterLaw(c["law"], c.get("setpoint", 0.0), c.get("k_r", 70.0), c.get("k_p", 0.0), c.get("k_i", 0.0),
                          c.get("rate", ct.R_MAX))
        meter = ct.SumoMeter(ct.Meter(law, c.get("overrides", True)), bank, c.get("loop", "alinea"))
    if "alks" in ctrl:
        c = ctrl["alks"]
        law = ct.MTFC(c.get("setpoint", 0.0), c.get("k_i", 0.02), c.get("b_min", ct.B_MIN), c.get("fixed_b"))
        alks = ct.SumoALKS(law, bank, c.get("loop", "drop"), c.get("zone", "long"),
                           {v.vid for v in dem.veh if v.cls in fl.COMMANDED}, {v.vid: v.desired for v in dem.veh},
                           cp.blocked if cp is not None else (lambda vid: False))
    if ctrl.get("cascade"):
        if meter is None or alks is None:
            raise ValueError("the cascade needs a meter and an ALKS rule")
        gate = ct.Cascade()
    return meter, alks, gate


def _block(b: dict, dem, t: float) -> dict | None:
    """V213 §5.2: the human vehicle on the lane nearest to pos that can stop there at its own decel with 10 m to
    spare gets a stop at pos; None if there is none yet."""
    ln = f"{b['edge']}_{b['lane']}"
    cand = []
    for v in ls.lane.getLastStepVehicleIDs(ln):
        if dem.by_id[v].cls not in ("hdv_car", "truck"):
            continue
        x, sp = ls.vehicle.getLanePosition(v), ls.vehicle.getSpeed(v)
        if x <= b["pos"] - sp * sp / (2.0 * ls.vehicle.getDecel(v)) - 10.0:
            cand.append((x, sp, v))
    for x, sp, v in sorted(cand, reverse=True):
        try:
            ls.vehicle.setStop(v, b["edge"], pos=b["pos"], laneIndex=b["lane"], duration=b["duration"] + 300.0)
        except ls.TraCIException:
            continue
        ls.vehicle.setLaneChangeMode(v, 0)
        return {"vid": v, "cls": dem.by_id[v].cls, "lane": ln, "pos": round(x, 1), "speed": round(sp, 2),
                "t": round(t, 1), "duration": b["duration"]}
    return None


def e1_metrics(tr: np.ndarray, blk: dict | None) -> dict:
    """V213 §7: all-vehicle D by origin and departure window, tails, served throughput per window (removed vehicles
    are already left out of tr)."""
    d, sched, arr, ramp = tr[:, 0], tr[:, 1], tr[:, 2], tr[:, 3].astype(bool)

    def m(mask):
        return round(float(d[mask].mean()), 3) if mask.any() else None

    out = {"d_all": m(np.ones(d.size, bool)), "d_main": m(~ramp), "d_ramp": m(ramp),
           "d_pm_depart": m((sched >= 15 * 3600.0) & (sched < 20 * 3600.0)),
           "d_p95": round(float(np.percentile(d, 95)), 1) if d.size else None,
           "share_over_600": round(float((d > 600.0).mean()), 5) if d.size else None,
           "delay_after24_share": round(float(d[arr > 86400.0].sum() / d.sum()), 5) if d.size and d.sum() > 0 else None,
           "served": {w: {"main": int(((arr >= a) & (arr < b) & ~ramp).sum()),
                          "ramp": int(((arr >= a) & (arr < b) & ramp).sum())} for w, (a, b) in WINDOWS.items()},
           "n_trips": int(d.size)}
    if blk:
        out["d_recovery"] = m((sched >= blk["t"] + blk["duration"]) & (sched < 20 * 3600.0))
    return out


def run_day(seed: int, run_dir: Path, adt: float = ADT, cfg: pl.Config = CFG, crash: dict | None = None,
            hours: tuple | None = None, courtesy: bool = False, squeeze: bool = False, teleport: bool = True,
            forced: dict | None = None, ctrl: dict | None = None, sumo_seed: int | None = None,
            blocker: dict | None = None) -> dict:
    """crash = None (crash-free reference day) or CrashProcess keyword arguments except seed; a crash process always
    runs with teleporting off. forced = {t, edge, lane, pos, duration}: one placed crash (V202), needs a crash process.
    E1 (V213): ctrl = {"meter": {...}, "alks": {...}, "cascade": bool} (see _controllers); sumo_seed changes only SUMO's
    driver noise (default: the demand seed); blocker = {t, edge, lane, pos, duration}: one stalled human vehicle that
    stops at pos with normal braking (§5.2), needs a crash process."""
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    d = fl.build_net(cfg)
    prof = [p for p in profile(adt) if hours is None or hours[0] * 3600 <= p[0] < hours[1] * 3600]
    dem = fl.FleetDemand(seed, prof, cfg)
    models = "".join(f"_{c}{m}" for c, m in fl.CAV_MODELS.items())
    tag = f"day_{cfg.tag()}{models}_adt{adt:g}_s{seed}_pid{os.getpid()}"
    rou, trip = run_dir / f"r_{tag}.rou.xml", run_dir / f"t_{tag}.xml"
    dem.write(rou)
    sim = (CrashSim if crash or not teleport else Sim)(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"],
                                       step_length=cfg.step, seed=seed if sumo_seed is None else sumo_seed,
                                       extra_args=["--tripinfo-output", str(trip)])
    cp = CrashProcess(seed, **crash) if crash else None
    pz = None
    forced_done = forced is None
    blocker_done, blk = blocker is None, None
    cg = rm = None
    removed, arrived_while_crashed = [], []
    loops = fl.loop_ids(cfg.geom)
    idx = {v.vid: i for i, v in enumerate(dem.veh)}
    cls_i = np.array([fl.CLASSES.index(v.cls) for v in dem.veh], dtype=np.int8)
    sim.start()
    fl.all_green(cfg.geom)
    if courtesy:
        cg = CourtesyGap(ls.lane.getLength(mg.LANE))
    if cfg.geom == corridor.NAME:
        rm = RampMerge(ls.lane.getLength(mg.LANE), squeeze)
    if cp is not None:
        pz = PassingZone(lambda vid: dem.by_id[vid].cls, fl.INCIDENT_TAU_FACTOR)
    bank = ct.LoopBank(loops) if cfg.geom == corridor.NAME else None
    meter, alks, gate = _controllers(ctrl, bank, dem, cp)
    ttt_w_s = 0
    rec, ser, coll = [], [], []
    veh_s = closing_s = 0
    min_gap = {}
    t_end = prof[-1][1]
    drained = False
    while True:
        sim.step()
        coll += [{"t": round(sim.t, 1), "collider": c.collider, "victim": c.victim, "type": c.type, "lane": c.lane,
                  "v_collider": round(c.colliderSpeed, 2), "v_victim": round(c.victimSpeed, 2),
                  "bumper": _bumper(c.collider, c.victim)}
                 for c in ls.simulation.getCollisions()]
        for vid in ls.simulation.getDepartedIDList():
            min_gap[vid] = ls.vehicle.getMinGap(vid)
        t = sim.t
        if not forced_done and t >= forced["t"]:
            ln = f"{forced['edge']}_{forced['lane']}"
            hit = [v for v in ls.lane.getLastStepVehicleIDs(ln) if dem.by_id[v].cls in ("hdv_car", "truck")
                   and ls.vehicle.getLanePosition(v) >= forced["pos"]]
            if hit:
                v0 = min(hit, key=ls.vehicle.getLanePosition)
                fol = ls.vehicle.getFollower(v0, 30.0)
                vids = (v0, fol[0]) if fol[0] and 0 <= fol[1] <= 30.0 else (v0,)
                _crash(vids)
                cp.force(t, vids, forced["duration"], dem.by_id[vids[-1]].cls)
                cp.events[-1] |= {"lane": ln, "pos": round(ls.vehicle.getLanePosition(v0), 1),
                                  "speed": round(ls.vehicle.getSpeed(v0), 2)}
                pz.add(v0)
                forced_done = True
        if not blocker_done and t >= blocker["t"]:
            blk = _block(blocker, dem, t)
            if blk is not None:
                cp.force(t, (blk["vid"],), blocker["duration"], blk["cls"])
                cp.events[-1] |= {"lane": blk["lane"], "pos": blk["pos"], "speed": blk["speed"], "kind": "blocker"}
                pz.add(blk["vid"])
                blocker_done = True
        if cp is not None and cp.release:
            live = set(ls.vehicle.getIDList())
            for vid in cp.due(t):
                if blk is not None and vid == blk["vid"] and vid in live:
                    blk["stopped_at_removal"] = ls.vehicle.isStopped(vid)
                    blk["x_removal"] = round(ls.vehicle.getLanePosition(vid), 1)
                if vid in live:
                    ls.vehicle.remove(vid)
                    removed.append(vid)
                else:
                    arrived_while_crashed.append(vid)
        if alks is not None:
            alks.step(t)
        if abs(t - round(t)) < 1e-6:
            if cg is not None:
                cg.step(t)
            if rm is not None:
                rm.step(t, cp.blocked if cp is not None else (lambda vid: False))
            if pz is not None:
                pz.step(cp.blocked)
            if bank is not None and abs(t / pl.LOOP_PERIOD - round(t / pl.LOOP_PERIOD)) < 1e-6:
                bank.read(t)
            if meter is not None:
                meter.step(t)
            if alks is not None and int(round(t)) % 60 == 0:
                alks.update(t, gate.update(meter.m.saturated) if gate is not None else True)
            if blk is not None and "t_stop" not in blk and ls.vehicle.isStopped(blk["vid"]):
                blk["t_stop"], blk["x_stop"] = round(t, 1), round(ls.vehicle.getLanePosition(blk["vid"]), 1)
            ids = ls.vehicle.getIDList()
            veh_s += len(ids)
            if t <= 86400.0:
                ttt_w_s += len(ids) + len(ls.simulation.getPendingVehicles())
            sp = {vid: ls.vehicle.getSpeed(vid) for vid in ids}
            for vid in ids:
                lead = ls.vehicle.getLeader(vid, LEADER_RANGE)
                if not lead or not lead[0] or lead[0] not in sp:
                    continue
                dv = sp[vid] - sp[lead[0]]
                if dv <= 0:
                    continue
                closing_s += 1
                ttc = (lead[1] + min_gap[vid]) / dv
                if ttc < TTC_KEEP:
                    rec.append((t, idx[vid], idx[lead[0]], ttc, sp[vid], sp[lead[0]]))
                    if cp is not None and cp.observe(t, idx[vid], idx[lead[0]], vid, lead[0], dem.by_id[vid].cls, ttc):
                        cp.events[-1] |= {"lane": ls.vehicle.getLaneID(vid), "pos": round(ls.vehicle.getLanePosition(vid), 1),
                                          "speed": round(sp[vid], 2)}
                        _crash((vid, lead[0]))
                        pz.add(lead[0])
            if cp is not None and int(round(t)) % 60 == 0:
                cp.prune(t)
            if abs(t / pl.LOOP_PERIOD - round(t / pl.LOOP_PERIOD)) < 1e-6:
                ser.append((round(t, 1), int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["exit"])),
                            loop_speed(loops["up"]), int(sim.departed), len(ls.simulation.getPendingVehicles()),
                            loop_speed(loops["merge_up"]) if "merge_up" in loops else None,
                            sum(ls.lane.getLastStepVehicleNumber(f"{e}_0") for e in ("r",)) if "ramp_q" in loops
                            else None,
                            loop_speed(loops["drop"]) if "drop" in loops else None,
                            loop_speed(loops["dropend"]) if "dropend" in loops else None))
        if t >= t_end and sim.departed == sim._total and ls.vehicle.getIDCount() == 0 \
                and not ls.simulation.getPendingVehicles():
            drained = True
            break
        if t >= t_end + DRAIN_CAP - 1e-9:
            break
    res = sim.close(drained=drained)
    log = sim.log_file.read_text(errors="replace")
    delays = {c: [] for c in fl.CLASSES}
    delays_wet = {c: [] for c in fl.CLASSES}      # V204 §7 secondary: against the weather-capped desired speed
    ttt = 0.0
    gone = set(removed)
    trips = []                 # E1 per vehicle: delay, scheduled departure, arrival, ramp origin, class
    for _, el in ET.iterparse(trip, events=("end",)):
        if el.tag == "tripinfo":
            v = dem.by_id[el.get("id")]
            tt = float(el.get("duration")) + float(el.get("departDelay"))
            ttt += tt
            dl = tt - float(el.get("routeLength")) / v.desired
            delays[v.cls].append(dl)
            delays_wet[v.cls].append(tt - float(el.get("routeLength")) / min(v.desired, v.max_speed or v.desired))
            if el.get("id") not in gone:
                trips.append((dl, float(el.get("depart")) - float(el.get("departDelay")), float(el.get("arrival")),
                              el.get("departLane", "").startswith("r_"), fl.CLASSES.index(v.cls)))
            el.clear()
    tr = np.array(trips, dtype=np.float64).reshape(-1, 5)
    np.savez_compressed(run_dir.parent / f"trips_s{seed}.npz", delay=tr[:, 0].astype(np.float32),
                        sched=tr[:, 1].astype(np.float32), arrival=tr[:, 2].astype(np.float32),
                        ramp=tr[:, 3].astype(bool), cls=tr[:, 4].astype(np.int8))
    r = np.array(rec, dtype=np.float64).reshape(-1, 6)
    np.savez_compressed(run_dir.parent / f"conflicts_s{seed}.npz", t=r[:, 0].astype(np.float32),
                        follower=r[:, 1].astype(np.int32), leader=r[:, 2].astype(np.int32),
                        ttc=r[:, 3].astype(np.float32), v_f=r[:, 4].astype(np.float32), v_l=r[:, 5].astype(np.float32),
                        cls=cls_i)
    ttc = r[:, 3]
    out = {
        "seed": seed, "adt": adt, "geom": cfg.geom, "cav_models": dict(fl.CAV_MODELS),
        "cav_apparent_decel": fl.CAV_APPARENT_DECEL, "generated": len(dem.veh), "arrived": res["arrived"], "drained": drained,
        "sumo_errors": log.count("Error"), "teleports": res["teleports"], "collisions": res["collisions"],
        "collision_pairs": dict(Counter(f"{dem.by_id[c['collider']].cls}>{dem.by_id[c['victim']].cls}" for c in coll
                                        if c["collider"] in dem.by_id and c["victim"] in dem.by_id)),
        "collision_events": (ev := _first_steps(coll)), **contact_counts(ev),
        "emergency_stops": res["emergency_stops"], "emergency_braking_warnings": log.count("performs emergency braking"),
        "breakdowns": breakdowns(ser), "max_pending": res.get("max_pending"),
        "breakdowns_merge": breakdowns(ser, 5) if "merge_up" in loops else None,
        "ramp_queue_max": max((x[6] for x in ser if x[6] is not None), default=None),
        "crash_rule": crash, "crashes": cp.events if cp else [], "removed": len(removed),
        "courtesy_gaps": cg.n_gaps if cg else None, "courtesy_no_follower": cg.n_no_follower if cg else None,
        "ramp_merge": rm.summary() if rm else None, "teleport": teleport and not crash,
        "incident_tau_factor": fl.INCIDENT_TAU_FACTOR, "zone_slowed": pz.n_slowed if pz else None,
        "arrived_while_crashed": arrived_while_crashed, "arrived_plus_removed": res["arrived"] + len(removed),
        "vehicle_seconds": veh_s, "closing_seconds": closing_s,
        "ttc_seconds_below": {f"{x:g}": int((ttc < x).sum()) for x in (0.5, 1.0, 1.5, 2.0, 3.0)},
        "ttc_min": float(ttc.min()) if ttc.size else None,
        "delay_mean_by_class": {c: round(float(np.mean(x)), 1) if x else None for c, x in delays.items()},
        "delay_wetref_mean_by_class": {c: round(float(np.mean(x)), 1) if x else None for c, x in delays_wet.items()},
        "ttt_h": round(ttt / 3600, 1), "weather": fl.WEATHER, "weather_cav": fl.WEATHER_CAV,
        "human_only": fl.SHARES == HUMAN_SHARES,
        **e1_metrics(tr, blk), "ttt_w_h": round(ttt_w_s / 3600, 2), "ctrl": ctrl, "sumo_seed": sumo_seed,
        "meter": meter.summary() if meter else None, "alks": alks.summary() if alks else None,
        "cascade": gate is not None, "blocker": blk, "removed_ids": sorted(gone),
        "breakdowns_drop": breakdowns(ser, 7) if "drop" in loops else None,
        "loops30": {"groups": list(bank.groups), "rows": bank.rows} if bank else None,
        "series": ser, "health": res["health"]["status"], "health_codes": sorted(res["health"]["by_code"]), "hash": res["hash"], "wall_s": round(time.time() - t_w0, 1),
    }
    out["route_sha1"] = hashlib.sha1(rou.read_bytes()).hexdigest()[:16]
    sim.log_file.replace(run_dir.parent / f"sumo_s{seed}.log")
    for f in (rou, trip, sim.stat_file):
        f.unlink(missing_ok=True)
    return out


def batch(out: Path, seeds: list, workers: int, extra: list) -> None:
    out.mkdir(parents=True, exist_ok=True)
    env = clean_sumo_env()
    print(f"{len(seeds)} days, cpu {_cpu_util():.0f} %", flush=True)

    def one(s):
        while _cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.day", "one", "--seed", str(s),
                            "--out", str(out / f"day_s{s}.json"), *extra], cwd=REPO_ROOT, env=env, capture_output=True,
                           text=True)
        return s, r.returncode, r.stderr[-500:] if r.returncode else ""

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for s, rc, err in ex.map(one, seeds):
            print(("FAIL" if rc else "done"), s, f"{time.time() - t0:.0f} s", err, flush=True)
    print(f"all done in {time.time() - t0:.0f} s", flush=True)


def _common(p) -> None:
    p.add_argument("--plant", help="adopted plant preset, e.g. v188 (overrides geometry, merge and model knobs)")
    p.add_argument("--cav-apparent-decel", type=float)
    p.add_argument("--geom", default=CFG.geom)
    for c in fl.CAV_MODELS:
        p.add_argument(f"--{c}-model", default=fl.CAV_MODELS[c])
    p.add_argument("--crash-k", type=float, help="Layer B scale k; no crash process when not given")
    p.add_argument("--crash-u", type=float, default=1.5)
    p.add_argument("--crash-shape", default="linear")
    p.add_argument("--crash-who", default="human")
    p.add_argument("--hours", help="only these hours of the reference day, e.g. 13,20")
    p.add_argument("--ramp-lc-assertive", type=float)
    p.add_argument("--courtesy", action="store_true", help="V194 courtesy-gap rule at the on-ramp merge")
    p.add_argument("--squeeze", action="store_true", help="V196 squeeze-in rule at the on-ramp merge")
    p.add_argument("--no-teleport", action="store_true")
    p.add_argument("--forced", help="one placed crash: t,edge,lane,pos,duration (V202); needs --crash-k")
    p.add_argument("--weather", default="dry", choices=tuple(fl.WEATHER_STATES), help="V204 weather state of the day")
    p.add_argument("--weather-cav", action="store_true", help="V204 Q5 bound: CAVs get the human rain factors")
    p.add_argument("--human-only", action="store_true", help="human fleet of V187 (no CAVs)")
    p.add_argument("--ctrl", help="E1 controllers as JSON (V213 §3, see _controllers)")
    p.add_argument("--sumo-seed", type=int, help="SUMO --seed (driver noise); default the demand seed (V213 twins)")
    p.add_argument("--blocker", help="one stalled vehicle: t,edge,lane,pos,duration (V213 §5.2); needs --crash-k")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--seed", type=int, required=True)
    o.add_argument("--adt", type=float, default=ADT)
    o.add_argument("--out", required=True)
    _common(o)
    b = sub.add_parser("batch")
    b.add_argument("--out", required=True)
    b.add_argument("--seed0", type=int, required=True)
    b.add_argument("--n", type=int, default=10)
    b.add_argument("--workers", type=int, default=10)
    b.add_argument("--adt", type=float, default=ADT)
    _common(b)
    a = ap.parse_args(argv)
    if a.cav_apparent_decel is not None:
        fl.CAV_APPARENT_DECEL = a.cav_apparent_decel
    fl.CAV_MODELS.update({c: getattr(a, f"{c}_model") for c in fl.CAV_MODELS})
    fl.RAMP_LC_ASSERTIVE = a.ramp_lc_assertive
    fl.WEATHER, fl.WEATHER_CAV = a.weather, a.weather_cav
    if a.human_only:
        fl.SHARES = HUMAN_SHARES
    hours = tuple(int(x) for x in a.hours.split(",")) if a.hours else None
    crash = None if a.crash_k is None else {"k": a.crash_k, "u": a.crash_u, "shape": a.crash_shape,
                                             "who": a.crash_who}
    if a.cmd == "one":
        out = Path(a.out)
        cfg = dataclasses.replace(CFG, geom=a.geom)
        if a.plant:
            cfg = fl.apply_plant(a.plant, cfg)
        teleport = not a.no_teleport and fl.PLANTS.get(a.plant, {}).get("teleport", True)
        fc = None
        if a.forced:
            t_, e_, l_, p_, d_ = a.forced.split(",")
            fc = {"t": float(t_), "edge": e_, "lane": int(l_), "pos": float(p_), "duration": float(d_)}
        bk = None
        if a.blocker:
            t_, e_, l_, p_, d_ = a.blocker.split(",")
            bk = {"t": float(t_), "edge": e_, "lane": int(l_), "pos": float(p_), "duration": float(d_)}
        if (fc or bk) and crash is None:
            raise SystemExit("--forced and --blocker need --crash-k")
        res = run_day(a.seed, out.parent / f"rd_s{a.seed}", a.adt, cfg, crash, hours, a.courtesy, a.squeeze, teleport,
                      fc, json.loads(a.ctrl) if a.ctrl else None, a.sumo_seed, bk)
        res |= {"plant": a.plant, "hours": a.hours, "ramp_lc_assertive": a.ramp_lc_assertive}
        tmp = out.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(res))
        tmp.replace(out)
    else:
        extra = ["--geom", a.geom] + [x for c in fl.CAV_MODELS for x in (f"--{c}-model", fl.CAV_MODELS[c])]
        if a.plant:
            extra += ["--plant", a.plant]
        extra += ["--adt", str(a.adt)]
        if a.hours:
            extra += ["--hours", a.hours]
        if a.ramp_lc_assertive is not None:
            extra += ["--ramp-lc-assertive", str(a.ramp_lc_assertive)]
        if a.forced:
            extra += ["--forced", a.forced]
        extra += ["--weather", a.weather]
        extra += [f for f, on in (("--courtesy", a.courtesy), ("--squeeze", a.squeeze),
                                  ("--no-teleport", a.no_teleport), ("--weather-cav", a.weather_cav),
                                  ("--human-only", a.human_only)) if on]
        if a.cav_apparent_decel is not None:
            extra += ["--cav-apparent-decel", str(a.cav_apparent_decel)]
        if crash:
            extra += [x for k, v in crash.items() for x in (f"--crash-{k}", str(v))]
        batch(Path(a.out), list(range(a.seed0, a.seed0 + a.n)), a.workers, extra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
