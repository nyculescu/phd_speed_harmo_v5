"""Reads the effective plant values from SUMO and the fleet sampler. No traffic metric is read or stored."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
import libsumo as ls

from v5b.fleet import b_env as be, b_merge as bm, corridor as co, fleet as fl

OUT = Path(__file__).parent
SEED = 7419640     # already used by the baseline v1 check; only vehicle parameters are read here
LC = "lcStrategic lcCooperative lcSpeedGain lcKeepRight lcOvertakeRight lcAssertive lcLookaheadLeft lcSpeedGainRight lcSpeedGainLookahead lcCooperativeRoundabout lcCooperativeSpeed lcOpposite lcSublane lcPushy lcImpatience lcTimeToImpatience lcAccelLat lcMaxSpeedLatStanding lcMaxSpeedLatFactor lcTurnAlignmentDistance lcOvertakeDeltaSpeedFactor lcKeepRightAcceptanceTime lcLaneDiscipline lcSigma".split()


def net_facts(d):
    root = ET.parse(d / "net.xml").getroot()
    lanes = []
    for e in root.iter("edge"):
        for ln in e.iter("lane"):
            lanes.append({"id": ln.get("id"), "len": float(ln.get("length")), "speed": float(ln.get("speed")), "width": float(ln.get("width", 3.2)), "internal": e.get("function") == "internal"})
    conn = [(c.get("from"), c.get("fromLane"), c.get("to"), c.get("toLane"), c.get("via")) for c in root.iter("connection") if not c.get("from").startswith(":")]
    junc = [(j.get("id"), j.get("type"), j.get("x"), j.get("y")) for j in root.iter("junction") if j.get("type") != "internal"]
    tl = [(t.get("id"), t.get("type"), [(p.get("duration"), p.get("state")) for p in t.iter("phase")]) for t in root.iter("tlLogic")]
    return {"lanes": lanes, "conn": conn, "junc": junc, "tl": tl, "add": (d / "add.xml").read_text().count("<inductionLoop")}


def run(geom):
    plant = {"lc": {"lcAssertive": 1.4}, "hdv": {}, "truck": {}, "smooth": True, "alks": {"lcOvertakeRight": 1}, "geom": geom}
    cfg = bm.setup(0.5, 0.1)
    fl.tune(plant)
    import dataclasses
    cfg = dataclasses.replace(cfg, geom=geom)
    fl.ALKS_EXPLICIT["actionStepLength"] = 0.5
    d = fl.build_net(cfg)
    dem = fl.FleetDemand(SEED, [(0.0, 1800.0, 5300.0)], cfg)
    rou = OUT / f"rb_{geom}.rou.xml"
    dem.write(rou)
    ls.start([be.__dict__.get("SUMO_BIN", "sumo"), "-n", str(d / "net.xml"), "-r", str(rou), "--step-length", "0.1", "--seed", str(SEED), "--route-steps", "0", "--time-to-teleport", "-1", "--collision.action", "warn", "--collision.check-junctions", "true", "--no-step-log", "true", "--duration-log.disable", "true", "--no-warnings", "true", "-a", str(d / "add.xml")])
    seen = {}
    t = 0
    while len(seen) < 3 and t < 1200:
        ls.simulationStep()
        t += 1
        for v in ls.simulation.getDepartedIDList():
            cls = dem.by_id[v].cls
            if cls in seen:
                continue
            g = ls.vehicle
            row = {"accel": g.getAccel(v), "decel": g.getDecel(v), "emergencyDecel": g.getEmergencyDecel(v), "apparentDecel": g.getApparentDecel(v), "minGap": g.getMinGap(v), "tau": g.getTau(v), "imperfection": g.getImperfection(v), "actionStepLength": g.getActionStepLength(v), "length": g.getLength(v), "width": g.getWidth(v), "maxSpeed": g.getMaxSpeed(v), "speedFactor": g.getSpeedFactor(v), "speedDeviation": ls.vehicletype.getSpeedDeviation(g.getTypeID(v)), "vClass": g.getVehicleClass(v), "emissionClass": g.getEmissionClass(v), "shape": g.getShapeClass(v), "maxSpeedLat": g.getMaxSpeedLat(v), "minGapLat": g.getMinGapLat(v), "lateralAlignment": g.getLateralAlignment(v), "speedMode": g.getSpeedMode(v), "laneChangeMode": g.getLaneChangeMode(v)}
            for p in LC:
                try:
                    row[p] = g.getParameter(v, "laneChangeModel." + p)
                except Exception as x:
                    row[p] = "n/a"
            seen[cls] = row
    tlstate = ls.trafficlight.getRedYellowGreenState("rm") if "rm" in ls.trafficlight.getIDList() else None
    ls.close()
    rou.unlink()
    return {"net": net_facts(d), "readback": seen, "tl_state_before_all_green": tlstate, "routes": {k: list(v) for k, v in fl.routes(geom).items()}, "t_stop_s": t / 10}


def draws():
    """Fleet draws over 40 seeds at 5,300 veh/h: parameters only, no simulation."""
    cfg = bm.setup(0.5, 0.1)
    fl.tune({"lc": {"lcAssertive": 1.4}, "alks": {"lcOvertakeRight": 1}, "smooth": True})
    import dataclasses
    cfg = dataclasses.replace(cfg, geom="m32")
    v = []
    route = []
    for s in range(SEED, SEED + 40):
        dem = fl.FleetDemand(s, [(0.0, 1800.0, 5300.0)], cfg)
        v += dem.veh
        route += dem.route_of
    out = {"n": len(v), "shares": {}, "route": {}, "lane": {}}
    for c in ("hdv_car", "truck", "alks"):
        x = [a for a in v if a.cls == c]
        out["shares"][c] = len(x) / len(v)
        q = {}
        for name, get in (("length", lambda a: a.length), ("width", lambda a: a.width), ("sf", lambda a: a.sf), ("desired_kmh", lambda a: a.desired * 3.6), ("tau", lambda a: a.tau), ("sigma", lambda a: a.sigma), ("asl", lambda a: a.asl)):
            y = np.array([get(a) for a in x if get(a) is not None], float)
            if not len(y):
                continue
            hist, edges = np.histogram(y, bins=24)
            q[name] = {"min": y.min(), "p5": np.quantile(y, .05), "p50": np.quantile(y, .5), "p95": np.quantile(y, .95), "max": y.max(), "mean": y.mean(), "hist": hist.tolist(), "edges": edges.tolist()}
            if name == "asl":
                q[name]["values"] = {str(k): float(np.mean(y == k)) for k in sorted(set(y.tolist()))}
        out[c] = q
    for r in ("main", "ramp"):
        x = [a for a, b in zip(v, route) if b == r]
        out["route"][r] = {"share": len(x) / len(v), **{c: sum(a.cls == c for a in x) / len(x) for c in ("hdv_car", "truck", "alks")}}
        out["lane"][r] = {str(k): sum(a.lane == k for a in x) / len(x) for k in range(3)}
    d = sorted(a.depart for a in v[:len(v) // 40])
    out["n_per_run"] = len(v) / 40
    return out


res = {"seed": SEED, "version": ls.getVersion() if False else None, "r1m3": run("m32")}
res["r2m3"] = run("r2m3")
res["r1m2"] = net_facts(fl.build_net(__import__("dataclasses").replace(bm.setup(0.5, 0.1), geom="r1m2")))
res["draws"] = draws()
(OUT / "plant_readback.json").write_text(json.dumps(res, indent=0, default=float))
print({k: list(res["r1m3"]["readback"]) for k in ("seed",) } if False else "ok", res["r1m3"]["t_stop_s"], res["r2m3"]["t_stop_s"], res["draws"]["n"])
