# core/__init__.py
"""
v5 core — lightweight SUMO/RL interface.

Public API
----------
Constants:
    MAX_SPEED_KPH, DEFAULT_MIN_SPEED_KPH, DEFAULT_VSL_SPEED_STEP_KPH

Data:
    TrafficMetrics

SAR framework:
    StateRepresentation, ActionStrategy, RewardFunction, RewardSignal
    create_state_representation, create_action_strategy, create_reward_function
    DEFAULT_SPEED_LIMIT

Regime:
    RegimeDetector, RegimeThresholds, TrafficRegime, DEFAULT_THRESHOLDS

Environment:
    TrafficEnv
"""
from .constants import (
    DEFAULT_MIN_SPEED_KPH,
    DEFAULT_VSL_SPEED_STEP_KPH,
    MAX_ADJACENT_DIFF_KPH,
    MAX_SPEED_KPH,
)
from .env_metrics import TrafficMetrics
from .sar_frame import (
    ActionStrategy,
    DEFAULT_SPEED_LIMIT,
    RewardFunction,
    RewardSignal,
    StateRepresentation,
    create_action_strategy,
    create_reward_function,
    create_state_representation,
)
from .regime_detector import (
    DEFAULT_THRESHOLDS,
    RegimeDetector,
    RegimeThresholds,
    TrafficRegime,
)
from .env_interact import TrafficEnv

# Lazy import: monitoring requires stable-baselines3, which may not
# be installed in the base test environment.
try:
    from .monitoring import HarmonizationMonitor
except ImportError:
    HarmonizationMonitor = None  # type: ignore[assignment,misc]

__all__ = [
    # constants
    "MAX_SPEED_KPH",
    "DEFAULT_MIN_SPEED_KPH",
    "DEFAULT_VSL_SPEED_STEP_KPH",
    "MAX_ADJACENT_DIFF_KPH",
    # metrics
    "TrafficMetrics",
    # SAR framework
    "StateRepresentation",
    "ActionStrategy",
    "RewardFunction",
    "RewardSignal",
    "DEFAULT_SPEED_LIMIT",
    "create_state_representation",
    "create_action_strategy",
    "create_reward_function",
    # regime
    "RegimeDetector",
    "RegimeThresholds",
    "TrafficRegime",
    "DEFAULT_THRESHOLDS",
    # environment
    "TrafficEnv",
    # monitoring
    "HarmonizationMonitor",
]
