"""MRG3 job (Track 2): one run of one classical controller at the merge bottleneck.

Controllers: nc | const:<b> (constant VSL rate b on the application area) | mtfc[:rho:kp:ki:ki2]
Upstream safety staircase (Carlson et al. "safety VSLs"): up2 = min(1, b+0.2), up3 = min(1, b+0.4);
application area (up1, up0a) = b; acceleration area (up0b) = 0.9 while active. VSL = b x 120 km/h.
Metrics: door-to-door mean time in system (all, mainline, ramp; incl. origin queue; drain until empty);
exit throughput; capacity-drop measurement from 5-min aggregates (onset = 5-min speed at up0b < 60 km/h).

python -m vsl_lab.jobs.mrg3_run --ctrl nc --seed 7120000 --main-peak 5400 --ramp-peak 900 --tag calib
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import libsumo as ls
import numpy as np

from vsl_lab.config import RUNS_ROOT
from vsl_lab.controllers.cav_staircase import CavStaircase
from vsl_lab.controllers.mtfc import MTFC
from vsl_lab.controllers.pi_saturation import PISaturation
from vsl_lab.controllers.specialist import Specialist
from vsl_lab.plants import mrg3 as P
from vsl_lab.sim.runner import SumoSim


# 10 s speed probes (edge, lane position; mean speed of vehicles within +-50 m): x ~ 500, 1500, 2500, 3250, 3735 m
# (merge starts at x = 4000). Used by the realism gate (docs/lab/t2_realism_protocol.md).
PROBES = (("up3", 500.0), ("up2", 500.0), ("up1", 500.0), ("up0a", 250.0), ("up0b", 233.0))


def capacity_drop(ts: list) -> dict:
    """ts rows: (t, exit_flow_vph_total, speed_up0b_kmh). 5-min (10 x 30 s) rolling means."""
    if len(ts) < 20:
        return {}
    t = np.array([r[0] for r in ts])
    q = np.array([r[1] for r in ts])
    v = np.array([r[2] if r[2] >= 0 else np.nan for r in ts])
    w = 10
    q5 = np.convolve(q, np.ones(w) / w, "valid")
    v5 = np.array([np.nanmean(v[i:i + w]) if np.isfinite(v[i:i + w]).any() else np.nan for i in range(len(v) - w + 1)])
    t5 = t[w - 1:]
    onset = np.nonzero(v5 < 60.0)[0]
    if len(onset) == 0:
        return {"breakdown": False, "max_5min_flow": float(np.max(q5))}
    i0 = int(onset[0])
    pre = q5[max(0, i0 - 30):i0 + 1]
    rec = np.nonzero(v5[i0:] > 70.0)[0]
    i1 = i0 + (int(rec[0]) if len(rec) else len(v5) - i0)
    dis = q5[min(i0 + 10, i1 - 1):i1] if i1 - i0 > 10 else q5[i0:i1]
    pre_max = float(np.max(pre)) if len(pre) else float("nan")
    dmean = float(np.mean(dis)) if len(dis) else float("nan")
    return {"breakdown": True, "onset_t": float(t5[i0]), "pre_max_5min_flow": pre_max, "discharge_mean_5min_flow": dmean,
            "ratio": dmean / pre_max if pre_max else float("nan"), "congested_s": float((i1 - i0) * 30.0)}


def run(ctrl: str, seed: int, main_peak: float, ramp_peak: float, p_nc: float, truck: float, tag: str, out_root: Path,
        t_end: float = 3900.0, t_ctrl0: float = 300.0, t_max: float = 10800.0, plant: str = "v1",
        driver: str | None = None, cav_share: float = 0.0, cav_model: str = "CACC", cav_arm: str = "none",
        cav_x: float = 1.0, step: float | None = None, geom: str = "merge", stops: bool = False,
        incident: str | None = None) -> dict:
    """Round 3 (round3_tm21_protocol.md): cav_share > 0 adds ACC/CACC CAVs. cav_arm 'B' = CAVs staircase toward the
    posted limit of their lane; 'C' = posted VSL untouched, CAVs on up1/up0a staircase toward b x 120 km/h (pre-zone:
    up2 min(1, b+0.2), up3 min(1, b+0.4)); controllers for C: nc | cavconst:<b> | cavmtfc[:rho:kp:ki:ki2] |
    cavstress (b alternates 0.4 / 1.0 every 300 s in the control window; the T-X safety schedule)."""
    model, dspeed = P.PLANTS[plant]
    dt = step or P.STEP_LENGTH          # Round 3 Addendum A: the author chose 0.2 s for Round 3 (default plant 0.5 s)
    cav_tag = f"_cav{cav_share:g}{cav_arm}{cav_model}x{cav_x:g}" if cav_share > 0 else ""
    cav_tag += f"_dt{dt:g}" if abs(dt - P.STEP_LENGTH) > 1e-9 else ""
    if geom == "lanedrop":
        cav_tag += "_ld"
    inc = None
    if incident:   # headroom scan (round4 Addendum E): "lo:hi:dur:edge:lane" -> a broken-down vehicle stops in that lane
        # at mid-edge for dur s; start ~ U(lo, hi) per seed. The vehicle is the next one on the upstream edge's same lane
        # (it brakes normally to the stop; a sudden lane closure produced artefact collisions in the smoke test).
        lo_, hi_, dur_, e_, l_ = incident.split(":")
        t0_ = float(np.random.default_rng(seed + 991).uniform(float(lo_), float(hi_)))
        inc = {"edge": e_, "lane_idx": int(l_), "lane": f"{e_}_{l_}", "dur": float(dur_), "t_start": round(t0_, 1),
               "veh": None, "t_stop": None, "on": False, "done": False}
        cav_tag += f"_inc{e_}{l_}d{int(float(dur_))}"
    run_id = (f"mrg3{plant}{'' if driver is None else driver}_{ctrl.replace(':', '_')}_s{seed}_m{int(main_peak)}"
              f"_r{int(ramp_peak)}_nc{p_nc:g}_tr{truck:g}{cav_tag}_pid{os.getpid()}")
    run_dir = out_root / tag / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    f = P.files(geom)
    nd = f["n_lanes"]["down"]
    mprof = P.profile(2500.0, main_peak, 600.0, 1200.0, 3000.0, t_end)
    rprof = P.profile(300.0, ramp_peak, 600.0, 1200.0, 3000.0, t_end) if geom == "merge" else []
    dem = P.demand(seed, mprof, rprof, p_noncompliant=p_nc, truck_share=truck, model=model, depart_speed=dspeed,
                   driver=driver, cav_share=cav_share, cav_model=cav_model, step_length=dt)
    cav_ids = {v[1] for v in dem.vehicles if v[3] == "cav"}
    rou = run_dir / f"routes_s{seed}_pid{os.getpid()}.rou.xml"
    dem.write(rou)
    trip_file = run_dir / f"tripinfo_pid{os.getpid()}.xml"
    extra = list(P.DRIVERS[driver]["args"] if driver else [])
    if stops:   # Round 4 co-primary stop metric: SUMO tripinfo waitingCount (speed <= 0.1 m/s episodes per vehicle)
        extra += ["--tripinfo-output", str(trip_file)]
    sim = SumoSim(f["net"], rou, run_dir, dem, additional=[f["add"]], step_length=dt, checkpoint_s=300.0,
                  seed=seed, stuck_wait_s=180.0, extra_args=extra)
    sim.start()
    sens = P.Sensors(f["lanes"])
    mt = None
    b_const = None
    vslad = None
    spec = None
    cav_mode = None                                   # arm C controller kind
    if ctrl.startswith("cavmtfc"):
        parts = ctrl.split(":")
        vals = [float(x) for x in parts[1:]] if len(parts) > 1 else []
        mt = MTFC(**dict(zip(["rho_set", "kp", "ki", "ki2"], vals)))
        cav_mode = "mtfc"
    elif ctrl.startswith("cavconst:"):
        b_const = float(ctrl.split(":")[1])
        cav_mode = "const"
    elif ctrl == "cavstress":
        cav_mode = "stress"
    elif ctrl == "spec" or ctrl.startswith("spec:"):
        # SPECIALIST (Hegyi et al. 2008; controllers/specialist.py): P1 parameters; "spec:<m_t_km>" = P1 with a different
        # tail margin (round4 Addendum B). Detectors = e1 loops at the edge ends; one VSL segment per approach edge.
        import xml.etree.ElementTree as _ET
        shp = {ln.get("id"): ln.get("shape") for ln in _ET.parse(f["net"]).getroot().iter("lane")}
        det_edges = ("up3", "up2", "up1", "up0a", "up0b", "down")
        det_x = [float(shp[f"{e}_0"].split()[0].split(",")[0]) + f["lanes"][f"{e}_0"] - 5.0 for e in det_edges]
        spec = Specialist(det_x, [(0.0, 1000.0), (1000.0, 2000.0), (2000.0, 3000.0), (3000.0, 3500.0), (3500.0, 4000.0)],
                          m_t_km=float(ctrl.split(":")[1]) if ":" in ctrl else 1.5, det_lanes=[3, 3, 3, 3, 3, nd])
        spec_edges = ("up3", "up2", "up1", "up0a", "up0b")
        spec_reasons = {}
    elif ctrl.startswith("vslad:"):
        # Round 4 non-learning adaptive scheduler (CLAUDE.md "best non-learning"): every 60 s, if the 1-min speed at the
        # drop (up0b end loops) < theta km/h, post b on up1/up0a (Carlson staircase upstream, acceleration area 0.9);
        # release when > theta + 10 km/h and on for >= 120 s
        _, th, bb = ctrl.split(":")
        vslad = {"theta": float(th), "b": float(bb), "on": False, "t_on": None}
    elif ctrl.startswith("mtfc"):
        parts = ctrl.split(":")
        vals = [float(x) for x in parts[1:]] if len(parts) > 1 else []
        names = ["rho_set", "kp", "ki", "ki2"]
        mt = MTFC(**dict(zip(names, vals)))
    elif ctrl.startswith("const:"):
        b_const = float(ctrl.split(":")[1])
    ts, bs, feats, probes = [], [], [], []
    dens_samples, qc_hist = [], []
    b_app, b_acc = 1.0, 1.0
    next_loop, next_ctrl, next_samp = 30.0, t_ctrl0 + 60.0, 10.0
    vmax = P.V_LIMIT

    def post(b_app, b_acc):
        P.set_vsl(("up1", "up0a"), b_app * vmax)
        P.set_vsl(("up2",), min(1.0, b_app + 0.2) * vmax)
        P.set_vsl(("up3",), min(1.0, b_app + 0.4) * vmax)
        P.set_vsl(("up0b",), b_acc * vmax)

    # arm P (Round 4): every CAV runs PI-with-saturation onboard (Stern et al. 2018) on the approach and the drop zone;
    # the staircase object only keeps CAV set speeds equal to the lane limit (targets None)
    stair = CavStaircase(cav_x) if cav_share > 0 and cav_arm in ("B", "C", "P") else None
    pis = {}
    b_cav = 1.0                                       # arm C rate (1.0 = no command)
    zone_b = {"up1": 1.0, "up0a": 1.0, "up2": 1.0, "up3": 1.0}

    def cav_control():
        if sim.t >= t_ctrl0 and cav_mode == "stress":
            nonlocal_b = 0.4 if int((sim.t - t_ctrl0) // 300.0) % 2 == 0 else 1.0
            zone_b.update(up1=nonlocal_b, up0a=nonlocal_b, up2=min(1.0, nonlocal_b + 0.2), up3=min(1.0, nonlocal_b + 0.4))
        for vid in ls.vehicle.getIDList():
            if vid not in cav_ids:
                continue
            lane = ls.vehicle.getLaneID(vid)
            if lane.startswith(":"):
                continue
            edge = lane.rsplit("_", 1)[0]
            lim = ls.lane.getMaxSpeed(lane)
            if cav_arm == "P":
                stair.update(sim.t, vid, None, lim)
                if ctrl == "cavpi" and sim.t >= t_ctrl0 and edge in ("up3", "up2", "up1", "up0a", "up0b", "merge"):
                    pi = pis.setdefault(vid, PISaturation(dt))
                    lead = ls.vehicle.getLeader(vid, 100.0)
                    v = ls.vehicle.getSpeed(vid)
                    if lead and lead[0]:
                        v_lead, gap = ls.vehicle.getSpeed(lead[0]), max(lead[1], 0.0)
                    else:
                        v_lead, gap = lim, 100.0
                    ls.vehicle.setSpeed(vid, min(max(pi.v_cmd(v, v_lead, gap), 0.0), lim))
                elif vid in pis:
                    ls.vehicle.setSpeed(vid, -1.0)
                    pis.pop(vid)
                continue
            if cav_arm == "B":
                tgt = lim if edge in ("up3", "up2", "up1", "up0a", "up0b") else None
            else:
                b = zone_b.get(edge, 1.0)
                tgt = b * vmax if b < 1.0 - 1e-9 else None
            stair.update(sim.t, vid, tgt, lim)

    while sim.t < t_end - 1e-9:
        if inc is not None and not inc["on"] and not inc["done"] and sim.t >= inc["t_start"] - 1e-9:
            up_edge = {"up0a": "up1", "up1": "up2", "up0b": "up0a", "up2": "up3"}[inc["edge"]]
            pos_ = 0.5 * f["lanes"][inc["lane"]]
            for vid_ in reversed(ls.lane.getLastStepVehicleIDs(f"{up_edge}_{inc['lane_idx']}")):
                try:
                    ls.vehicle.setStop(vid_, inc["edge"], pos=pos_, laneIndex=inc["lane_idx"], duration=inc["dur"])
                    ls.vehicle.setLaneChangeMode(vid_, 0)
                    inc.update(veh=vid_, on=True, t_stop=round(sim.t, 1))
                    break
                except ls.TraCIException:
                    continue
        if stair is None:
            sim.run_until(sim.t + 10.0)
        else:
            sim.run_until(sim.t + dt)
            cav_control()
        if sim.t >= next_samp - 1e-9:
            dens_samples.append(sens.density_merge_vkl())
            row = [round(sim.t, 1)]
            for e, x in PROBES:
                vs = [ls.vehicle.getSpeed(v) for v in ls.edge.getLastStepVehicleIDs(e)
                      if abs(ls.vehicle.getLanePosition(v) - x) <= 50.0]
                row.append(round(float(np.mean(vs)), 3) if vs else "")
            probes.append(row)
            next_samp += 10.0
        if spec is not None and sim.t >= t_ctrl0:     # re-post the moving SPECIALIST area every 10 s
            for e_, b_ in zip(spec_edges, spec.factors_at(sim.t)):
                P.set_vsl((e_,), b_ * vmax)
        if sim.t >= next_loop - 1e-9:
            q_exit = sum(ls.inductionloop.getLastIntervalVehicleNumber(f"e1_down_{i}") for i in range(nd)) * 120.0
            ts.append((sim.t, q_exit, P.Sensors.speed_kmh("up0b")))
            qc_hist.append(P.Sensors.flow_vph_per_lane("up0a"))
            # D-check feature table (30 s): per-edge flow/lane, speed, per-lane speed spread, densities, ramp flow, b
            row = [round(sim.t, 1)]
            for e in ("up3", "up2", "up1", "up0a", "up0b", "down"):
                ne = nd if e == "down" else 3
                lane_v = [ls.inductionloop.getLastIntervalMeanSpeed(f"e1_{e}_{i}") for i in range(ne)]
                lane_v = [v for v in lane_v if v >= 0]
                row += [round(P.Sensors.flow_vph_per_lane(e, ne), 1), round(P.Sensors.speed_kmh(e, ne), 2),
                        round(float(np.std(lane_v)) * 3.6, 2) if len(lane_v) > 1 else 0.0]
            row += [round(sens.density_merge_vkl(), 2), round(sens.density_down_vkl(), 2),
                    ls.inductionloop.getLastIntervalVehicleNumber("e1_ramp_0") * 120, round(b_app, 2)]
            feats.append(row)
            next_loop += 30.0
        if sim.t >= next_ctrl - 1e-9 and sim.t >= t_ctrl0:
            if cav_mode in ("mtfc", "const"):
                if cav_mode == "mtfc":
                    rho = float(np.mean(dens_samples[-6:])) if dens_samples else 0.0
                    qc = float(np.mean(qc_hist[-2:])) if qc_hist else 0.0
                    b_cav, _ = mt.step(rho, qc)
                else:
                    b_cav = b_const
                zone_b.update(up1=b_cav, up0a=b_cav, up2=min(1.0, b_cav + 0.2), up3=min(1.0, b_cav + 0.4))
                b_app = b_cav
            elif mt is not None:
                rho = float(np.mean(dens_samples[-6:])) if dens_samples else 0.0
                qc = float(np.mean(qc_hist[-2:])) if qc_hist else 0.0
                b_app, b_acc = mt.step(rho, qc)
                post(b_app, b_acc)
            elif b_const is not None:
                b_app, b_acc = b_const, (0.9 if b_const < 1.0 else 1.0)
                post(b_app, b_acc)
            elif spec is not None:
                q1m = [float(np.mean([r_[1 + 3 * i] for r_ in feats[-2:]])) for i in range(6)]
                v1m = [float(np.mean([r_[2 + 3 * i] for r_ in feats[-2:] if r_[2 + 3 * i] >= 0] or [-1.0])) for i in range(6)]
                bs_ = spec.step(sim.t, q1m, v1m)
                for e_, b_ in zip(spec_edges, bs_):
                    P.set_vsl((e_,), b_ * vmax)
                b_app = min(bs_)
                rk_ = spec.last_reason.split(":")[0]
                spec_reasons[rk_] = spec_reasons.get(rk_, 0) + 1
            elif vslad is not None:
                vs = [r_[2] for r_ in ts[-2:] if r_[2] >= 0]
                v1 = float(np.mean(vs)) if vs else 120.0
                if not vslad["on"] and v1 < vslad["theta"]:
                    vslad["on"], vslad["t_on"] = True, sim.t
                elif vslad["on"] and v1 > vslad["theta"] + 10.0 and sim.t - vslad["t_on"] >= 120.0 - 1e-9:
                    vslad["on"] = False
                b_app, b_acc = (vslad["b"], 0.9) if vslad["on"] else (1.0, 1.0)
                post(b_app, b_acc)
            bs.append((sim.t, b_app))
            next_ctrl += 60.0
    # demand over: release VSL / CAV commands, drain uncontrolled
    post(1.0, 1.0)
    if inc is not None:
        inc["done"] = True
    if stair is not None:   # like the posted VSL, CAV commands are released at once for the uncontrolled drain
        for vid in ls.vehicle.getIDList():
            if vid in pis:
                ls.vehicle.setSpeed(vid, -1.0)
            if vid in cav_ids:
                ln = ls.vehicle.getLaneID(vid)
                ls.vehicle.setMaxSpeed(vid, vmax if ln.startswith(":") else ls.lane.getMaxSpeed(ln))
    drained = sim.drain(t_max)
    by_route = sim.time_in_system_by_route()
    out = sim.close(drained=drained)
    n = out["generated"]
    out.update({
        "job": "mrg3_run", "plant": plant, "run_id": run_id, "ctrl": ctrl, "seed": seed, "main_peak": main_peak,
        "ramp_peak": ramp_peak,
        "p_noncompliant": p_nc, "truck_share": truck,
        "mean_time_in_system_s": out["tts_system_vehh"] * 3600.0 / max(n, 1),
        "time_main_s": by_route.get("main", {}).get("mean_s"), "time_ramp_s": by_route.get("ramp", {}).get("mean_s"),
        "n_main": by_route.get("main", {}).get("n"), "n_ramp": by_route.get("ramp", {}).get("n"),
        "capdrop": capacity_drop(ts), "b_trace": bs[::5], "min_b": min((b for _, b in bs), default=1.0),
        "cav_share": cav_share, "cav_arm": cav_arm, "cav_model": cav_model, "cav_x": cav_x, "n_cav": len(cav_ids),
        "cav_steps": stair.n_steps if stair else 0, "cav_max_excess_ms": round(stair.max_excess, 3) if stair else None,
        "emergency_braking": (out.get("sumo_stats") or {}).get("emergencyBraking"), "step_length": dt, "geom": geom,
        "incident": ({k: inc[k] for k in ("lane", "t_start", "t_stop", "dur", "veh")} if inc else None),
        "specialist": ({"n_detected": spec.n_detected, "n_solvable": spec.n_solvable, "n_unsolvable": spec.n_unsolvable,
                        "reasons": spec_reasons} if spec is not None else None),
    })
    try:   # emergency braking attributed to CAVs vs humans, per 1,000 veh-km (Round 3 Addendum A); never fatal
        import re as _re
        km = {"main": 5.25, "ramp": 1.53}
        eb = {"cav": 0, "human": 0}
        for line in sim.log_file.read_text(errors="replace").splitlines():
            m_ = _re.search(r"Vehicle '([^']*)' performs emergency braking", line)
            if m_:
                eb["cav" if m_.group(1) in cav_ids else "human"] += 1
        vkm = {"cav": 0.0, "human": 0.0}
        for v in dem.vehicles:
            vkm["cav" if v[1] in cav_ids else "human"] += km[v[2]]
        out["eb_cav"], out["eb_human"] = eb["cav"], eb["human"]
        out["eb_cav_per_1000vkm"] = 1000.0 * eb["cav"] / vkm["cav"] if vkm["cav"] else None
        out["eb_human_per_1000vkm"] = 1000.0 * eb["human"] / vkm["human"] if vkm["human"] else None
    except Exception as exc:   # noqa: BLE001
        out["eb_attribution_error"] = repr(exc)
    if stops:
        try:
            import xml.etree.ElementTree as _ET
            wc, wt, tl, n = [], [], [], 0
            for _, el in _ET.iterparse(trip_file):
                if el.tag == "tripinfo":
                    wc.append(int(el.get("waitingCount", 0))); wt.append(float(el.get("waitingTime", 0.0)))
                    tl.append(float(el.get("timeLoss", 0.0))); n += 1
                    el.clear()
            out["stops_per_veh"] = float(np.mean(wc)) if wc else None
            out["share_stopped_veh"] = float(np.mean([c > 0 for c in wc])) if wc else None
            out["stop_time_per_veh_s"] = float(np.mean(wt)) if wt else None
            out["time_loss_per_veh_s"] = float(np.mean(tl)) if tl else None
            out["n_tripinfo"] = n
            trip_file.unlink()
        except Exception as exc:   # noqa: BLE001
            out["stops_error"] = repr(exc)
    out.pop("arrivals_bins", None)
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    with open(run_dir / "probes10.csv", "w") as fh:
        fh.write("t," + ",".join(f"{e}@{int(x)}" for e, x in PROBES) + "\n")
        for r in probes:
            fh.write(",".join(str(x) for x in r) + "\n")
    hdr = ["t"] + [f"{e}_{k}" for e in ("up3", "up2", "up1", "up0a", "up0b", "down") for k in ("q", "v", "vspread")] \
        + ["rho_merge", "rho_down", "q_ramp", "b"]
    with open(run_dir / "features.csv", "w") as fh:
        fh.write(",".join(hdr) + "\n")
        for r in feats:
            fh.write(",".join(str(x) for x in r) + "\n")
    try:
        rou.unlink()
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctrl", default="nc")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--main-peak", type=float, default=5400.0)
    ap.add_argument("--ramp-peak", type=float, default=900.0)
    ap.add_argument("--p-nc", type=float, default=0.3)
    ap.add_argument("--truck", type=float, default=0.1)
    ap.add_argument("--plant", default="v1", choices=["v1", "v2", "v3"])
    ap.add_argument("--driver", default=None, choices=sorted(P.DRIVERS))
    ap.add_argument("--cav-share", type=float, default=0.0)
    ap.add_argument("--cav-model", default="CACC", choices=["CACC", "ACC"])
    ap.add_argument("--cav-arm", default="none", choices=["none", "B", "C", "P"])
    ap.add_argument("--cav-x", type=float, default=1.0)
    ap.add_argument("--step", type=float, default=None, help="simulation step (default plant 0.5 s)")
    ap.add_argument("--geom", default="merge", choices=["merge", "lanedrop"])
    ap.add_argument("--stops", action="store_true", help="tripinfo stop metrics (Round 4)")
    ap.add_argument("--incident", default=None, help="lo:hi:dur:edge:lane lane closure (headroom scan)")
    ap.add_argument("--tag", default="smoke")
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "t2"))
    a = ap.parse_args(argv)
    out = run(a.ctrl, a.seed, a.main_peak, a.ramp_peak, a.p_nc, a.truck, a.tag, Path(a.out_root), plant=a.plant,
              driver=a.driver, cav_share=a.cav_share, cav_model=a.cav_model, cav_arm=a.cav_arm, cav_x=a.cav_x,
              step=a.step, geom=a.geom, stops=a.stops, incident=a.incident)
    keys = ("run_id", "mean_time_in_system_s", "time_main_s", "time_ramp_s", "capdrop", "min_b", "teleports", "drained",
            "wall_s")
    print(json.dumps({k: out.get(k) for k in keys} | {"health": out["health"]["status"],
                                                       "codes": list(out["health"]["by_code"].keys())}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
