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
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class HarmonizationMonitor(BaseCallback):
    """
    Per-episode monitoring callback for the speed harmonization environment.

    Tracks and logs to TensorBoard:
      - Reward components (spatial, temporal, throughput, smoothness, total)
      - Action statistics per regime (FREE_FLOW, METASTABLE, CONGESTED)
      - SAC/TQC temperature (alpha) if available
      - Regime distribution per episode
      - Convergence diagnostics (action drift, reward trend)

    Optionally writes a per-episode CSV for offline analysis.

    Parameters
    ----------
    csv_path : str or Path, optional
        If provided, write a per-episode CSV with all metrics.
    verbose : int
        0 = silent, 1 = episode summary, 2 = per-step detail.
    """

    def __init__(self, csv_path: Optional[str] = None, verbose: int = 0):
        super().__init__(verbose)
        self._csv_path = Path(csv_path) if csv_path else None

        # Per-episode accumulators (reset each episode)
        self._ep_rewards: List[float] = []
        self._ep_components: Dict[str, List[float]] = defaultdict(list)
        self._ep_actions: List[np.ndarray] = []
        self._ep_regimes: List[int] = []  # 0=FF, 1=META, 2=CONG

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
            obs = self.locals.get("new_obs")
            if obs is not None:
                ob = np.asarray(obs[i]).flatten()
                if len(ob) >= 54:
                    regime_vec = ob[51:54]  # [FF, META, CONG]
                    regime_idx = int(np.argmax(regime_vec))
                    self._ep_regimes.append(regime_idx)

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
        alpha = 0.0
        if hasattr(self.model, "log_ent_coef"):
            alpha = float(self.model.ent_coef)

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

        # --- Console output ---
        if self.verbose >= 1:
            regime_str = f"FF={ff_frac:.0%} M={meta_frac:.0%} C={cong_frac:.0%}"
            print(
                f"[Ep {ep:4d}] R={total_reward:+.3f} "
                f"main={mean_mainline:.0f}kph ramp={mean_ramp:.0f}kph "
                f"({regime_str}) "
                f"sp={comp_means['spatial']:+.3f} "
                f"tp={comp_means['temporal']:+.3f} "
                f"thr={comp_means['throughput']:+.3f}"
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

    def _on_training_end(self) -> None:
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None
