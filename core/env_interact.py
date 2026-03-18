# core/env_interact.py
"""
Gymnasium environment wrapping a SUMO ramps_v1 simulation.

Design
------
- One env step = one E1 aggregation window (``aggregation_time`` seconds).
- Speed limits are posted to controlled segments (mainline + ramp transition).
- CAVs receive ``traci.vehicle.slowDown()`` at every SUMO step.
- ``sumo_cfg_path=None`` → dry-run mode: no SUMO process, all metrics zero.
"""
from __future__ import annotations

import logging
import socket
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

import gymnasium as gym
import numpy as np

from .constants import MAX_SPEED_KPH
from .env_metrics import TrafficMetrics
from .sar_frame import ActionStrategy, RewardFunction, StateRepresentation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ramps_v1 topology constants
# ---------------------------------------------------------------------------

# All segments with their lane counts.
_SEGMENT_LANES: Dict[str, int] = {
    "seg_3_before": 3,
    "seg_2_before": 3,
    "seg_1_before": 3,
    "seg_0_before": 3,
    "seg_0_after": 4,
    "seg_1_after": 3,
    "ramp_on_approach": 1,
    "ramp_on_transition": 1,
    "ramp_on_merge": 1,
    "ramp_off_diverge": 1,
    "ramp_off_transition": 1,
    "ramp_off_departure": 1,
}

# Segments that receive posted speed limits from the action.
_CONTROLLED_SEGS: Tuple[str, ...] = (
    "seg_0_before", "seg_1_before", "seg_2_before", "ramp_on_transition",
)

# E1 detector position to read.
_DET_POS: str = "exit"

# Edges where CAV slowDown() is applied.  CAVs on any other edge drive at
# free-flow speed — this is the "release point" design:
#   - Mainline: seg_2/1/0_before only (upstream of merge)
#   - Ramp: approach + transition only (merge geometry dominates at ramp_on_merge)
#   - seg_0_after / seg_1_after: FREE — CAVs accelerate back after the merge
_MAINLINE_CONTROLLED_EDGES: Tuple[str, ...] = (
    "seg_0_before", "seg_1_before", "seg_2_before",
)
_RAMP_CONTROLLED_EDGES: Tuple[str, ...] = (
    "ramp_on_approach", "ramp_on_transition",
)


def _det_ids(seg: str, n_lanes: int) -> List[str]:
    return [f"flow_loop_{seg}_{i}_{_DET_POS}" for i in range(n_lanes)]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# TrafficEnv
# ---------------------------------------------------------------------------

