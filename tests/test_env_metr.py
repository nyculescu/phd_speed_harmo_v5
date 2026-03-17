# tests/test_env_metr.py
"""
E1 / E3 sensor metric tests — SUMO 1.26 TraCI API coverage.

Purpose
-------
Verifies every TraCI getter available on induction-loop (E1) and
multi-entry-exit (E3) detectors that are defined in
``traffic_environment/sumo/loops_detectors_m43_v0.add.xml``.

Design for extensibility
------------------------
Each detector family (E1 / E3) has a *metric registry* — a list of
``E1Spec`` / ``E3Spec`` dataclass instances that describe one TraCI call:
the method name, expected Python return type, and valid value range.

To add a new metric in the future:
  1.  Append one entry to ``_E1_SPECS`` or ``_E3_SPECS``.
  2.  Done.  The parametrised test classes pick it up automatically.

No other code change is needed.

Detector inventory (all in loops_detectors_m43_v0.add.xml, freq=30 s)
----------------------------------------------------------------------
E1 — 48 induction loops (``<inductionLoop>``):
  seg_2_before  lanes 0-3  × {entry, mid, exit}  →  12 detectors
  seg_1_before  lanes 0-3  × {entry, mid, exit}  →  12 detectors
  seg_0_before  lanes 0-3  × {entry, mid, exit}  →  12 detectors
  seg_0_after   lanes 0-2  × {entry, mid, exit}  →  12 detectors
  Naming: flow_loop_{seg}_{lane}_{pos}

E3 — 4 multi-entry-exit zones (``<e3Detector>``):
  e3_seg_2_before  spans seg_2_before  (entry pos 0 → exit pos 1000)
  e3_seg_1_before  spans seg_1_before
  e3_seg_0_before  spans seg_0_before
  e3_corridor      spans seg_2_before entry → seg_0_after exit (full corridor)

TraCI API summary (SUMO 1.26)
-----------------------------
traci.inductionloop — key methods:
  Interval (last completed 30 s window):
    getLastIntervalVehicleNumber(id)   → int    vehicles that passed
    getLastIntervalMeanSpeed(id)       → float  m/s  (-1 = no vehicle)
    getLastIntervalOccupancy(id)       → float  %    time-fraction
    getLastIntervalVehicleIDs(id)      → tuple  vehicle ID strings
  Current interval (in-progress):
    getIntervalVehicleNumber(id)       → int
    getIntervalMeanSpeed(id)           → float  m/s
    getIntervalOccupancy(id)           → float  %
    getIntervalVehicleIDs(id)          → tuple
  Last simulation step (1 s):
    getLastStepVehicleNumber(id)       → int
    getLastStepMeanSpeed(id)           → float  m/s
    getLastStepOccupancy(id)           → float  %
    getLastStepVehicleIDs(id)          → tuple
    getLastStepMeanLength(id)          → float  m   (-1 = no vehicle)
  Per-vehicle detail:
    getVehicleData(id)                 → list[(id, length, entry, exit, vType)]
  Time since last detection:
    getTimeSinceDetection(id)          → float  s

traci.multientryexit — key methods:
  Interval (last completed 30 s window):
    getLastIntervalVehicleSum(id)           → int
    getLastIntervalMeanTravelTime(id)       → float  s  (-1 = no vehicle)
    getLastIntervalMeanTimeLoss(id)         → float  s  (-1 = no vehicle)
    getLastIntervalMeanHaltsPerVehicle(id)  → float  count
  Last simulation step (1 s):
    getLastStepVehicleNumber(id)       → int
    getLastStepMeanSpeed(id)           → float  m/s
    getLastStepVehicleIDs(id)          → tuple
    getLastStepHaltingNumber(id)       → int

Run
---
    # from the phd_speed_harmo_v5/ root:
    pytest tests/test_env_metr.py -v -s
    # or with the sumo marker:
    pytest -m sumo -v
"""
from __future__ import annotations

