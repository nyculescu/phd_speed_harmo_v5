#!/usr/bin/env python3
"""
Launch SUMO-GUI instances for visual inspection.

Usage:
  python tests/run_sumo_gui.py                     # defaults: 9000 + 7200 vph
  python tests/run_sumo_gui.py 6000                # single instance at 6000 vph
  python tests/run_sumo_gui.py 9000 7200 5500      # three instances
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")

from tests._sumo_helpers import NET_FILE, DET_FILE
from traffic_environment.vehicle_fleet import generate_fleet_xml, pick_vehicle_type

EPISODE_S = 3600
CAV_PCT = 50.0
RAMP_FRAC = 0.25
SEED = 42


def _make_scenario(demand_vph: int, tmp_dir: Path, idx: int):
    rou_path = tmp_dir / f"gui_{demand_vph}vph.rou.xml"
    cfg_path = tmp_dir / f"gui_{demand_vph}vph.sumocfg"

    fleet_xml = generate_fleet_xml(seed=SEED + idx, weather="clear", step_length=0.5)
    rng = np.random.RandomState(SEED + demand_vph + idx)

    total_veh = int(demand_vph * EPISODE_S / 3600)
    n_main = int(total_veh * (1 - RAMP_FRAC))
    n_ramp = total_veh - n_main

    vehicles = []
    veh_id = 0

    def _add(count, route, t0, span):
        nonlocal veh_id
        if count <= 0:
            return
        step = span / count
        for i in range(count):
            dep = t0 + (i + 0.5) * step
            if dep > EPISODE_S:
                break
            is_cav = rng.random() * 100.0 < CAV_PCT
            vtype = pick_vehicle_type(rng, is_cav=is_cav)
            vehicles.append((dep, route, veh_id, vtype))
            veh_id += 1

    _add(n_main, "mainline_through", 0, EPISODE_S)
    _add(n_ramp, "ramp_on_through", 100, EPISODE_S - 100)
    vehicles.sort(key=lambda v: v[0])

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<routes>", fleet_xml]
    lines.append('  <route id="mainline_through" edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"/>')
    lines.append('  <route id="ramp_on_through" edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')
    for dep, route, vid, vtype in vehicles:
        lines.append(
            f'  <vehicle id="veh_{vid}" type="{vtype}" route="{route}" '
            f'depart="{dep:.2f}" departPos="last" departLane="best" '
            f'departSpeed="desired" insertionChecks="none"/>'
        )
    lines.append("</routes>")
    rou_path.write_text("\n".join(lines))

    cfg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{NET_FILE.resolve()}"/>
        <route-files value="{rou_path.resolve()}"/>
        <additional-files value="{DET_FILE.resolve()}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{EPISODE_S}"/>
    </time>
</configuration>
"""
    cfg_path.write_text(cfg_content)
    return str(cfg_path)


def main():
    demands = [int(d) for d in sys.argv[1:]] if len(sys.argv) > 1 else [9000, 7200]

    tmp_dir = Path(tempfile.mkdtemp(prefix="sumo_gui_"))
    print(f"Temp dir: {tmp_dir}")
    print(f"Launching {len(demands)} SUMO-GUI instance(s): {demands} vph")
    print()

    procs = []
    for idx, d in enumerate(demands):
        cfg = _make_scenario(d, tmp_dir, idx)
        print(f"  [{idx+1}] {d} vph → {Path(cfg).name}")
        p = subprocess.Popen(
            ["sumo-gui", "--configuration-file", cfg,
             "--step-length", "0.5",
             "--step-method.ballistic",
             "--collision.action", "warn",
             "--time-to-teleport", "-1",
             "--window-size", "1200,400",
             "--delay", "50",
             "--start",
             "--quit-on-end"],
        )
        procs.append(p)
        time.sleep(0.5)

    print()
    print("Close SUMO-GUI windows to exit, or Ctrl+C here.")
    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
