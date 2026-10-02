# core/env_interact.py
"""
Gymnasium environment wrapping a SUMO ramps_v2 simulation.

Design
------
- One env step = one E1 aggregation window (``aggregation_time`` seconds).
- Speed limits are posted to controlled segments (mainline + ramp transition).
- CAVs receive ``traci.vehicle.slowDown()`` at every SUMO step.
- ``sumo_cfg_path=None`` → dry-run mode: no SUMO process, all metrics zero.
"""
from __future__ import annotations

import logging
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import gymnasium as gym
import numpy as np

from .constants import MAX_SPEED_KPH
from .env_metrics import TrafficMetrics
from .sar_frame import ActionStrategy, RewardFunction, StateRepresentation

logger = logging.getLogger(__name__)
_SEED_MOD = 2 ** 32

# ---------------------------------------------------------------------------
# ramps_v2 topology constants
# ---------------------------------------------------------------------------

# All segments with their lane counts.
_SEGMENT_LANES: Dict[str, int] = {
    "seg_3_before": 3,
    "seg_2_before": 3,
    "seg_1_before": 3,
    "seg_0_before": 3,
    "seg_0_after": 4,  # 3 through + 1 acceleration lane (L0)
    "seg_1_after": 3,
    "ramp_on_approach": 1,
    "ramp_on_transition": 1,
    "ramp_on_merge": 1,
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


def _free_port(min_port: int = 20000, max_port: int = 60000) -> int:
    """Pick a random port from a wide range and verify it's bindable.

    Using OS-assigned sequential ports (bind to port 0) causes collisions
    when 100+ workers start simultaneously — the OS gives nearby ports
    that collide with SUMO processes still binding.  Random selection
    from a 40k range effectively eliminates this.
    Adapted from phd_speed_harmo_v4 which runs 700 workers reliably.
    """
    import random
    for _ in range(200):
        port = random.randint(min_port, max_port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("Could not find a free port after 200 random attempts")


def _seed_u32(seed: int, offset: int = 0) -> int:
    """Fold any integer seed into NumPy RandomState's valid [0, 2**32-1] range."""
    return int((int(seed) + int(offset)) % _SEED_MOD)


# ---------------------------------------------------------------------------
# TrafficEnv
# ---------------------------------------------------------------------------

class TrafficEnv(gym.Env):
    """
    Gymnasium environment for the ramps_v2 SUMO network.

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
        *,
        demand_config: Optional[Dict[str, Any]] = None,
        anomaly_config: Optional[Dict[str, Any]] = None,
        env_seed: Optional[int] = 0,
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

        # Stochastic demand: regenerate routes every reset()
        self._demand_config = demand_config  # None → use fixed sumo_cfg_path
        self._anomaly_config = anomaly_config
        # env_seed=None → truly random scenarios (fresh entropy each reset).
        # env_seed=int → deterministic chain: env_seed → episode_count → ep_seed.
        self._env_seed: Optional[int] = (
            _seed_u32(env_seed) if env_seed is not None else None
        )
        self._episode_count: int = 0
        self._tmp_dir: Optional[Path] = None
        self._scenario_manager = None  # set via set_scenario_manager()

        self._sumo_proc: Optional[subprocess.Popen] = None
        self._port: int = 0
        self._traci_label: str = ""
        self._traci_conn = None  # traci.Connection — unique per instance
        self._step_count: int = 0
        self._sumo_seed: int = 0  # set each reset; threaded into `sumo --seed`
        self._metrics: TrafficMetrics = TrafficMetrics()
        self._anomaly_injector = None
        # Optional per-SUMO-step evaluation hook. evaluate_models.py attaches an
        # EvalMetricsCollector here for accel/jerk logging; stays None during
        # training, so the hook in _advance_sumo is a no-op there.
        self._eval_collector = None

    # ------------------------------------------------------------------
    # gymnasium interface
    # ------------------------------------------------------------------

    def set_scenario_manager(self, manager) -> None:
        """Attach a ScenarioManager for pre-generated scenario cycling."""
        self._scenario_manager = manager

    def _compute_ep_seed(self) -> int:
        """Return a 31-bit episode seed used by demand/route/anomaly generators
        and by `sumo --seed`.

        - env_seed is None  → fresh entropy each call (truly random scenarios).
        - env_seed is int   → deterministic: env_seed * 100_000 + episode_count.
        """
        if self._env_seed is None:
            return int.from_bytes(os.urandom(4), "big") & 0x7FFFFFFF
        return _seed_u32(self._env_seed * 100_000, self._episode_count) & 0x7FFFFFFF

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
        self.reward_func.reset()
        self._anomaly_injector = None

        # Compute episode seed ONCE here, thread it everywhere: route file
        # generation, anomaly injector, AND `sumo --seed`. This ties SUMO's
        # internal RNG to the same deterministic chain as Python-side RNG.
        ep_seed = self._compute_ep_seed()
        self._sumo_seed = ep_seed

        if not self.dry_run:
            if self._scenario_manager is not None:
                # Use pre-generated scenario from pool
                self.sumo_cfg_path = self._scenario_manager.get_next_scenario()
                # Anomaly injector for this episode
                acfg = self._anomaly_config or {}
                if acfg.get("enabled", False):
                    from traffic_environment.anomaly_injector import AnomalyInjector
                    self._anomaly_injector = AnomalyInjector(
                        anomaly_prob=acfg.get("probability", 0.15),
                        seed=_seed_u32(ep_seed, 50_000),
                    )
            elif self._demand_config is not None:
                # Fallback: generate on-the-fly
                self._regenerate_routes(ep_seed=ep_seed)
            self._start_sumo()
            self._advance_sumo(self._steps_per_window)
            self._collect_metrics()

        self._episode_count += 1
        obs = self._make_obs()
        return obs, {}

    def _regenerate_routes(self, ep_seed: int) -> None:
        """Create a fresh stochastic demand profile + routes for this episode.

        ep_seed is computed by reset() and threaded in (also used as SUMO --seed)
        so the entire stochastic chain — demand profile, fleet, anomalies, and
        SUMO's internal RNG — derives from one number.
        """
        from traffic_environment.stochastic_demand import generate_demand_profile
        from traffic_environment.anomaly_injector import AnomalyInjector

        dcfg = self._demand_config
        profile = generate_demand_profile(
            episode_duration_s=self.episode_duration,
            peak_demand_range=tuple(dcfg["peak_demand_range"]),
            base_fraction_range=tuple(dcfg["base_fraction_range"]),
            ramp_fraction_range=tuple(dcfg["ramp_fraction_range"]),
            t_peak_frac_range=tuple(dcfg["t_peak_range"]),
            t_decay_frac_range=tuple(dcfg["t_decay_range"]),
            noise_std=dcfg["noise_std"],
            seed=ep_seed,
        )

        # Anomaly injector (new each episode)
        acfg = self._anomaly_config or {}
        if acfg.get("enabled", False):
            self._anomaly_injector = AnomalyInjector(
                anomaly_prob=acfg.get("probability", 0.15),
                seed=_seed_u32(ep_seed, 50_000),
            )
        else:
            self._anomaly_injector = None

        # Write routes to temp dir (reuse dir across episodes)
        if self._tmp_dir is None:
            import tempfile
            self._tmp_dir = Path(tempfile.mkdtemp(
                prefix=f"train_env{self._env_seed}_"
            ))

        rou_path = self._tmp_dir / "scenario.rou.xml"
        cfg_path = self._tmp_dir / "scenario.sumocfg"

        from tests._sumo_helpers import (
            generate_stochastic_route_file, generate_sumocfg,
        )
        generate_stochastic_route_file(
            rou_path, profile,
            cav_pct=self.cav_percent * 100.0,
            seed=_seed_u32(ep_seed, 10_000),
        )
        generate_sumocfg(cfg_path, rou_path, self.episode_duration)

        # Point SUMO at the fresh config
        self.sumo_cfg_path = str(cfg_path)

        logger.debug(
            "Episode %d: peak=%.0f vph, ramp_frac=%.2f, anomaly=%s (seed=%d)",
            self._episode_count, profile.peak_demand_vph,
            profile.ramp_fraction,
            self._anomaly_injector.event.anomaly_type if (
                self._anomaly_injector and self._anomaly_injector.has_anomaly
            ) else "none",
            ep_seed,
        )

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

        # Store raw speed_limits dict for _advance_sumo to use directly
        self._current_speed_limits_ms = speed_limits_ms

        # Also update metrics.current_speed_limits for backward compat
        # (state repr and reward may read it)
        for i, seg in enumerate(_CONTROLLED_SEGS):
            limit_ms = speed_limits_ms.get(seg, MAX_SPEED_KPH / 3.6)
            if i < len(self._metrics.current_speed_limits):
                self._metrics.current_speed_limits[i] = limit_ms * 3.6  # kph

        # 3. Advance simulation
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
        if self._tmp_dir is not None:
            import shutil
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
            self._tmp_dir = None

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

    def _start_sumo(self, max_attempts: int = 5, backoff: float = 1.0) -> None:
        """Start SUMO with retry-on-new-port (adapted from v4's robust launch).

        On failure, picks a fresh random port and retries with linear backoff.
        This handles the rare case where the port was free at bind() time but
        taken by another worker's SUMO process before our SUMO could bind it.
        """
        import traci

        if not self.sumo_cfg_path:
            raise RuntimeError(
                "sumo_cfg_path is None — either pass a .sumocfg or set "
                "demand_config so routes are generated on reset()"
            )

        last_exc: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                delay = backoff * (attempt - 1)
                logger.warning(
                    "SUMO launch retry %d/%d (port=%d failed) — waiting %.1fs, new port",
                    attempt, max_attempts, self._port, delay,
                )
                self._close_sumo()
                time.sleep(delay)

            self._port = _free_port()
            self._traci_label = f"env_{os.getpid()}_{self._port}"

            try:
                cmd = [
                    "sumo",
                    "-c", str(self.sumo_cfg_path),
                    "--remote-port", str(self._port),
                    "--seed", str(self._sumo_seed),
                    "--step-method.ballistic",
                    "--collision.action", "warn",
                    "--time-to-teleport", "-1",
                    "--no-step-log",
                    "--no-warnings",
                    "--start",
                ]
                self._sumo_proc = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                # Give SUMO time to bind the port
                time.sleep(0.75)

                # Check if SUMO died immediately
                if self._sumo_proc.poll() is not None:
                    raise RuntimeError(
                        f"SUMO exited immediately (code={self._sumo_proc.returncode})"
                    )

                traci.init(port=self._port, numRetries=5, label=self._traci_label)
                self._traci_conn = traci.getConnection(self._traci_label)
                logger.debug(
                    "SUMO started on port %d label=%s (attempt %d)",
                    self._port, self._traci_label, attempt,
                )
                return  # success
            except Exception as exc:
                last_exc = exc
                logger.warning("SUMO attempt %d failed: %s", attempt, exc)

        raise RuntimeError(
            f"SUMO failed to start after {max_attempts} attempts: {last_exc}"
        ) from last_exc

    def _close_sumo(self) -> None:
        if self.dry_run:
            return
        if self._traci_conn is not None:
            try:
                self._traci_conn.close()
            except Exception:
                pass
            self._traci_conn = None
        if self._sumo_proc is not None:
            try:
                self._sumo_proc.terminate()
                self._sumo_proc.wait(timeout=5)
            except Exception:
                try:
                    self._sumo_proc.kill()
                except Exception:
                    pass
            self._sumo_proc = None

    def _recover_sumo(self) -> None:
        """Kill the dead SUMO and restart it mid-episode.

        This is a last-resort recovery — the episode continues with
        zeroed metrics for the current step.  The alternative (crashing
        the SubprocVecEnv worker) kills the entire training run.
        """
        logger.warning("Recovering SUMO (pid=%s port=%s)",
                       getattr(self._sumo_proc, 'pid', '?'), self._port)
        self._close_sumo()
        try:
            self._start_sumo()
            # Fast-forward to roughly the right simulation time.
            # Not exact, but prevents the reward from seeing a fresh-start
            # state that doesn't match the episode progression.
            warmup = min(self._step_count * self._steps_per_window, 300)
            if warmup > 0 and self._traci_conn is not None:
                for _ in range(warmup):
                    self._traci_conn.simulationStep()
            logger.info("SUMO recovered after %d warmup steps", warmup)
        except Exception as e:
            logger.error("SUMO recovery failed: %s — env will return zeros", e)
            self._traci_conn = None

    def _advance_sumo(self, n_steps: int) -> None:
        conn = self._traci_conn
        if conn is None:
            return

        sl = getattr(self, "_current_speed_limits_ms", {})

        # Per-lane limits for seg_0_before
        seg0_per_lane_ms = [
            sl.get("seg_0_before_L0", MAX_SPEED_KPH / 3.6),
            sl.get("seg_0_before_L1", MAX_SPEED_KPH / 3.6),
            sl.get("seg_0_before_L2", MAX_SPEED_KPH / 3.6),
        ]
        ramp_limit_ms = sl.get("ramp_on_transition", MAX_SPEED_KPH / 3.6)

        # Per-lane limits for seg_1_before (Box(7)) or uniform
        has_seg1_per_lane = "seg_1_before_L0" in sl
        if has_seg1_per_lane:
            seg1_per_lane_ms = [
                sl.get("seg_1_before_L0", MAX_SPEED_KPH / 3.6),
                sl.get("seg_1_before_L1", MAX_SPEED_KPH / 3.6),
                sl.get("seg_1_before_L2", MAX_SPEED_KPH / 3.6),
            ]
            upstream_limit_ms = min(seg1_per_lane_ms)
        else:
            seg1_per_lane_ms = None
            upstream_limit_ms = sl.get("seg_1_before", min(seg0_per_lane_ms))

        # Box(5) physical VSL on seg_1_before (edge-wide speed limit for HDVs)
        if "seg_1_before_physical" in sl:
            try:
                conn.edge.setMaxSpeed("seg_1_before", sl["seg_1_before_physical"])
            except Exception:
                pass

        seg2_limit_ms = sl.get("seg_2_before", upstream_limit_ms)

        # Apply CAV slowDown every _SLOWDOWN_INTERVAL steps (not every step).
        # The slowDown() duration covers the full aggregation window, so
        # vehicles already commanded will maintain their target speed.
        # New vehicles entering the network between intervals get commanded
        # on the next interval.  At 5-step intervals, max delay = 5s — acceptable
        # given the 30s control window.
        _SLOWDOWN_INTERVAL = 5
        sim_time_base = self._step_count * self.aggregation_time
        for i in range(n_steps):
            try:
                conn.simulationStep()
            except Exception as e:
                logger.warning("SUMO connection lost during step: %s — restarting", e)
                self._recover_sumo()
                conn = self._traci_conn
                if conn is None:
                    return
                continue

            # Safety-by-construction evidence per ADR-010. SUMO is launched with
            # --collision.action warn (see _start_sumo), which logs collisions
            # without removing the colliding vehicles. Poll the count directly
            # so we can persist it in evaluation_summary.csv as positive evidence
            # of the safety claim. Expected value across all episodes: 0.
            try:
                n_collided = conn.simulation.getCollidingVehiclesNumber()
                if n_collided > 0:
                    self._metrics.episode_collision_count += int(n_collided)
            except Exception:
                pass  # Don't let a TraCI hiccup kill the episode.

            # Per-SUMO-step acceleration / jerk instrumentation. Active only
            # when evaluate_models.py has attached an EvalMetricsCollector;
            # _eval_collector is None during training, so this is a no-op there.
            if self._eval_collector is not None:
                try:
                    self._eval_collector.sumo_step(conn, float(sim_time_base + i + 1))
                except Exception:
                    pass

            # Anomaly injection (if active this episode)
            if self._anomaly_injector is not None:
                sim_t = sim_time_base + i
                self._anomaly_injector.step(float(sim_t), conn)
                self._metrics.anomaly_active = self._anomaly_injector.is_active
                if self._anomaly_injector.has_anomaly:
                    self._metrics.anomaly_type = self._anomaly_injector.event.anomaly_type

            if self.cav_percent > 0.0 and i % _SLOWDOWN_INTERVAL == 0:
                self._apply_cav_slowdown(
                    seg0_per_lane_ms, ramp_limit_ms, upstream_limit_ms,
                    seg1_per_lane_ms=seg1_per_lane_ms,
                    seg2_limit_ms=seg2_limit_ms,
                )

    # ------------------------------------------------------------------
    # Speed control
    # ------------------------------------------------------------------

    def _apply_cav_slowdown(
        self,
        seg0_per_lane_ms: list,
        ramp_limit_ms: float,
        upstream_limit_ms: float,
        seg1_per_lane_ms: list = None,
        seg2_limit_ms: float = None,
    ) -> None:
        """Issue slowDown() to CAVs on controlled edges.

        Per-lane control on seg_0_before (always) and seg_1_before (Box(7)).
        Uniform on seg_2_before. Implements "release point" design.
        """
        conn = self._traci_conn
        duration = float(self.aggregation_time)
        _seg2_ms = seg2_limit_ms if seg2_limit_ms is not None else upstream_limit_ms

        for veh_id in conn.vehicle.getIDList():
            try:
                vtype = conn.vehicle.getTypeID(veh_id)
            except Exception:
                continue
            if "cav" not in vtype.lower():
                continue
            try:
                edge = conn.vehicle.getRoadID(veh_id)
            except Exception:
                continue

            if edge == "seg_0_before":
                # Per-lane differential control
                try:
                    lane_idx = conn.vehicle.getLaneIndex(veh_id)
                    limit = seg0_per_lane_ms[lane_idx] if lane_idx < len(seg0_per_lane_ms) else seg0_per_lane_ms[0]
                except Exception:
                    limit = seg0_per_lane_ms[0]
            elif edge == "seg_1_before":
                if seg1_per_lane_ms is not None:
                    # Box(7): per-lane on seg_1_before too
                    try:
                        lane_idx = conn.vehicle.getLaneIndex(veh_id)
                        limit = seg1_per_lane_ms[lane_idx] if lane_idx < len(seg1_per_lane_ms) else seg1_per_lane_ms[0]
                    except Exception:
                        limit = seg1_per_lane_ms[0]
                else:
                    limit = upstream_limit_ms
            elif edge == "seg_2_before":
                limit = _seg2_ms
            elif edge in _RAMP_CONTROLLED_EDGES:
                limit = ramp_limit_ms
            else:
                continue  # release point — CAV drives at free-flow
            try:
                conn.vehicle.slowDown(veh_id, limit, duration)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Metrics collection
    # ------------------------------------------------------------------

    def _collect_metrics(self) -> None:
        """Read E1 detector aggregates from SUMO for all 12 segments."""
        conn = self._traci_conn
        if conn is None:
            return  # Dead connection — metrics stay at zero

        def _read(det_ids_list: List[str]) -> Tuple[float, float, float]:
            """Return (flow_vph, speed_ms, occ_pct)."""
            counts, speeds, occs = [], [], []
            for det in det_ids_list:
                try:
                    cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det))
                    spd = float(conn.inductionloop.getLastIntervalMeanSpeed(det))
                    occ = float(conn.inductionloop.getLastIntervalOccupancy(det))
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

        # Per-lane metrics at seg_0_before (merge approach)
        for lane_idx in range(3):
            det_id = f"flow_loop_seg_0_before_{lane_idx}_{_DET_POS}"
            try:
                cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det_id))
                spd = max(0.0, float(conn.inductionloop.getLastIntervalMeanSpeed(det_id)))
                occ = float(conn.inductionloop.getLastIntervalOccupancy(det_id))
            except Exception:
                cnt, spd, occ = 0.0, 0.0, 0.0
            flow = cnt * (3600.0 / self.aggregation_time)
            setattr(m, f"seg_0_before_L{lane_idx}_speed_ms", spd)
            setattr(m, f"seg_0_before_L{lane_idx}_flow_vph", flow)
            setattr(m, f"seg_0_before_L{lane_idx}_occ_pct", occ)

        # TTS increment
        try:
            n_veh = float(conn.vehicle.getIDCount())
        except Exception:
            n_veh = 0.0
        m.tts_increment_s = n_veh * self.aggregation_time