import csv
import dataclasses
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

import numpy as np
import pytest
import yaml

from sar_components.discovery import discover_components
from core import (
    TrafficEnv,
    create_action_strategy,
    create_reward_function,
    create_state_representation,
)
from traffic_environment.scenario_generator import _generate_single_scenario_pair_worker

discover_components()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_CONFIG_PATH  = Path(__file__).resolve().parents[1] / "configurations" / "_common_config.yaml"
_RESULTS_ROOT = Path(__file__).resolve().parent / "results"

# ---------------------------------------------------------------------------
# Detector ID registries
# ---------------------------------------------------------------------------

_US_SEGS      = ("seg_2_before", "seg_1_before", "seg_0_before")
_US_LANE_CNT  = 4
_DS_SEG       = "seg_0_after"
_DS_LANE_CNT  = 3
_POSITIONS    = ("entry", "mid", "exit")

E1_IDS: Tuple[str, ...] = tuple(
    f"flow_loop_{seg}_{lane}_{pos}"
    for seg  in _US_SEGS
    for lane in range(_US_LANE_CNT)
    for pos  in _POSITIONS
) + tuple(
    f"flow_loop_{_DS_SEG}_{lane}_{pos}"
    for lane in range(_DS_LANE_CNT)
    for pos  in _POSITIONS
)

E3_IDS: Tuple[str, ...] = (
    "e3_seg_2_before",
    "e3_seg_1_before",
    "e3_seg_0_before",
    "e3_corridor",
)

# ---------------------------------------------------------------------------
# Metric spec dataclasses
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class E1Spec:
    """Describes one TraCI getter on traci.inductionloop."""
    name: str           # human-readable name (used as pytest param ID)
    fn:   str           # method name on traci.inductionloop
    ret_type: type      # expected Python type of return value
    lo: Optional[float] # minimum valid value, or None (skip check)
    hi: Optional[float] # maximum valid value, or None (skip check)
    description: str    # one-line description for documentation


@dataclasses.dataclass(frozen=True)
class E3Spec:
    """Describes one TraCI getter on traci.multientryexit."""
    name: str
    fn:   str
    ret_type: type
    lo: Optional[float]
    hi: Optional[float]
    description: str


# ---------------------------------------------------------------------------
# E1 metric registry
# To add a metric: append one E1Spec entry.
# ---------------------------------------------------------------------------

