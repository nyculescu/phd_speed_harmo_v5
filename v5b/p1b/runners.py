"""P1b amber and red runners (addendum p1b_addendum.md B2, R4; sensitivity rows only, R5).

- A share s of the vehicles are "runners": every vehicle (human or AV) is a runner iff u_i < s, with u_i drawn per
  vehicle, in the demand's vehicle order, from rng(demand seed + RUNNER_SALT). The draw does not touch the demand rng,
  so the vehicles, their departures and types are the same for every arm and every s; the runner sets are nested
  (s = 10 % is a subset of s = 30 %). At s = 0 the route file is byte-identical to the one without runners.
- A runner has the vType of its base type plus the SUMO junction-model parameters RUNNER_JM:
  jmDriveAfterYellowTime = 3 s (amber is 3 s: ignored), jmDriveAfterRedTime = 1.5 s, jmDriveRedSpeed = 13.9 m/s.
"""
from __future__ import annotations

import numpy as np

RUNNER_SALT = 6271            # new salt (incident 3301, false alarm 5113, D1 2027 / 4049)
RUNNER_JM = {"jmDriveAfterYellowTime": "3", "jmDriveAfterRedTime": "1.5", "jmDriveRedSpeed": "13.9"}
SHARES = (0.10, 0.30)         # R4, V108 (3): s in {10 %, 30 %}; the main analysis uses s = 0
SUFFIX = "_run"


def runner_vtypes(vtypes_xml: str, base_types=("human", "av")) -> str:
    """The base vType lines plus one runner copy per base type (id + SUFFIX, with RUNNER_JM)."""
    jm = " ".join(f'{k}="{v}"' for k, v in RUNNER_JM.items())
    lines = vtypes_xml.splitlines()
    extra = []
    for t in base_types:
        src = [ln for ln in lines if f'id="{t}"' in ln]
        if len(src) != 1:
            raise ValueError(f"vType {t!r} not found once in the vType block")
        extra.append(src[0].replace(f'id="{t}"', f'id="{t}{SUFFIX}"').replace("/>", f" {jm}/>"))
    return "\n".join(lines + extra)


def runner_flags(n: int, seed: int, share: float) -> np.ndarray:
    if not 0.0 <= share <= 1.0:
        raise ValueError(share)
    return np.random.default_rng(seed + RUNNER_SALT).random(n) < share


def apply_runners(demand, seed: int, share: float):
    """Mark runners in a generated Demand in place (share 0: unchanged). Returns the set of runner vehicle ids."""
    if share == 0:
        return set()
    flags = runner_flags(len(demand.vehicles), seed, share)
    demand.vtypes_xml = runner_vtypes(demand.vtypes_xml)
    out, vehs = set(), []
    for f, (dep, vid, rid, vt) in zip(flags, demand.vehicles):
        if f:
            vt = vt + SUFFIX
            out.add(vid)
        vehs.append((dep, vid, rid, vt))
    demand.vehicles = vehs
    return out


def signal_scenario(mode: str = "tick", t_amber: float = 10.0, t_end: float = 60.0) -> dict:
    """Pre-data check (B2, R4), one SUMO run on BN4 (call in its own process: libsumo). Four vehicles cruise at
    10 m/s on separate lanes of edge 2 towards the meter; the signal is G, then y at t_amber for 3 s, then r to the
    end, set every 1-s tick ('tick', as the P1b episode) or every 0.5-s step ('step'). Vehicles (type, lane, metres to
    the stop line at amber onset): run35 (runner, 0, 35: reaches the line about 0.5 s into red), norm35 (normal, 1, 35),
    run100 (runner, 2, 100: reaches the line about 7 s into red), norm100 (normal, 3, 100). Returns the red onset, the
    crossing time of each vehicle (None if it never left edge 2) and the final road and speed of each vehicle."""
    import tempfile
    from pathlib import Path

    import libsumo as ls

    from v5b.d1 import plant
    from v5b.d1.config import SUMO_BIN
    if mode not in ("tick", "step"):
        raise ValueError(mode)
    d = Path(tempfile.mkdtemp(prefix="p1b_runner_check_"))
    files = plant.files()
    rou = d / "r.rou.xml"
    rou.write_text("<routes>\n" + runner_vtypes(plant.vtypes_xml()) + '\n  <route id="r" edges="2 3 4 5"/>\n</routes>\n')
    ls.start([SUMO_BIN, "-n", str(files["net"]), "-r", str(rou), "-a", str(files["add"]), "--step-length",
              str(plant.STEP_LENGTH), "--no-step-log", "true", "--collision.action", "warn", "--log", str(d / "log")])
    L, v0 = ls.lane.getLength("2_0"), 10.0
    cases = {"run35": ("human" + SUFFIX, 0, 35.0), "norm35": ("human", 1, 35.0),
             "run100": ("human" + SUFFIX, 2, 100.0), "norm100": ("human", 3, 100.0)}
    for vid, (vt, lane, dist) in cases.items():
        ls.vehicle.add(vid, "r", vt, depart="now", departLane=str(lane), departPos=str(L - dist - v0 * t_amber),
                       departSpeed=str(v0))
    ls.trafficlight.setRedYellowGreenState(plant.TLS_ID, "GGGG")
    ls.simulationStep()
    for vid in cases:
        ls.vehicle.setSpeedFactor(vid, 1.0)
        ls.vehicle.setMaxSpeed(vid, v0)
    cross = {vid: None for vid in cases}
    while ls.simulation.getTime() < t_end - 1e-9:
        t = ls.simulation.getTime()
        st = "GGGG" if t < t_amber else "yyyy" if t < t_amber + 3.0 else "rrrr"
        if mode == "step" or abs(t - round(t)) < 1e-9:
            ls.trafficlight.setRedYellowGreenState(plant.TLS_ID, st)
        ls.simulationStep()
        ids = set(ls.vehicle.getIDList())
        for vid in cases:
            if cross[vid] is None and (vid not in ids or ls.vehicle.getRoadID(vid) != "2"):
                cross[vid] = t      # left edge 2 during the step that started at t
    ids = set(ls.vehicle.getIDList())
    final = {vid: (ls.vehicle.getRoadID(vid), ls.vehicle.getSpeed(vid)) if vid in ids else None for vid in cases}
    ls.close()
    return {"mode": mode, "t_amber": t_amber, "t_red": t_amber + 3.0, "cross_step_start": cross, "final": final}
