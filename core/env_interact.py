# core/env_interact.py
"""
Design
------
- One env step = one E1 aggregation window (``aggregation_time`` seconds).
- Speed limits are posted to all lanes in the controlled upstream segments.
- CAVs receive ``traci.vehicle.slowDown()`` at every SUMO step.
- ``sumo_cfg_path=None`` → dry-run mode: no SUMO process, all metrics are
  zero.  Used for unit/integration tests without a SUMO installation.

"""
from __future__ import annotations

import logging
import socket
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np

from .constants import MAX_SPEED_KPH
from .env_metrics import TrafficMetrics
from .sar_frame import ActionStrategy, RewardFunction, StateRepresentation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Network topology constants for merge_4_to_3
# ---------------------------------------------------------------------------

# Upstream segments ordered from furthest-from-merge to closest.
# Each has 4 lanes (the 4-lane highway before the 4→3 merge point).
_UPSTREAM_SEGS: Tuple[str, ...] = ("seg_2_before", "seg_1_before", "seg_0_before")
_UPSTREAM_LANE_COUNT: int = 4

# Downstream segment (3 lanes after the merge).
_DOWNSTREAM_SEG: str = "seg_0_after"
_DOWNSTREAM_LANE_COUNT: int = 3

# E1 detector position within each segment to read from.
# "exit" = closest to merge inside the upstream segment (best predictive signal).
# "entry" = just after the merge for the downstream segment.
_US_DET_POS: str = "exit"
_DS_DET_POS: str = "entry"

# Segments that receive posted speed limits (same order as TrafficMetrics.current_speed_limits).
_CONTROLLED_SEGS: Tuple[str, ...] = ("seg_0_before", "seg_1_before", "seg_2_before")


def _us_det_ids(seg: str) -> List[str]:
    return [f"flow_loop_{seg}_{i}_{_US_DET_POS}" for i in range(_UPSTREAM_LANE_COUNT)]


def _ds_det_ids() -> List[str]:
    return [f"flow_loop_{_DOWNSTREAM_SEG}_{i}_{_DS_DET_POS}" for i in range(_DOWNSTREAM_LANE_COUNT)]


def _seg_lane_ids(seg: str, n: int) -> List[str]:
    return [f"{seg}_{i}" for i in range(n)]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# TrafficEnv
# ---------------------------------------------------------------------------

class TrafficEnv(gym.Env):
    """
    Gymnasium environment wrapping a SUMO merge_4_to_3_v0 simulation.

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

        # Each SUMO step is 1 s; one env step advances aggregation_time SUMO steps.
        self._steps_per_window: int = self.aggregation_time
        self._max_steps: int = self.episode_duration // self.aggregation_time

        # gymnasium spaces (delegated to SAR components)
        self.observation_space = self.state_repr.get_observation_space()
        self.action_space = self.action_strat.get_action_space()

        # Runtime
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
            self._advance_sumo(self._steps_per_window)  # first window
            self._collect_metrics()

        obs = self._make_obs()
        return obs, {}

    def step(
        self,
        action: int,
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action = int(action)

        # 1. Apply action → speed limits (m/s per segment)
        speed_limits_ms, penalty, pattern = self.action_strat.apply_action(
            action, self._metrics
        )

        # 2. Update control bookkeeping in metrics
        self._metrics.prev_action_idx = self._metrics.action_idx
        self._metrics.action_idx = action
        for i, seg in enumerate(_CONTROLLED_SEGS):
            limit_ms = speed_limits_ms.get(seg, MAX_SPEED_KPH / 3.6)
            self._metrics.current_speed_limits[i] = limit_ms * 3.6  # kph

        # 3. Advance simulation
        if not self.dry_run:
            self._apply_segment_limits(speed_limits_ms)
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
        import traci  # type: ignore[import]

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
            import traci  # type: ignore[import]
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
        import traci  # type: ignore[import]

        limit_ms = self._metrics.current_speed_limits[0] / 3.6  # seg_0_before
        for _ in range(n_steps):
            traci.simulationStep()
            if self.cav_percent > 0.0:
                self._apply_cav_slowdown(limit_ms)

    # ------------------------------------------------------------------
    # Speed control
    # ------------------------------------------------------------------

    def _apply_segment_limits(self, speed_limits_ms: Dict[str, float]) -> None:
        """Set lane maxspeed for all lanes in each controlled segment."""
        import traci  # type: ignore[import]

        for seg, limit_ms in speed_limits_ms.items():
            for lane in _seg_lane_ids(seg, _UPSTREAM_LANE_COUNT):
                try:
                    traci.lane.setMaxSpeed(lane, float(limit_ms))
                except Exception:
                    pass

    def _apply_cav_slowdown(self, limit_ms: float) -> None:
        """Issue slowDown() to all CAV vehicles."""
        import traci  # type: ignore[import]

        duration_ms = float(self.aggregation_time)  # TraCI 1.26+: seconds (not ms)
        for veh_id in traci.vehicle.getIDList():
            try:
                vtype = traci.vehicle.getTypeID(veh_id)
            except Exception:
                continue
            if "cav" in vtype.lower():
                try:
                    traci.vehicle.slowDown(veh_id, limit_ms, duration_ms)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Metrics collection
    # ------------------------------------------------------------------

    def _collect_metrics(self) -> None:
        """Read E1 detector aggregates from SUMO and populate self._metrics."""
        import traci  # type: ignore[import]

        def _read(det_ids: List[str]) -> Tuple[float, float, float]:
            """Return (flow_vph, speed_ms, occ_pct) aggregated across detector list."""
            counts, speeds, occs = [], [], []
            for det in det_ids:
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

        m.flow_rate_vph_us0, m.avg_speed_upstream_s0, m.occupancy_pct_us0 = _read(
            _us_det_ids(_UPSTREAM_SEGS[2])  # seg_0_before (closest to merge)
        )
        m.flow_rate_vph_us1, m.avg_speed_upstream_s1, m.occupancy_pct_us1 = _read(
            _us_det_ids(_UPSTREAM_SEGS[1])  # seg_1_before
        )
        m.flow_rate_vph_us2, m.avg_speed_upstream_s2, m.occupancy_pct_us2 = _read(
            _us_det_ids(_UPSTREAM_SEGS[0])  # seg_2_before (furthest from merge)
        )
        m.flow_rate_vph_ds0, m.avg_speed_downstream_s0, m.occupancy_pct_ds0 = _read(
            _ds_det_ids()
        )

        m.upstream_demand_vph = (
            m.flow_rate_vph_us0 + m.flow_rate_vph_us1 + m.flow_rate_vph_us2
        )

        # TTS increment: vehicles-in-network × step_duration (conservative proxy).
        try:
            n_veh = float(traci.vehicle.getIDCount())
        except Exception:
            n_veh = 0.0
        m.tts_increment_s = n_veh * self.aggregation_time