_E1_SPECS = [
    # ── Last completed interval (30 s window) ────────────────────────────────
    E1Spec(
        name        = "last_interval_vehicle_number",
        fn          = "getLastIntervalVehicleNumber",
        ret_type    = int,
        lo          = 0,
        hi          = None,
        description = "Vehicles that passed during the last completed 30 s window.",
    ),
    E1Spec(
        name        = "last_interval_mean_speed",
        fn          = "getLastIntervalMeanSpeed",
        ret_type    = float,
        lo          = -1.0,   # -1.0 when no vehicle passed
        hi          = None,
        description = "Mean speed (m/s) in last interval; -1.0 if no vehicles.",
    ),
    E1Spec(
        name        = "last_interval_occupancy",
        fn          = "getLastIntervalOccupancy",
        ret_type    = float,
        lo          = 0.0,
        hi          = 100.0,
        description = "Fraction of interval time detector was occupied (%).",
    ),
    # ── Current in-progress interval ─────────────────────────────────────────
    E1Spec(
        name        = "interval_vehicle_number",
        fn          = "getIntervalVehicleNumber",
        ret_type    = int,
        lo          = 0,
        hi          = None,
        description = "Vehicles that passed during the current in-progress interval.",
    ),
    E1Spec(
        name        = "interval_mean_speed",
        fn          = "getIntervalMeanSpeed",
        ret_type    = float,
        lo          = -1.0,
        hi          = None,
        description = "Mean speed (m/s) in current interval; -1.0 if no vehicles.",
    ),
    E1Spec(
        name        = "interval_occupancy",
        fn          = "getIntervalOccupancy",
        ret_type    = float,
        lo          = 0.0,
        hi          = 100.0,
        description = "Occupancy (%) in current in-progress interval.",
    ),
    # ── Last simulation step (1 s) ────────────────────────────────────────────
    E1Spec(
        name        = "last_step_vehicle_number",
        fn          = "getLastStepVehicleNumber",
        ret_type    = int,
        lo          = 0,
        hi          = None,
        description = "Vehicles on detector during the last 1 s simulation step.",
    ),
    E1Spec(
        name        = "last_step_mean_speed",
        fn          = "getLastStepMeanSpeed",
        ret_type    = float,
        lo          = -1.0,
        hi          = None,
        description = "Mean speed (m/s) in last sim step; -1.0 if no vehicles.",
    ),
    E1Spec(
        name        = "last_step_occupancy",
        fn          = "getLastStepOccupancy",
        ret_type    = float,
        lo          = 0.0,
        hi          = 100.0,
        description = "Occupancy (%) during the last sim step.",
    ),
    E1Spec(
        name        = "last_step_mean_length",
        fn          = "getLastStepMeanLength",
        ret_type    = float,
        lo          = -1.0,   # -1.0 when no vehicle
        hi          = None,
        description = "Mean vehicle length (m) in last sim step; -1.0 if empty.",
    ),
    # ── Time since last detection ─────────────────────────────────────────────
    E1Spec(
        name        = "time_since_detection",
        fn          = "getTimeSinceDetection",
        ret_type    = float,
        lo          = 0.0,
        hi          = None,
        description = "Seconds elapsed since a vehicle last triggered the detector.",
    ),
]


# ---------------------------------------------------------------------------
# E3 metric registry
# To add a metric: append one E3Spec entry.
# ---------------------------------------------------------------------------

_E3_SPECS = [
    # ── Last completed interval (30 s window) ────────────────────────────────
    E3Spec(
        name        = "last_interval_vehicle_sum",
        fn          = "getLastIntervalVehicleSum",
        ret_type    = int,
        lo          = 0,
        hi          = None,
        description = "Vehicles that passed through the zone in the last interval.",
    ),
    E3Spec(
        name        = "last_interval_mean_travel_time",
        fn          = "getLastIntervalMeanTravelTime",
        ret_type    = float,
        lo          = -1.0,   # -1.0 when no vehicle
        hi          = None,
        description = "Mean time (s) vehicles spent inside the zone; -1.0 if empty.",
    ),
    E3Spec(
        name        = "last_interval_mean_time_loss",
        fn          = "getLastIntervalMeanTimeLoss",
        ret_type    = float,
        lo          = -1.0,   # -1.0 when no vehicle; negative = vehicle gained time
        hi          = None,
        description = "Mean time loss (s) per vehicle due to congestion; -1.0 if empty.",
    ),
    E3Spec(
        name        = "last_interval_mean_halts_per_vehicle",
        fn          = "getLastIntervalMeanHaltsPerVehicle",
        ret_type    = float,
        lo          = -1.0,   # -1.0 when no vehicle
        hi          = None,
        description = "Mean number of full stops per vehicle in last interval.",
    ),
    # ── Last simulation step (1 s) ────────────────────────────────────────────
    E3Spec(
        name        = "last_step_vehicle_number",
        fn          = "getLastStepVehicleNumber",
        ret_type    = int,
        lo          = 0,
        hi          = None,
        description = "Vehicles inside the zone during the last sim step.",
    ),
    E3Spec(
        name        = "last_step_mean_speed",
        fn          = "getLastStepMeanSpeed",
        ret_type    = float,
        lo          = -1.0,
        hi          = None,
        description = "Mean speed (m/s) of vehicles in zone during last sim step.",
    ),
    E3Spec(
        name        = "last_step_halting_number",
        fn          = "getLastStepHaltingNumber",
        ret_type    = int,
        lo          = 0,
        hi          = None,
        description = "Number of stationary vehicles in zone during last sim step.",
    ),
]


