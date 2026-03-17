"""Builder for standard DQN algorithm with smoother updates."""
from typing import TYPE_CHECKING
import logging

import torch as th
from stable_baselines3 import DQN
from core import TemporalPrioritizedReplayBuffer

from . import register

if TYPE_CHECKING:
    from stable_baselines3.common.vec_env import VecEnv
    from train_eval.drl_vsl_train import Config

logger = logging.getLogger(__name__)


@register("DQN_v1")
def build_dqn_v1(train_env: "VecEnv", config: "Config"):
    """Instantiate DQN with larger buffer, soft targets, and safer exploration."""

    defaults = dict(
        learning_rate=5e-5,
        buffer_size=150_000,
        learning_starts=2_500,
        batch_size=128,
        tau=0.02,  # soft target updates
        gamma=0.99,
        train_freq=(3, "step"),
        gradient_steps=3,
        target_update_interval=600,
        exploration_fraction=0.2,
        exploration_initial_eps=0.1,
        exploration_final_eps=0.02,
        max_grad_norm=1.0,
        verbose=1,
        device="auto",
    )

    yaml_params = config.get("sar.parameters", {}) or {}

    lr = yaml_params.pop("learning_rate", defaults["learning_rate"])
    defaults["learning_rate"] = lr

    # Policy kwargs merging
    default_policy = dict(
        net_arch=[256, 256],
        activation_fn=th.nn.ReLU,
    )
    yaml_policy = yaml_params.pop("policy_kwargs", {}) or {}
    merged_policy = {**default_policy, **yaml_policy}
    replay_buffer_kwargs = yaml_params.pop("replay_buffer_kwargs", {}) or {}

    act_fn = merged_policy.get("activation_fn")
    if isinstance(act_fn, str):
        name = act_fn.strip()
        if hasattr(th.nn, name):
            merged_policy["activation_fn"] = getattr(th.nn, name)
        elif hasattr(th.nn, name.upper()):
            merged_policy["activation_fn"] = getattr(th.nn, name.upper())
        else:
            logger.warning("Unknown activation_fn '%s'; defaulting to ReLU.", name)
            merged_policy["activation_fn"] = th.nn.ReLU

    final_params = {**defaults, **yaml_params}
    if replay_buffer_kwargs:
        final_params["replay_buffer_class"] = TemporalPrioritizedReplayBuffer
        final_params["replay_buffer_kwargs"] = replay_buffer_kwargs

    return DQN(
        policy="MlpPolicy",
        env=train_env,
        policy_kwargs=merged_policy,
        seed=config.get("advanced.seed", None),
        **final_params,
    )