class TrafficEnv(gym.Env):
    """
    Gymnasium environment for the ramps_v1 SUMO network.

    Parameters
    ----------
    sumo_cfg_path:
        Absolute path to the ``.sumocfg`` file.  Pass ``None`` for dry-run.
    state_repr:
        Instantiated :class:`~core.sar_frame.StateRepresentation`.
    action_strat:
        Instantiated :class:`~core.sar_frame.ActionStrategy`.
    reward_func:
        Instantiated :class:`~core.sar_frame.RewardFunction`.
    episode_duration:
        Episode length in simulation seconds.
    cav_percent:
        Fraction of vehicles that are CAVs (0.0–1.0).
    aggregation_time:
        E1 window and env-step duration in seconds.
    """

    metadata: Dict[str, Any] = {"render_modes": []}

    def __init__(
        self,
        sumo_cfg_path: Optional[str],
        state_repr: StateRepresentation,
        action_strat: ActionStrategy,
        reward_func: RewardFunction,
        episode_duration: int,
        cav_percent: float = 0.5,
        aggregation_time: int = 30,
    ) -> None:
        super().__init__()

        self.sumo_cfg_path = sumo_cfg_path
        self.dry_run: bool = sumo_cfg_path is None
        self.state_repr = state_repr
        self.action_strat = action_strat
        self.reward_func = reward_func
        self.episode_duration = int(episode_duration)
        self.cav_percent = float(cav_percent)
        self.aggregation_time = int(aggregation_time)

        self._steps_per_window: int = self.aggregation_time
        self._max_steps: int = self.episode_duration // self.aggregation_time

        self.observation_space = self.state_repr.get_observation_space()
        self.action_space = self.action_strat.get_action_space()

        self._sumo_proc: Optional[subprocess.Popen] = None
        self._port: int = 0
        self._step_count: int = 0
        self._metrics: TrafficMetrics = TrafficMetrics()

    # ------------------------------------------------------------------
    # gymnasium interface
    # ------------------------------------------------------------------

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self._close_sumo()
        self._step_count = 0
        self._metrics = TrafficMetrics()
        self.state_repr.reset()
        self.action_strat.reset()

        if not self.dry_run:
            self._start_sumo()
            self._advance_sumo(self._steps_per_window)
            self._collect_metrics()

        obs = self._make_obs()
        return obs, {}

    def step(
        self,
        action: Any,
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        # 1. Apply action → speed limits (m/s per segment)
        speed_limits_ms, penalty, pattern = self.action_strat.apply_action(
            action, self._metrics
        )

        # 2. Update control bookkeeping
        self._metrics.prev_action = (
            self._metrics.action.copy() if self._metrics.action is not None else None
        )
        if isinstance(action, np.ndarray):
            self._metrics.action = action.copy()
        else:
            self._metrics.action = np.array([action], dtype=np.float32)

        for i, seg in enumerate(_CONTROLLED_SEGS):
            limit_ms = speed_limits_ms.get(seg, MAX_SPEED_KPH / 3.6)
            self._metrics.current_speed_limits[i] = limit_ms * 3.6  # kph

        # 3. Advance simulation (pure Lagrangian: only CAV slowDown, no lane setMaxSpeed)
        if not self.dry_run:
            self._advance_sumo(self._steps_per_window)
            self._collect_metrics()

        self._step_count += 1
        self._metrics.simulation_step = self._step_count * self.aggregation_time

        # 4. Build observation and reward
        obs = self._make_obs()
        reward_signal = self.reward_func.calculate(self._metrics)
        reward = float(reward_signal.total) + penalty
        terminated = self._step_count >= self._max_steps

        return obs, reward, terminated, False, {
            "reward_components": reward_signal.components,
            "action_pattern": pattern,
            "sim_time": float(self._metrics.simulation_step),
        }

    def close(self) -> None:
        self._close_sumo()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_obs(self) -> np.ndarray:
        context = {
            "sim_time": float(self._step_count * self.aggregation_time),
            "episode_duration": float(self.episode_duration),
        }
        raw = self.state_repr.build_state(self._metrics, context=context)
        return self.state_repr.preprocess_state(raw)

    # ------------------------------------------------------------------
    # SUMO lifecycle
    # ------------------------------------------------------------------

    def _start_sumo(self) -> None:
        import traci

        self._port = _free_port()
        cmd = [
            "sumo",
            "-c", str(self.sumo_cfg_path),
            "--remote-port", str(self._port),
            "--no-step-log",
            "--no-warnings",
            "--start",
        ]
        self._sumo_proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        traci.init(port=self._port, numRetries=10)
        logger.debug("SUMO started on port %d", self._port)

    def _close_sumo(self) -> None:
        if self.dry_run:
            return
        try:
            import traci
            traci.close()
        except Exception:
            pass
        if self._sumo_proc is not None:
            try:
                self._sumo_proc.terminate()
                self._sumo_proc.wait(timeout=5)
            except Exception:
                pass
            self._sumo_proc = None

    def _advance_sumo(self, n_steps: int) -> None:
        import traci

        mainline_limit_ms = self._metrics.current_speed_limits[0] / 3.6
        ramp_limit_ms = self._metrics.current_speed_limits[3] / 3.6
        for _ in range(n_steps):
            traci.simulationStep()
            if self.cav_percent > 0.0:
                self._apply_cav_slowdown(mainline_limit_ms, ramp_limit_ms)

    # ------------------------------------------------------------------
    # Speed control
    # ------------------------------------------------------------------

    # _apply_segment_limits() removed — pure Lagrangian control (v5 paradigm).
    # HDVs slow down via car-following behind decelerating CAVs, not via
    # lane speed caps. See docs/slowDown_argument.md for rationale.
    #
    # TODO (future iteration): re-introduce as a secondary effect for HDVs
    # with 5 kph granularity rounded up, updated every 5 minutes based on
    # current traffic state. This would simulate advisory VSL signs for
    # HDVs that are ahead of all CAVs on their lane.

    def _apply_cav_slowdown(
        self, mainline_limit_ms: float, ramp_limit_ms: float
    ) -> None:
        """Issue slowDown() to CAVs on controlled edges only.

        Three zones:
          - _MAINLINE_CONTROLLED_EDGES → mainline_limit_ms
          - _RAMP_CONTROLLED_EDGES    → ramp_limit_ms
          - Everything else           → no slowDown (CAV drives at free-flow)

        This implements the "release point" design: CAVs that have passed
        the merge (seg_0_after, seg_1_after) or are on the merge curve
        (ramp_on_merge) are not restricted, allowing them to accelerate
        back to free-flow speed.
        """
        import traci

        duration = float(self.aggregation_time)
        for veh_id in traci.vehicle.getIDList():
            try:
                vtype = traci.vehicle.getTypeID(veh_id)
            except Exception:
                continue
            if "cav" not in vtype.lower():
                continue
            try:
                edge = traci.vehicle.getRoadID(veh_id)
            except Exception:
                continue
            if edge in _MAINLINE_CONTROLLED_EDGES:
                limit = mainline_limit_ms
            elif edge in _RAMP_CONTROLLED_EDGES:
                limit = ramp_limit_ms
            else:
                continue  # no slowDown — CAV drives at free-flow speed
            try:
                traci.vehicle.slowDown(veh_id, limit, duration)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Metrics collection
    # ------------------------------------------------------------------

    def _collect_metrics(self) -> None:
        """Read E1 detector aggregates from SUMO for all 12 segments."""
        import traci

        def _read(det_ids_list: List[str]) -> Tuple[float, float, float]:
            """Return (flow_vph, speed_ms, occ_pct)."""
            counts, speeds, occs = [], [], []
            for det in det_ids_list:
                try:
                    cnt = float(traci.inductionloop.getLastIntervalVehicleNumber(det))
                    spd = float(traci.inductionloop.getLastIntervalMeanSpeed(det))
                    occ = float(traci.inductionloop.getLastIntervalOccupancy(det))
                    counts.append(cnt)
                    speeds.append(max(0.0, spd))
                    occs.append(occ)
                except Exception:
                    pass

            flow_vph = float(sum(counts)) * (3600.0 / self.aggregation_time)
            total_cnt = sum(counts)
            if total_cnt > 1e-6:
                speed_ms = float(sum(c * s for c, s in zip(counts, speeds)) / total_cnt)
            else:
                speed_ms = float(np.mean(speeds)) if speeds else 0.0
            occ_pct = float(np.mean(occs)) if occs else 0.0
            return flow_vph, speed_ms, occ_pct

        m = self._metrics

        # Read all segments
        for seg, n_lanes in _SEGMENT_LANES.items():
            flow, speed, occ = _read(_det_ids(seg, n_lanes))
            setattr(m, f"{seg}_speed_ms", speed)
            setattr(m, f"{seg}_flow_vph", flow)
            setattr(m, f"{seg}_occ_pct", occ)

        # Upstream demand (sum of mainline upstream flows)
        m.upstream_demand_vph = (
            m.seg_3_before_flow_vph
            + m.seg_2_before_flow_vph
            + m.seg_1_before_flow_vph
            + m.seg_0_before_flow_vph
        )

        # TTS increment
        try:
            n_veh = float(traci.vehicle.getIDCount())
        except Exception:
            n_veh = 0.0
        m.tts_increment_s = n_veh * self.aggregation_time
