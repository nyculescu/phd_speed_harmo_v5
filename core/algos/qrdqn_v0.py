"""Builder for QRDQN v3 (anti-collapse defaults + optional CVaR action selection)."""
from typing import TYPE_CHECKING
import logging
import os

import torch as th
from sb3_contrib import QRDQN

from . import register

if TYPE_CHECKING:  # pragma: no cover - typing only
    from stable_baselines3.common.vec_env import VecEnv
    from train_eval.drl_vsl_train import Config

from .qrdqn_policy_cvar_v0 import CvarQRDQNPolicy

logger = logging.getLogger(__name__)


@register("QRDQN_v3")
def build_qrdqn_v3(train_env: "VecEnv", config: "Config"):
    """Instantiate QR-DQN with stronger anti-collapse defaults for lane-drop control."""

    defaults = dict(
        learning_rate=6e-5,
        buffer_size=150_000,
        learning_starts=5_000,
        batch_size=256,
        tau=0.01,
        gamma=0.99,
        train_freq=(2, "step"),
        gradient_steps=2,
        target_update_interval=700,
        exploration_fraction=0.40,
        exploration_initial_eps=1.0,
        exploration_final_eps=0.08,
        max_grad_norm=1.0,
        verbose=1,
        device="auto",
    )

    yaml_params = config.get("sar.parameters", {}) or {}

    default_policy = dict(
        net_arch=[256, 256],
        activation_fn=th.nn.ReLU,
        n_quantiles=128,
    )
    yaml_policy = yaml_params.pop("policy_kwargs", {}) or {}
    merged_policy = {**default_policy, **yaml_policy}

    final_params = defaults.copy()
    final_params.update(yaml_params)

    anti_cfg = config.get("sar.anti_collapse") or {}
    min_final_eps = float(anti_cfg.get("min_exploration_final_eps", 0.08))
    min_fraction = float(anti_cfg.get("min_exploration_fraction", 0.25))

    try:
        eps_final = float(final_params.get("exploration_final_eps", defaults["exploration_final_eps"]))
    except (TypeError, ValueError):
        eps_final = defaults["exploration_final_eps"]
    try:
        eps_init = float(final_params.get("exploration_initial_eps", defaults["exploration_initial_eps"]))
    except (TypeError, ValueError):
        eps_init = defaults["exploration_initial_eps"]
    try:
        eps_frac = float(final_params.get("exploration_fraction", defaults["exploration_fraction"]))
    except (TypeError, ValueError):
        eps_frac = defaults["exploration_fraction"]

    eps_final = max(min_final_eps, eps_final)
    eps_frac = max(min_fraction, eps_frac)
    eps_init = max(eps_init, eps_final)

    final_params["exploration_final_eps"] = eps_final
    final_params["exploration_initial_eps"] = eps_init
    final_params["exploration_fraction"] = eps_frac

    risk_cfg = config.get("sar.risk") or {}
    risk_mode = (risk_cfg.get("mode") or "").lower() if risk_cfg else ""
    risk_alpha_raw = risk_cfg.get("alpha", 0.05) if risk_cfg else 0.05
    risk_enabled = bool(risk_cfg.get("enabled", False)) if risk_cfg else False
    runtime_env = str(risk_cfg.get("runtime_override_env") or "").strip() if risk_cfg else ""
    env_override = os.getenv(runtime_env) if runtime_env else None
    if env_override:
        risk_mode = env_override.strip().lower()
        risk_enabled = True
        logger.info("QRDQN_v3 risk mode overridden via env %s=%s", runtime_env, env_override)

    try:
        risk_alpha = float(risk_alpha_raw)
    except (TypeError, ValueError):
        logger.warning("Invalid QRDQN_v3 risk alpha %s; defaulting to 0.05", risk_alpha_raw)
        risk_alpha = 0.05
    risk_alpha = float(min(max(risk_alpha, 1e-6), 1.0))

    use_cvar = bool(risk_enabled and risk_mode == "cvar")
    if risk_enabled and risk_mode and risk_mode != "cvar":
        logger.warning("QRDQN_v3 risk mode '%s' is unsupported; disabling risk-aware action selection.", risk_mode)

    policy_cls = CvarQRDQNPolicy if use_cvar else "MlpPolicy"
    if use_cvar:
        merged_policy["risk_mode"] = "cvar"
        merged_policy["risk_alpha"] = risk_alpha

    logger.info(
        "QRDQN_v3 exploration clamp | initial=%.3f final=%.3f fraction=%.3f",
        float(final_params["exploration_initial_eps"]),
        float(final_params["exploration_final_eps"]),
        float(final_params["exploration_fraction"]),
    )

    return QRDQN(
        policy=policy_cls,
        env=train_env,
        policy_kwargs=merged_policy,
        seed=config.get("advanced.seed", 42),
        **final_params,
    )
