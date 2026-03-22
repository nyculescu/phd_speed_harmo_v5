# tests/_sumo_helpers.py
"""
Shared helpers for SUMO-based tests.

Provides route/config generation, TrafficEnv construction, and
common constants.  All SUMO tests import from here instead of
duplicating the scaffolding.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# Ensure SUMO tools (traci) are importable.
_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
_SUMO_TOOLS = os.path.join(_SUMO_HOME, "tools")
if _SUMO_TOOLS not in sys.path:
    sys.path.insert(0, _SUMO_TOOLS)

import numpy as np

_SUMO_DIR = Path(__file__).resolve().parents[1] / "traffic_environment" / "sumo"
NET_FILE = _SUMO_DIR / "ramps_v2.net.xml"
DET_FILE = _SUMO_DIR / "detectors_ramps_v2.add.xml"
RESULTS_ROOT = Path(__file__).resolve().parent / "results"

DEFAULT_AGG_TIME = 30
DEFAULT_CAV_PCT = 50.0
RAMP_DELAY_S = 100.0


def generate_route_file(
    output_path: Path,
    demand_vph: int,
    episode_s: int,
    cav_pct: float = DEFAULT_CAV_PCT,
    seed: int = 42,
) -> None:
    """Write a .rou.xml with diversified fleet, 2 routes, 100s ramp delay."""
    from traffic_environment.vehicle_fleet import (
        generate_fleet_xml, pick_vehicle_type,
    )

    fleet_xml = generate_fleet_xml(seed=seed)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append("<routes>")
    lines.append(fleet_xml)
    lines.append('  <route id="mainline_through" '
                 'edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"/>')
    lines.append('  <route id="ramp_on_through" '
                 'edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')

    total_veh = int(demand_vph * episode_s / 3600)
    n_mainline = int(total_veh * 0.75)
    n_ramp = total_veh - n_mainline

    rng = np.random.RandomState(seed + 1000)
    vehicles = []

    def _add(count, route_id, t_offset, t_span):
        if count <= 0:
            return
        step = t_span / count
        for i in range(count):
            dep = t_offset + (i + 0.5) * step
            if dep > episode_s:
                break
            vehicles.append((dep, route_id))

    _add(n_mainline, "mainline_through", 0.0, float(episode_s))
    _add(n_ramp, "ramp_on_through", RAMP_DELAY_S, float(episode_s) - RAMP_DELAY_S)

    vehicles.sort(key=lambda v: v[0])

    for veh_id, (depart, route_id) in enumerate(vehicles):
        is_cav = rng.random() * 100.0 < cav_pct
        vtype = pick_vehicle_type(rng, is_cav=is_cav)
        lines.append(f'  <vehicle id="veh_{veh_id}" type="{vtype}" '
                     f'route="{route_id}" depart="{depart:.2f}" '
                     f'departPos="last" departLane="best" '
                     f'departSpeed="desired" insertionChecks="none"/>')

    lines.append("</routes>")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def generate_stochastic_route_file(
    output_path: Path,
    profile,  # DemandProfile from stochastic_demand
    cav_pct: float = DEFAULT_CAV_PCT,
    seed: int = 42,
) -> None:
    """Write a .rou.xml with diversified fleet from a stochastic DemandProfile."""
    from traffic_environment.vehicle_fleet import (
        generate_fleet_xml, pick_vehicle_type,
    )

    fleet_xml = generate_fleet_xml(seed=seed)

    rng = np.random.RandomState(seed + 1000)
    vehicles = []
    veh_id = 0

    T = len(profile.mainline_rates)
    for t in range(T):
        m_rate = float(profile.mainline_rates[t])
        if m_rate > 0 and rng.random() < m_rate:
            vehicles.append((float(t), "mainline_through", veh_id))
            veh_id += 1

        if t >= RAMP_DELAY_S:
            r_rate = float(profile.ramp_rates[t])
            if r_rate > 0 and rng.random() < r_rate:
                vehicles.append((float(t), "ramp_on_through", veh_id))
                veh_id += 1

    vehicles.sort(key=lambda v: v[0])

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append("<routes>")
    lines.append(fleet_xml)
    lines.append('  <route id="mainline_through" '
                 'edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"/>')
    lines.append('  <route id="ramp_on_through" '
                 'edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')
    # Route needed for anomaly ramp_spike injection
    lines.append('  <route id="ramp_route" '
                 'edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')

    for depart, route_id, vid in vehicles:
        is_cav = rng.random() * 100.0 < cav_pct
        vtype = pick_vehicle_type(rng, is_cav=is_cav)
        lines.append(f'  <vehicle id="veh_{vid}" type="{vtype}" '
                     f'route="{route_id}" depart="{depart:.2f}" '
                     f'departPos="last" departLane="best" '
                     f'departSpeed="desired" insertionChecks="none"/>')

    lines.append("</routes>")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def generate_sumocfg(
    cfg_path: Path,
    rou_path: Path,
    episode_s: int = 3600,
) -> None:
    """Write a .sumocfg pointing at the ramps_v1 network."""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{NET_FILE.resolve()}"/>
        <route-files value="{rou_path.resolve()}"/>
        <additional-files value="{DET_FILE.resolve()}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{episode_s}"/>
    </time>
</configuration>
"""
    cfg_path.write_text(content, encoding="utf-8")


def make_env(
    demand_vph: int,
    episode_s: int = 3600,
    cav_pct: float = DEFAULT_CAV_PCT,
    tmp_dir: Optional[Path] = None,
    seed: int = 42,
):
    """
    Create a fully-configured TrafficEnv with a live SUMO scenario.

    Returns (env, tmp_dir_path) — caller must clean up tmp_dir.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from sar_components.discovery import discover_components
    from core import (
        TrafficEnv,
        create_action_strategy,
        create_reward_function,
        create_state_representation,
    )

    discover_components()

    sar_config = {
        "max_flow_vph": 8000.0,
        "max_ramp_flow_vph": 2000.0,
        "ref_flow_vph": 6000.0,
        "speed_floor_kph": 50.0,
        "harmo_spatial_blend": 0.5,
        "throughput_threshold": 0.85,
        "reward_weights": {"w_h": 0.55, "w_q": 0.30, "w_a": 0.15},
    }

    if tmp_dir is None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="test_harmo_"))
    else:
        tmp_dir = Path(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

    rou_path = tmp_dir / "scenario.rou.xml"
    cfg_path = tmp_dir / "scenario.sumocfg"

    generate_route_file(rou_path, demand_vph, episode_s, cav_pct, seed)
    generate_sumocfg(cfg_path, rou_path, episode_s)

    state_repr = create_state_representation("r44_state_v1", sar_config)
    action_strat = create_action_strategy("r44_action_v1", {})
    reward_func = create_reward_function("r44_reward_v2", sar_config)

    env = TrafficEnv(
        sumo_cfg_path=str(cfg_path),
        state_repr=state_repr,
        action_strat=action_strat,
        reward_func=reward_func,
        episode_duration=episode_s,
        cav_percent=cav_pct / 100.0,
        aggregation_time=DEFAULT_AGG_TIME,
    )

    return env, tmp_dir