# ---------------------------------------------------------------------------
# Pytest markers and skip condition
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.sumo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_sar_config(cfg: dict) -> dict:
    sc = cfg.get("sar_config", {})
    weights = sc.get("reward_weights", {})
    return {
        "max_flow_vph":   sc.get("max_flow_vph",  4000.0),
        "max_tts_s":      sc.get("max_tts_s",     5000.0),
        "ref_flow_vph":   sc.get("ref_flow_vph",  2520.0),
        "reward_weights": {
            "w_v": weights.get("w_v", 0.50),
            "w_q": weights.get("w_q", 0.35),
            "w_a": weights.get("w_a", 0.15),
        },
    }


def _result_dir(version: str) -> Path:
    ts  = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    out = _RESULTS_ROOT / f"{version.replace('_', '-')}_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    return out


# ---------------------------------------------------------------------------
# Module-scoped fixture: running SUMO env
#
# The fixture generates one scenario, boots SUMO, resets the env, runs two
# full aggregation steps so at least one completed interval is available,
# then keeps TraCI connected for the duration of the test session.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live_env(tmp_path_factory):
    """Yield a TrafficEnv that is mid-episode with TraCI connected."""
    tmpdir  = tmp_path_factory.mktemp("metr_scenario")
    rou_dir = tmpdir / "flows"
    cfg_dir = tmpdir / "configs"
    rou_dir.mkdir()
    cfg_dir.mkdir()

    cfg      = _load_config()
    cav_pct  = float(cfg.get("scenario_generation", {}).get("cavs_percentage", 50.0))
    topology = cfg.get("scenario_generation", {}).get("network_topology", "merge_4_to_3_v0")
    agg_time = int(cfg.get("sumo", {}).get("aggregation_time", 30))

    _generate_single_scenario_pair_worker({
        "index":            0,
        "prefix":           "metr_test",
        "demand_vph":       2000,
        "episode_duration": 300,
        "cav_percentage":   cav_pct,
        "network_topology": topology,
        "rou_output_dir":   str(rou_dir),
        "cfg_output_dir":   str(cfg_dir),
        "pattern":          "flat",
        "bin_seconds":      agg_time,
    })

    cfg_files = list(cfg_dir.glob("*.sumocfg"))
    assert cfg_files, "Scenario generation produced no .sumocfg"

    sar_config = _build_sar_config(cfg)
    sar_names  = cfg.get("sar", {})
    env = TrafficEnv(
        sumo_cfg_path    = str(cfg_files[0]),
        state_repr       = create_state_representation(sar_names.get("state",  "m43_state_v0"), sar_config),
        action_strat     = create_action_strategy(     sar_names.get("action", "m43_action_v0"), {}),
        reward_func      = create_reward_function(     sar_names.get("reward", "m43_reward_v0"), sar_config),
        episode_duration = 300,
        cav_percent      = cav_pct / 100.0,
        aggregation_time = agg_time,
    )

    env.reset()
    # Advance two full aggregation windows so getLastInterval* has data.
    env.step(3)
    env.step(3)

    yield env

    env.close()


# ---------------------------------------------------------------------------
# TestDetectorPresence
# Confirms the simulation loaded every expected detector ID.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo binary not found on PATH")
class TestDetectorPresence:

    def test_all_e1_ids_present(self, live_env):
        import traci
        live_ids = set(traci.inductionloop.getIDList())
        missing  = [d for d in E1_IDS if d not in live_ids]
        assert not missing, f"Missing E1 detector IDs: {missing}"

    def test_all_e3_ids_present(self, live_env):
        import traci
        live_ids = set(traci.multientryexit.getIDList())
        missing  = [d for d in E3_IDS if d not in live_ids]
        assert not missing, f"Missing E3 detector IDs: {missing}"

    def test_e1_count(self, live_env):
        import traci
        assert traci.inductionloop.getIDCount() >= len(E1_IDS)

    def test_e3_count(self, live_env):
        import traci
        assert traci.multientryexit.getIDCount() >= len(E3_IDS)


