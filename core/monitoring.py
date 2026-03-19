# core/monitoring.py
"""
SB3 training callbacks for speed harmonization monitoring.

Logs per-episode diagnostic metrics to TensorBoard so that early
convergence problems (Risk 2) can be detected without post-hoc analysis.

Usage with SB3:
    from core.monitoring import HarmonizationMonitor
    model.learn(total_timesteps=..., callback=HarmonizationMonitor())
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


# ---------------------------------------------------------------------------
# Observation feature names (must match r44_state_v1.py layout)
# ---------------------------------------------------------------------------
# 56-dim = 3 frames × 18 per-frame features + 2 prev_action features.

_FRAME_FEATURE_NAMES = [
    "seg_2_before_speed", "seg_2_before_flow", "seg_2_before_occ",
    "seg_1_before_speed", "seg_1_before_flow", "seg_1_before_occ",
    "seg_0_before_speed", "seg_0_before_flow", "seg_0_before_occ",
    "seg_0_after_speed",  "seg_0_after_flow",  "seg_0_after_occ",
    "ramp_approach_flow", "ramp_merge_speed",  "seg_1_after_flow",
    "regime_FF",          "regime_META",        "regime_CONG",
]

_FRAME_SIZE = len(_FRAME_FEATURE_NAMES)  # 18
_N_FRAMES = 3
_STATIC_NAMES = ["prev_action_mainline", "prev_action_ramp"]


def _obs_feature_name(idx: int) -> str:
    """Map observation dimension index (0-55) to a human-readable name."""
    frame_total = _FRAME_SIZE * _N_FRAMES  # 54
    if idx < frame_total:
        frame_idx = idx // _FRAME_SIZE
        feat_idx = idx % _FRAME_SIZE
        return f"f{frame_idx}/{_FRAME_FEATURE_NAMES[feat_idx]}"
    static_idx = idx - frame_total
    if static_idx < len(_STATIC_NAMES):
        return _STATIC_NAMES[static_idx]
    return f"obs[{idx}]"


class HarmonizationMonitor(BaseCallback):
    """
    Per-episode monitoring callback for the speed harmonization environment.

    Tracks and logs to TensorBoard:
      - Reward components (spatial, temporal, throughput, smoothness, total)
      - Action statistics per regime (FREE_FLOW, METASTABLE, CONGESTED)
      - SAC/TQC temperature (alpha) if available
      - Regime distribution per episode
      - Convergence diagnostics (action drift, reward trend)
      - Dead feature detection (obs dimensions with near-zero variance)

    Optionally writes a per-episode CSV for offline analysis.

    Dead feature detection
    ----------------------
    At each episode end, compute per-dimension std across all observations
    collected during that episode.  Any dimension with std < 0.01 is flagged
    as "dead" — it carries no information for the critic/actor networks and
    wastes capacity in the first Linear layer.

    This catches two failure modes:
      1. A normalization ceiling is too high (e.g., max_flow=8000 but actual
         flow never exceeds 2000 → feature stuck near 0.25).  Not dead, but
         compressed — std will be low.
      2. A feature is truly constant (e.g., ramp flow = 0 for the entire
         episode because no ramp vehicles spawned) → std = 0.

    Logged to TensorBoard as obs/dead_feature_count and obs/dead_features
    (comma-separated names).  See r44_state_v1.py for the feature layout.

    Parameters
    ----------
    csv_path : str or Path, optional
        If provided, write a per-episode CSV with all metrics.
    verbose : int
        0 = silent, 1 = episode summary, 2 = per-step detail.
    dead_feature_threshold : float
        Std threshold below which a feature is flagged as dead (default 0.01).
    """

    def __init__(
        self,
        csv_path: Optional[str] = None,
        verbose: int = 0,
        dead_feature_threshold: float = 0.01,
    ):
        super().__init__(verbose)
        self._csv_path = Path(csv_path) if csv_path else None
        self._dead_threshold = float(dead_feature_threshold)

        # Per-episode accumulators (reset each episode)
        self._ep_rewards: List[float] = []
        self._ep_components: Dict[str, List[float]] = defaultdict(list)
        self._ep_actions: List[np.ndarray] = []
        self._ep_regimes: List[int] = []  # 0=FF, 1=META, 2=CONG
        self._ep_observations: List[np.ndarray] = []

        # Cross-episode tracking
        self._episode_count = 0
        self._csv_writer = None
        self._csv_file = None

    def _on_training_start(self) -> None:
        if self._csv_path:
            self._csv_path.parent.mkdir(parents=True, exist_ok=True)
            self._csv_file = open(self._csv_path, "w", newline="")
            self._csv_writer = csv.writer(self._csv_file)
            self._csv_writer.writerow([
                "episode", "n_steps", "total_reward", "mean_reward",
                "mean_spatial", "mean_temporal", "mean_throughput",
                "mean_smoothness", "mean_harmonization",
                "mean_action_mainline", "mean_action_ramp",
                "std_action_mainline", "std_action_ramp",
                "ff_frac", "meta_frac", "cong_frac",
                "mean_action_mainline_ff", "mean_action_mainline_cong",
                "alpha",
            ])

    def _on_step(self) -> bool:
        # SB3 calls _on_step after every env.step().
        # For VecEnv with n_envs=1, infos is a list of length 1.
        infos = self.locals.get("infos", [])
        actions = self.locals.get("actions")
        rewards = self.locals.get("rewards")

        for i, info in enumerate(infos):
            reward = float(rewards[i]) if rewards is not None else 0.0
            self._ep_rewards.append(reward)

            # Reward components
            components = info.get("reward_components", {})
            for key in ("spatial", "temporal", "throughput",
                        "smoothness", "harmonization"):
                self._ep_components[key].append(components.get(key, 0.0))

            # Action
            if actions is not None:
                act = np.asarray(actions[i], dtype=np.float32).flatten()
                self._ep_actions.append(act)

            # Regime: infer from the observation.
            # In r44_state_v1, the regime one-hot is at indices [15, 16, 17]
            # of the MOST RECENT frame (the last 18 features before the
            # 2 prev_action features, i.e., obs[36:54] is frame 2).
            # frame2 regime indices: 36 + 15 = 51, 52, 53
            if obs is not None:
                ob = np.asarray(obs[i]).flatten()
                if len(ob) >= 54:
                    regime_vec = ob[51:54]  # [FF, META, CONG]
                    regime_idx = int(np.argmax(regime_vec))
                    self._ep_regimes.append(regime_idx)

            # Collect observation for dead-feature analysis
            obs = self.locals.get("new_obs")
            if obs is not None:
                self._ep_observations.append(
                    np.asarray(obs[i], dtype=np.float32).flatten().copy()
                )

            # Check for episode done
            done = self.locals.get("dones", [False])[i]
            if done:
                self._flush_episode()

        return True

    def _flush_episode(self) -> None:
        """Compute and log episode-level metrics."""
        if not self._ep_rewards:
            self._reset_episode()
            return

        self._episode_count += 1
        n = len(self._ep_rewards)

        # --- Reward statistics ---
        total_reward = sum(self._ep_rewards)
        mean_reward = total_reward / n

        comp_means = {}
        for key in ("spatial", "temporal", "throughput",
                     "smoothness", "harmonization"):
            vals = self._ep_components.get(key, [])
            comp_means[key] = np.mean(vals) if vals else 0.0

        # --- Action statistics ---
        if self._ep_actions:
            actions_arr = np.array(self._ep_actions)
            mean_mainline = float(np.mean(actions_arr[:, 0]))
            mean_ramp = float(np.mean(actions_arr[:, 1]))
            std_mainline = float(np.std(actions_arr[:, 0]))
            std_ramp = float(np.std(actions_arr[:, 1]))
        else:
            mean_mainline = mean_ramp = std_mainline = std_ramp = 0.0

        # --- Regime fractions ---
        ff_frac = meta_frac = cong_frac = 0.0
        if self._ep_regimes:
            r_arr = np.array(self._ep_regimes)
            n_r = len(r_arr)
            ff_frac = float(np.sum(r_arr == 0)) / n_r
            meta_frac = float(np.sum(r_arr == 1)) / n_r
            cong_frac = float(np.sum(r_arr == 2)) / n_r

        # --- Per-regime action means ---
        mean_act_ff = mean_act_cong = 0.0
        if self._ep_actions and self._ep_regimes:
            actions_arr = np.array(self._ep_actions)
            r_arr = np.array(self._ep_regimes[:len(actions_arr)])
            ff_mask = r_arr == 0
            cong_mask = r_arr == 2
            if ff_mask.any():
                mean_act_ff = float(np.mean(actions_arr[ff_mask, 0]))
            if cong_mask.any():
                mean_act_cong = float(np.mean(actions_arr[cong_mask, 0]))

        # --- SAC/TQC alpha (entropy temperature) ---
        # Alpha controls the exploration-exploitation balance in SAC/TQC.
        # The policy objective is: J = E[Σ γ^t (r_t + α * H(π))],
        # where H(π) is the policy entropy.
        #
        # With our reward in [-1, 0] per step:
        #   α ≈ 0.01–0.1  → healthy: entropy is meaningful relative to reward
        #   α > 0.5       → TOO HIGH: agent ignores reward and explores randomly.
        #                    Likely cause: reward is too flat or critic hasn't
        #                    converged.  The agent will not learn useful behavior.
        #   α < 0.001     → TOO LOW: policy is near-deterministic.  Risk of
        #                    premature convergence to a suboptimal action (e.g.,
        #                    always posting 90 kph regardless of traffic state).
        #
        # SB3's ent_coef="auto" auto-tunes α via a learned log_ent_coef
        # parameter targeting target_entropy = -dim(A) = -2.
        alpha = 0.0
        if hasattr(self.model, "log_ent_coef"):
            alpha = float(self.model.ent_coef)

        # --- Dead feature detection ---
        # Compute per-dimension std across the episode's observations.
        # Any dim with std < threshold is "dead": it carries no gradient
        # signal through the first Linear layer and wastes network capacity.
        dead_names: List[str] = []
        obs_std = np.zeros(0)
        if self._ep_observations:
            obs_arr = np.array(self._ep_observations)  # (n_steps, 56)
            obs_std = np.std(obs_arr, axis=0)           # (56,)
            dead_mask = obs_std < self._dead_threshold
            if dead_mask.any():
                dead_indices = np.where(dead_mask)[0]
                dead_names = [
                    _obs_feature_name(int(idx)) for idx in dead_indices
                ]

        # --- Log to TensorBoard ---
        ep = self._episode_count
        self.logger.record("episode/total_reward", total_reward)
        self.logger.record("episode/mean_reward", mean_reward)
        self.logger.record("episode/n_steps", n)

        self.logger.record("reward/spatial", comp_means["spatial"])
        self.logger.record("reward/temporal", comp_means["temporal"])
        self.logger.record("reward/throughput", comp_means["throughput"])
        self.logger.record("reward/smoothness", comp_means["smoothness"])
        self.logger.record("reward/harmonization", comp_means["harmonization"])

        self.logger.record("action/mean_mainline_kph", mean_mainline)
        self.logger.record("action/mean_ramp_kph", mean_ramp)
        self.logger.record("action/std_mainline_kph", std_mainline)
        self.logger.record("action/std_ramp_kph", std_ramp)

        self.logger.record("regime/free_flow_frac", ff_frac)
        self.logger.record("regime/metastable_frac", meta_frac)
        self.logger.record("regime/congested_frac", cong_frac)

        self.logger.record("action/mainline_at_free_flow", mean_act_ff)
        self.logger.record("action/mainline_at_congested", mean_act_cong)

        self.logger.record("train/alpha", alpha)

        self.logger.record("obs/dead_feature_count", len(dead_names))
        if dead_names:
            self.logger.record(
                "obs/dead_features", ", ".join(dead_names)
            )

        # --- Console output ---
        if self.verbose >= 1:
            regime_str = f"FF={ff_frac:.0%} M={meta_frac:.0%} C={cong_frac:.0%}"
            # Alpha label: flag when outside the healthy 0.01–0.1 range.
            if alpha > 0.5:
                alpha_label = f"α={alpha:.3f} HIGH!"
            elif alpha < 0.001 and alpha > 0:
                alpha_label = f"α={alpha:.4f} LOW!"
            else:
                alpha_label = f"α={alpha:.3f}"
            print(
                f"[Ep {ep:4d}] R={total_reward:+.3f} "
                f"main={mean_mainline:.0f}kph ramp={mean_ramp:.0f}kph "
                f"({regime_str}) "
                f"sp={comp_means['spatial']:+.3f} "
                f"tp={comp_means['temporal']:+.3f} "
                f"thr={comp_means['throughput']:+.3f} "
                f"{alpha_label}"
            )
            if dead_names:
                print(
                    f"  WARNING: {len(dead_names)} dead feature(s) "
                    f"(std < {self._dead_threshold}): "
                    + ", ".join(dead_names)
                )

        # --- CSV ---
        if self._csv_writer:
            self._csv_writer.writerow([
                ep, n, f"{total_reward:.4f}", f"{mean_reward:.4f}",
                f"{comp_means['spatial']:.4f}",
                f"{comp_means['temporal']:.4f}",
                f"{comp_means['throughput']:.4f}",
                f"{comp_means['smoothness']:.4f}",
                f"{comp_means['harmonization']:.4f}",
                f"{mean_mainline:.2f}", f"{mean_ramp:.2f}",
                f"{std_mainline:.2f}", f"{std_ramp:.2f}",
                f"{ff_frac:.4f}", f"{meta_frac:.4f}", f"{cong_frac:.4f}",
                f"{mean_act_ff:.2f}", f"{mean_act_cong:.2f}",
                f"{alpha:.6f}",
            ])
            self._csv_file.flush()

        self._reset_episode()

    def _reset_episode(self) -> None:
        self._ep_rewards.clear()
        self._ep_components.clear()
        self._ep_actions.clear()
        self._ep_regimes.clear()
        self._ep_observations.clear()

    def _on_training_end(self) -> None:
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None
