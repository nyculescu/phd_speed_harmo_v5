"""Builder for RBC51DQN v3 (anti-collapse defaults + risk-aware distributional control)."""
from typing import TYPE_CHECKING
import logging
import math
import os

from core import (
    DDDQN_NL_PER_Policy,
    DDDQN_NL_PER_TEMP,
    TemporalPrioritizedReplayBuffer,
)

from . import register

if TYPE_CHECKING:  # pragma: no cover - typing only
    from stable_baselines3.common.vec_env import VecEnv
    from train_eval.drl_vsl_train import Config

logger = logging.getLogger(__name__)


@register("RBC51DQN_v3")
def build_rbc51dqn_v3(train_env: "VecEnv", config: "Config"):
    """Instantiate Rainbow-C51 controller with anti-collapse exploration floor."""
    seed = config.get("advanced.seed", None)
    dist_bounds = (config.get("sar_runtime.distributional_bounds") or {}).copy()
    dist_cfg = config.get("sar.distributional_support") or {}
    use_static_bounds = bool(dist_cfg.get("use_static_bounds", False))

    def _valid_bounds(raw_min, raw_max):
        try:
            b_min = float(raw_min)
            b_max = float(raw_max)
        except (TypeError, ValueError):
            return None
        if b_min >= b_max:
            return None
        return b_min, b_max

    support_meta = None
    bounds_source = "sar_runtime"

    support_span_limit = float(dist_cfg.get("support_span_limit") or 400.0)
    support_padding_frac = float(dist_cfg.get("support_padding_frac") or 0.05)
    atoms_override = dist_cfg.get("atoms")

    chosen_bounds = None
    if use_static_bounds:
        static_bounds = _valid_bounds(dist_cfg.get("static_v_min"), dist_cfg.get("static_v_max"))
        if static_bounds:
            bounds_source = "config_static"
            chosen_bounds = static_bounds
            support_meta = {
                "v_min": chosen_bounds[0],
                "v_max": chosen_bounds[1],
                "source": bounds_source,
                "reward": config.get("sar.reward"),
            }
        else:
            logger.warning(
                "Static distributional bounds requested but invalid (v_min=%s, v_max=%s); falling back to SAR-derived values.",
                dist_cfg.get("static_v_min"),
                dist_cfg.get("static_v_max"),
            )

    if chosen_bounds is None:
        runtime_bounds = _valid_bounds(dist_bounds.get("v_min"), dist_bounds.get("v_max"))
        if runtime_bounds:
            chosen_bounds = runtime_bounds
            bounds_source = dist_bounds.get("source", "sar_config")
            support_meta = dict(dist_bounds)
            support_meta["v_min"] = chosen_bounds[0]
            support_meta["v_max"] = chosen_bounds[1]
            support_meta.setdefault("source", bounds_source)
            support_meta.setdefault("reward", config.get("sar.reward"))

    if chosen_bounds is None:
        v_min, v_max = -250.0, 150.0
        bounds_source = "fallback_default"
        logger.warning(
            "Distributional bounds missing or invalid; falling back to [%.1f, %.1f].",
            v_min,
            v_max,
        )
        support_meta = {
            "v_min": v_min,
            "v_max": v_max,
            "source": bounds_source,
            "reward": config.get("sar.reward"),
        }
    else:
        v_min, v_max = chosen_bounds
        span = v_max - v_min
        if not math.isfinite(span) or span <= 0:
            v_min, v_max = -200.0, 200.0
            bounds_source = f"{bounds_source}+reset"
        elif span > support_span_limit:
            center = (v_max + v_min) / 2.0
            half_span = support_span_limit / 2.0
            v_min, v_max = center - half_span, center + half_span
            bounds_source = f"{bounds_source}+clamped"
        pad = (v_max - v_min) * support_padding_frac
        v_min -= pad
        v_max += pad

    if support_meta is None:
        support_meta = {"source": bounds_source, "reward": config.get("sar.reward")}
    support_meta.update({"v_min": v_min, "v_max": v_max, "source": bounds_source})

    risk_cfg = config.get("sar.risk") or {}
    risk_mode = risk_cfg.get("mode")
    risk_alpha = risk_cfg.get("alpha", 0.05)
    risk_enabled = bool(risk_cfg.get("enabled", False))
    runtime_env = str(risk_cfg.get("runtime_override_env") or "").strip()
    env_override = os.getenv(runtime_env) if runtime_env else None
    if env_override:
        risk_mode = env_override
        risk_enabled = True
        logger.info("RBC51DQN_v3 risk mode overridden via env %s=%s", runtime_env, env_override)

    try:
        risk_alpha = float(risk_alpha)
    except (TypeError, ValueError):
        logger.warning("Invalid risk alpha %s; defaulting to 0.05", risk_alpha)
        risk_alpha = 0.05
    risk_alpha = min(max(risk_alpha, 1e-6), 1.0)

    if isinstance(risk_mode, str):
        risk_mode = risk_mode.strip().lower() or None
    if not risk_enabled or risk_mode not in {"var", "cvar"}:
        if risk_mode not in {None, ""} and risk_enabled:
            logger.warning("Unsupported risk mode '%s'; disabling risk-aware actions.", risk_mode)
        risk_mode = None

    config.data.setdefault("sar_runtime", {})["distributional_bounds_resolved"] = {
        "v_min": v_min,
        "v_max": v_max,
        "source": bounds_source,
        "risk_mode": risk_mode or "disabled",
        "risk_alpha": risk_alpha,
    }
    logger.info(
        "RBC51DQN_v3 support | source=%s v_min=%.2f v_max=%.2f risk_mode=%s alpha=%.3f",
        bounds_source,
        v_min,
        v_max,
        risk_mode or "disabled",
        risk_alpha,
    )

    defaults = dict(
        learning_rate=4.5e-5,
        buffer_size=180_000,
        learning_starts=5_000,
        batch_size=256,
        gamma=0.99,
        train_freq=(2, "step"),
        gradient_steps=2,
        tau=0.012,
        target_update_interval=700,
        exploration_fraction=0.45,
        exploration_initial_eps=1.0,
        exploration_final_eps=0.08,
        max_grad_norm=1.0,
        aggregation_time=int(config.get("sumo.aggregation_time", 150) or 150),
        target_update_windows=10,
        use_noisynet_exploration=True,
        verbose=1,
        device="auto",
    )

    yaml_params = config.get("sar.parameters", {}) or {}
    replay_buffer_kwargs = yaml_params.pop("replay_buffer_kwargs", {}) or {}
    policy_kwargs = yaml_params.pop("policy_kwargs", {}) or {}

    anti_cfg = config.get("sar.anti_collapse") or {}
    min_final_eps = float(anti_cfg.get("min_exploration_final_eps", 0.08))
    min_fraction = float(anti_cfg.get("min_exploration_fraction", 0.25))

    policy_defaults = dict(
        noisy=True,
        dist=True,
        atoms=int(atoms_override or 101),
        net_arch=(256, 256),
        track_support_edges=True,
    )
    merged_policy = {**policy_defaults, **policy_kwargs}
    merged_policy.update(
        {
            "atoms": int(merged_policy.get("atoms", atoms_override or 101)),
            "v_min": float(v_min),
            "v_max": float(v_max),
            "risk_mode": risk_mode,
            "risk_alpha": risk_alpha,
            "support_telemetry": support_meta,
        }
    )

    rb_defaults = dict(
        alpha=0.6,
        beta_start=0.4,
        beta_frames=600_000,
        eps=1e-6,
        temporal_priority_boost=1.1,
    )
    merged_rb = {**rb_defaults, **replay_buffer_kwargs}

    final_params = defaults.copy()
    final_params.update(yaml_params)

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

    final_params["dist"] = bool(merged_policy.get("dist", True))
    final_params["atoms"] = int(merged_policy.get("atoms", atoms_override or 101))
    final_params["v_min"] = float(v_min)
    final_params["v_max"] = float(v_max)

    logger.info(
        "RBC51DQN_v3 exploration clamp | initial=%.3f final=%.3f fraction=%.3f",
        float(final_params["exploration_initial_eps"]),
        float(final_params["exploration_final_eps"]),
        float(final_params["exploration_fraction"]),
    )

    return DDDQN_NL_PER_TEMP(
        policy=DDDQN_NL_PER_Policy,
        env=train_env,
        policy_kwargs=merged_policy,
        replay_buffer_class=TemporalPrioritizedReplayBuffer,
        replay_buffer_kwargs=merged_rb,
        seed=seed,
        **final_params,
    )