# ---------------------------------------------------------------------------
# TestE1Metrics
# Parametrised over _E1_SPECS; each spec is tested against all 48 E1 IDs.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo binary not found on PATH")
class TestE1Metrics:

    @pytest.mark.parametrize("spec", _E1_SPECS, ids=lambda s: s.name)
    def test_type_and_range(self, live_env, spec):
        import traci
        fn = getattr(traci.inductionloop, spec.fn)
        for det_id in E1_IDS:
            val = fn(det_id)
            assert isinstance(val, spec.ret_type), (
                f"[{spec.name}] detector={det_id}: expected {spec.ret_type.__name__}, "
                f"got {type(val).__name__} (value={val!r})"
            )
            if spec.lo is not None:
                assert val >= spec.lo, (
                    f"[{spec.name}] detector={det_id}: value {val} < lo={spec.lo}"
                )
            if spec.hi is not None:
                assert val <= spec.hi, (
                    f"[{spec.name}] detector={det_id}: value {val} > hi={spec.hi}"
                )

    def test_last_interval_vehicle_ids_are_strings(self, live_env):
        """Vehicle IDs returned by getLastIntervalVehicleIDs must all be str."""
        import traci
        for det_id in E1_IDS:
            ids = traci.inductionloop.getLastIntervalVehicleIDs(det_id)
            assert isinstance(ids, (tuple, list)), (
                f"detector={det_id}: expected tuple/list, got {type(ids).__name__}"
            )
            for veh_id in ids:
                assert isinstance(veh_id, str), (
                    f"detector={det_id}: vehicle ID {veh_id!r} is not a string"
                )

    def test_last_step_vehicle_ids_are_strings(self, live_env):
        """Vehicle IDs returned by getLastStepVehicleIDs must all be str."""
        import traci
        for det_id in E1_IDS:
            ids = traci.inductionloop.getLastStepVehicleIDs(det_id)
            assert isinstance(ids, (tuple, list))
            for veh_id in ids:
                assert isinstance(veh_id, str)

    def test_vehicle_data_structure(self, live_env):
        """getVehicleData returns a list; each record is a 5-element sequence."""
        import traci
        for det_id in E1_IDS:
            records = traci.inductionloop.getVehicleData(det_id)
            assert isinstance(records, (list, tuple)), (
                f"detector={det_id}: expected list, got {type(records).__name__}"
            )
            for rec in records:
                assert len(rec) == 5, (
                    f"detector={det_id}: expected 5-element record, got {len(rec)}: {rec}"
                )
                veh_id, length, entry_time, exit_time, vtype = rec
                assert isinstance(veh_id,     str),   f"veh_id not str: {veh_id!r}"
                assert isinstance(length,     float),  f"length not float: {length!r}"
                assert isinstance(entry_time, float),  f"entry_time not float: {entry_time!r}"
                assert isinstance(exit_time,  float),  f"exit_time not float: {exit_time!r}"
                assert isinstance(vtype,      str),    f"vtype not str: {vtype!r}"
                assert length     >  0.0,     f"vehicle length must be > 0, got {length}"
                assert entry_time >= 0.0,     f"entry_time must be >= 0, got {entry_time}"
                # exit_time is -1.0 if vehicle is still on detector
                assert exit_time  >= -1.0,    f"exit_time must be >= -1.0, got {exit_time}"

    def test_lane_id_is_string(self, live_env):
        """getLaneID must return a non-empty string for every detector."""
        import traci
        for det_id in E1_IDS:
            lane = traci.inductionloop.getLaneID(det_id)
            assert isinstance(lane, str) and lane, (
                f"detector={det_id}: getLaneID returned {lane!r}"
            )

    def test_position_is_non_negative(self, live_env):
        """getPosition must return a non-negative float for every detector."""
        import traci
        for det_id in E1_IDS:
            pos = traci.inductionloop.getPosition(det_id)
            assert isinstance(pos, float), (
                f"detector={det_id}: getPosition returned {type(pos).__name__}"
            )
            assert pos >= 0.0, (
                f"detector={det_id}: position must be >= 0, got {pos}"
            )


