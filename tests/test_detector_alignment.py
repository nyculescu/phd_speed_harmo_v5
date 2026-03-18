# tests/test_detector_alignment.py
"""
Detector ID alignment: verify every programmatically-generated detector
ID actually exists in the SUMO network.

The environment's _collect_metrics() silently catches exceptions when
detector IDs don't resolve.  This test catches that failure mode by
asserting that every ID resolves without exception.

Requires SUMO.
Run:  pytest tests/test_detector_alignment.py -v -s
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.sumo

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# Ensure traci is importable
_SUMO_TOOLS = os.path.join(os.environ.get("SUMO_HOME", "/usr/share/sumo"), "tools")
if _SUMO_TOOLS not in sys.path:
    sys.path.insert(0, _SUMO_TOOLS)

from tests._sumo_helpers import (
    generate_route_file, generate_sumocfg,
    NET_FILE, DET_FILE,
)

# Lane counts per segment — must match env_interact.py
_SEGMENT_LANES = {
    "seg_3_before": 3, "seg_2_before": 3, "seg_1_before": 3, "seg_0_before": 3,
    "seg_0_after": 4, "seg_1_after": 3,
    "ramp_on_approach": 1, "ramp_on_transition": 1, "ramp_on_merge": 1,
    "ramp_off_diverge": 1, "ramp_off_transition": 1, "ramp_off_departure": 1,
}

# Detector positions available in detectors_ramps_v1.add.xml
_ALL_POSITIONS = ["entry", "mid", "exit"]

# The env only reads "exit" position — this is the critical set.
_ENV_POSITION = "exit"


def _env_det_ids(seg: str, n_lanes: int):
    """Generate detector IDs matching what env_interact._det_ids() produces."""
    return [f"flow_loop_{seg}_{lane}_{_ENV_POSITION}" for lane in range(n_lanes)]


def _all_det_ids(seg: str, n_lanes: int):
    """Generate ALL detector IDs (entry + mid + exit) for comprehensive check."""
    ids = []
    for lane in range(n_lanes):
        for pos in _ALL_POSITIONS:
            ids.append(f"flow_loop_{seg}_{lane}_{pos}")
    return ids


class TestDetectorAlignment:

    def test_all_detector_ids_resolve(self, tmp_path):
        """Every programmatic detector ID should exist in SUMO."""
        import traci

        # Generate a minimal scenario just to boot SUMO
        rou_path = tmp_path / "det_test.rou.xml"
        cfg_path = tmp_path / "det_test.sumocfg"
        generate_route_file(rou_path, demand_vph=1000, episode_s=60, seed=1)
        generate_sumocfg(cfg_path, rou_path, episode_s=60)

        # Boot
        with socket.socket() as s:
            s.bind(("", 0))
            port = s.getsockname()[1]

        proc = subprocess.Popen(
            ["sumo", "-c", str(cfg_path), "--remote-port", str(port),
             "--no-step-log", "--no-warnings", "--start"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        traci.init(port=port, numRetries=10)

        # Advance one step so detectors are initialized
        traci.simulationStep()

        missing = []
        total = 0
        try:
            # Test the exact IDs that env_interact.py uses (exit position only)
            for seg, n_lanes in _SEGMENT_LANES.items():
                for det_id in _env_det_ids(seg, n_lanes):
                    total += 1
                    try:
                        traci.inductionloop.getLastIntervalVehicleNumber(det_id)
                    except Exception as e:
                        missing.append((det_id, str(e)))
        finally:
            try:
                traci.close()
            except Exception:
                pass
            proc.terminate()
            proc.wait(timeout=5)

        print(f"\n  Total detector IDs checked: {total}")
        print(f"  Missing/broken: {len(missing)}")
        if missing:
            for det_id, err in missing[:10]:  # show first 10
                print(f"    {det_id}: {err}")

        assert len(missing) == 0, (
            f"{len(missing)}/{total} detector IDs failed to resolve. "
            f"First: {missing[0][0]} — {missing[0][1]}"
        )
