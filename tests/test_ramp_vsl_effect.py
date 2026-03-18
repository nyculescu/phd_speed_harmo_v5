# tests/test_ramp_vsl_effect.py
"""
Ramp VSL independence verification.

Runs two episodes with identical mainline VSL (120 kph = no restriction)
but different ramp VSL (90 vs 40 kph).  Verifies that the ramp action
dimension has a measurable effect on ramp approach speed.

Requires SUMO.
Run:  pytest tests/test_ramp_vsl_effect.py -v -s
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.sumo

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# Ensure traci is importable
_SUMO_TOOLS = os.path.join(os.environ.get("SUMO_HOME", "/usr/share/sumo"), "tools")
if _SUMO_TOOLS not in sys.path:
    sys.path.insert(0, _SUMO_TOOLS)

from tests._sumo_helpers import (
    make_env, generate_route_file, generate_sumocfg,
    NET_FILE, DET_FILE, DEFAULT_AGG_TIME,
)

_DEMAND = 6500
_EPISODE_S = 3600


def _run_episode_with_ramp_tracking(
    mainline_kph: float,
    ramp_kph: float,
    tmp_dir: Path,
) -> dict:
    """Run an episode and track ramp_on_transition CAV speeds via TraCI."""
    import traci

    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    rou_path = tmp_dir / "scenario.rou.xml"
    cfg_path = tmp_dir / "scenario.sumocfg"

    generate_route_file(rou_path, _DEMAND, _EPISODE_S, cav_pct=50.0, seed=42)
    generate_sumocfg(cfg_path, rou_path, _EPISODE_S)

    # Boot SUMO
    import subprocess, socket

    def _free_port():
        with socket.socket() as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    port = _free_port()
    proc = subprocess.Popen(
        ["sumo", "-c", str(cfg_path), "--remote-port", str(port),
         "--no-step-log", "--no-warnings", "--start"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    traci.init(port=port, numRetries=10)

    mainline_ms = mainline_kph / 3.6
    ramp_ms = ramp_kph / 3.6
    duration = float(DEFAULT_AGG_TIME)

    cav_ramp_speeds = []
    hdv_ramp_speeds = []

    try:
        for sim_step in range(_EPISODE_S):
            traci.simulationStep()

            for veh_id in traci.vehicle.getIDList():
                try:
                    edge = traci.vehicle.getRoadID(veh_id)
                    vtype = traci.vehicle.getTypeID(veh_id)
                    is_cav = "cav" in vtype.lower()

                    # Track speeds on ramp_on_transition
                    if edge == "ramp_on_transition":
                        spd_ms = traci.vehicle.getSpeed(veh_id)
                        spd_kph = spd_ms * 3.6
                        if is_cav:
                            cav_ramp_speeds.append(spd_kph)
                        else:
                            hdv_ramp_speeds.append(spd_kph)

                    # Apply control
                    if not is_cav:
                        continue
                    if edge in ("seg_0_before", "seg_1_before", "seg_2_before"):
                        traci.vehicle.slowDown(veh_id, mainline_ms, duration)
                    elif edge in ("ramp_on_approach", "ramp_on_transition"):
                        traci.vehicle.slowDown(veh_id, ramp_ms, duration)
                except Exception:
                    continue
    finally:
        try:
            traci.close()
        except Exception:
            pass
        proc.terminate()
        proc.wait(timeout=5)

    return {
        "cav_ramp_mean": float(np.mean(cav_ramp_speeds)) if cav_ramp_speeds else 0.0,
        "hdv_ramp_mean": float(np.mean(hdv_ramp_speeds)) if hdv_ramp_speeds else 0.0,
        "cav_ramp_count": len(cav_ramp_speeds),
        "hdv_ramp_count": len(hdv_ramp_speeds),
    }


class TestRampVSLEffect:

    def test_ramp_vsl_independence(self, tmp_path):
        """Ramp VSL 40 vs 90 should produce measurably different CAV speeds."""
        result_no_restrict = _run_episode_with_ramp_tracking(
            mainline_kph=120.0, ramp_kph=90.0,
            tmp_dir=tmp_path / "ramp90",
        )
        result_restrict = _run_episode_with_ramp_tracking(
            mainline_kph=120.0, ramp_kph=40.0,
            tmp_dir=tmp_path / "ramp40",
        )

        cav_no = result_no_restrict["cav_ramp_mean"]
        cav_yes = result_restrict["cav_ramp_mean"]
        diff = cav_no - cav_yes

        print(f"\n  Ramp 90 kph: CAV mean = {cav_no:.1f} kph "
              f"(n={result_no_restrict['cav_ramp_count']})")
        print(f"  Ramp 40 kph: CAV mean = {cav_yes:.1f} kph "
              f"(n={result_restrict['cav_ramp_count']})")
        print(f"  Difference:  {diff:+.1f} kph")

        hdv_no = result_no_restrict["hdv_ramp_mean"]
        hdv_yes = result_restrict["hdv_ramp_mean"]
        print(f"  HDV no-restrict: {hdv_no:.1f} kph")
        print(f"  HDV restrict:    {hdv_yes:.1f} kph")

        # Ramp VSL should produce measurably different outcomes.
        # Direction may be counterintuitive (restricting ramp can reduce
        # congestion → surviving vehicles move faster), so check absolute diff.
        abs_diff = abs(diff)
        assert abs_diff > 5.0, (
            f"Ramp VSL has negligible effect on CAV speed "
            f"(|diff| = {abs_diff:.1f} kph < 5 kph). "
            f"The ramp action dimension may not be learnable."
        )

        if abs_diff < 10.0:
            print(
                f"\n  WARNING: Ramp VSL effect is moderate ({abs_diff:.1f} kph). "
                f"Consider whether the ramp action dimension provides "
                f"enough signal for the critic to learn."
            )