# ---------------------------------------------------------------------------
# TestE3Metrics
# Parametrised over _E3_SPECS; each spec is tested against all 4 E3 zones.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo binary not found on PATH")
class TestE3Metrics:

    @pytest.mark.parametrize("spec", _E3_SPECS, ids=lambda s: s.name)
    def test_type_and_range(self, live_env, spec):
        import traci
        fn = getattr(traci.multientryexit, spec.fn)
        for det_id in E3_IDS:
            val = fn(det_id)
            assert isinstance(val, spec.ret_type), (
                f"[{spec.name}] zone={det_id}: expected {spec.ret_type.__name__}, "
                f"got {type(val).__name__} (value={val!r})"
            )
            if spec.lo is not None:
                assert val >= spec.lo, (
                    f"[{spec.name}] zone={det_id}: value {val} < lo={spec.lo}"
                )
            if spec.hi is not None:
                assert val <= spec.hi, (
                    f"[{spec.name}] zone={det_id}: value {val} > hi={spec.hi}"
                )

    def test_last_step_vehicle_ids_are_strings(self, live_env):
        """getLastStepVehicleIDs must return a sequence of str."""
        import traci
        for det_id in E3_IDS:
            ids = traci.multientryexit.getLastStepVehicleIDs(det_id)
            assert isinstance(ids, (tuple, list))
            for veh_id in ids:
                assert isinstance(veh_id, str), (
                    f"zone={det_id}: vehicle ID {veh_id!r} is not a string"
                )

    def test_entry_lanes_are_strings(self, live_env):
        """getEntryLanes must return a non-empty sequence of lane ID strings."""
        import traci
        for det_id in E3_IDS:
            lanes = traci.multientryexit.getEntryLanes(det_id)
            assert isinstance(lanes, (tuple, list)) and len(lanes) > 0, (
                f"zone={det_id}: getEntryLanes returned {lanes!r}"
            )
            for lane in lanes:
                assert isinstance(lane, str) and lane, (
                    f"zone={det_id}: entry lane {lane!r} is not a string"
                )

    def test_exit_lanes_are_strings(self, live_env):
        """getExitLanes must return a non-empty sequence of lane ID strings."""
        import traci
        for det_id in E3_IDS:
            lanes = traci.multientryexit.getExitLanes(det_id)
            assert isinstance(lanes, (tuple, list)) and len(lanes) > 0, (
                f"zone={det_id}: getExitLanes returned {lanes!r}"
            )
            for lane in lanes:
                assert isinstance(lane, str) and lane

    def test_entry_positions_are_non_negative(self, live_env):
        """getEntryPositions must return non-negative floats."""
        import traci
        for det_id in E3_IDS:
            positions = traci.multientryexit.getEntryPositions(det_id)
            assert isinstance(positions, (tuple, list)) and len(positions) > 0
            for pos in positions:
                assert isinstance(pos, float) and pos >= 0.0, (
                    f"zone={det_id}: entry position {pos!r} invalid"
                )

    def test_exit_positions_are_non_negative(self, live_env):
        """getExitPositions must return non-negative floats."""
        import traci
        for det_id in E3_IDS:
            positions = traci.multientryexit.getExitPositions(det_id)
            assert isinstance(positions, (tuple, list)) and len(positions) > 0
            for pos in positions:
                assert isinstance(pos, float) and pos >= 0.0, (
                    f"zone={det_id}: exit position {pos!r} invalid"
                )

    def test_corridor_spans_full_network(self, live_env):
        """e3_corridor must have entry lanes on seg_2_before and exit on seg_0_after."""
        import traci
        entries = traci.multientryexit.getEntryLanes("e3_corridor")
        exits   = traci.multientryexit.getExitLanes("e3_corridor")
        assert any("seg_2_before" in e for e in entries), (
            f"e3_corridor entries do not include seg_2_before lanes: {entries}"
        )
        assert any("seg_0_after" in e for e in exits), (
            f"e3_corridor exits do not include seg_0_after lanes: {exits}"
        )


# ---------------------------------------------------------------------------
# TestMetricSnapshot
# Runs a full episode and dumps all E1 + E3 metrics at each step to CSV.
# Serves as a regression baseline and as diagnostic output.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo binary not found on PATH")
class TestMetricSnapshot:

    def test_snapshot_full_episode(self, tmp_path):
        """
        Run a complete short episode and write a per-step CSV of every
        E1/E3 metric for every detector.  Fails only if a metric raises
        an exception or returns an obviously invalid value.
        """
        import traci

        cfg       = _load_config()
        version   = "m43_v0"
        agg_time  = int(cfg.get("sumo", {}).get("aggregation_time", 30))
        cav_pct   = float(cfg.get("scenario_generation", {}).get("cavs_percentage", 50.0))
        sar_config = _build_sar_config(cfg)
        sar_names  = cfg.get("sar", {})

        rou_dir = tmp_path / "flows"
        cfg_dir = tmp_path / "configs"
        rou_dir.mkdir(); cfg_dir.mkdir()
        _generate_single_scenario_pair_worker({
            "index": 0, "prefix": "snap", "demand_vph": 2000,
            "episode_duration": 300, "cav_percentage": cav_pct,
            "network_topology": "merge_4_to_3_v0",
            "rou_output_dir": str(rou_dir), "cfg_output_dir": str(cfg_dir),
            "pattern": "flat", "bin_seconds": agg_time,
        })
        cfg_files = list(cfg_dir.glob("*.sumocfg"))
        assert cfg_files

        env = TrafficEnv(
            sumo_cfg_path    = str(cfg_files[0]),
            state_repr       = create_state_representation(sar_names.get("state",  "m43_state_v0"), sar_config),
            action_strat     = create_action_strategy(     sar_names.get("action", "m43_action_v0"), {}),
            reward_func      = create_reward_function(     sar_names.get("reward", "m43_reward_v0"), sar_config),
            episode_duration = 300,
            cav_percent      = cav_pct / 100.0,
            aggregation_time = agg_time,
        )

        result_dir = _result_dir(version)
        rows       = []

        try:
            env.reset()
            terminated = False
            step = 0

            while not terminated:
                _, _, terminated, _, _ = env.step(3)
                step += 1
                row: dict = {"step": step}

                # Collect E1 interval metrics for every detector
                for det_id in E1_IDS:
                    row[f"e1_{det_id}_count"] = traci.inductionloop.getLastIntervalVehicleNumber(det_id)
                    row[f"e1_{det_id}_speed"] = traci.inductionloop.getLastIntervalMeanSpeed(det_id)
                    row[f"e1_{det_id}_occ"]   = traci.inductionloop.getLastIntervalOccupancy(det_id)

                # Collect E3 interval metrics for every zone
                for det_id in E3_IDS:
                    row[f"e3_{det_id}_sum"]        = traci.multientryexit.getLastIntervalVehicleSum(det_id)
                    row[f"e3_{det_id}_travel_time"] = traci.multientryexit.getLastIntervalMeanTravelTime(det_id)
                    row[f"e3_{det_id}_time_loss"]   = traci.multientryexit.getLastIntervalMeanTimeLoss(det_id)
                    row[f"e3_{det_id}_halts"]       = traci.multientryexit.getLastIntervalMeanHaltsPerVehicle(det_id)

                rows.append(row)

        finally:
            env.close()

        assert rows, "No steps were recorded"

        csv_path = result_dir / "metric_snapshot.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
