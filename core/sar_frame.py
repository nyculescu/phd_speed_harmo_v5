# core/sar_frame.py
"""
SAR framework — abstract base classes and factory functions.

StateRepresentation, ActionStrategy, RewardFunction define the plugin interface.
Factory functions create instances by name via the sar_components registry.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np

from .constants import MAX_SPEED_KPH

logger = logging.getLogger(__name__)

DEFAULT_SPEED_LIMIT: float = MAX_SPEED_KPH  # kph

# ---------------------------------------------------------------------------
# Registry initialisation (lazy, done once)
# ---------------------------------------------------------------------------

_REGISTRY_LOADED: bool = False


def _load_registry() -> None:
    global _REGISTRY_LOADED
    if _REGISTRY_LOADED:
        return
    try:
        from sar_components.discovery import discover_components
        discover_components()
    except ImportError:
        logger.warning("sar_components not found; only built-in SAR components available.")
    _REGISTRY_LOADED = True


# ---------------------------------------------------------------------------
# RewardSignal
# ---------------------------------------------------------------------------

@dataclass
class RewardSignal:
    """Return type for RewardFunction.calculate()."""
    total: float
    components: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract base classes
# ---------------------------------------------------------------------------

class StateRepresentation(ABC):
    """Plugin interface for observation construction."""

    def __init__(self, config: Dict[str, Any], enable_safety_metrics: bool = False) -> None:
        self.config = config
        self.enable_safety_metrics = enable_safety_metrics
        self._setup()

    def _setup(self) -> None:
        """Override to initialise subclass-specific state."""

    def reset(self, **kwargs: Any) -> None:
        """Called at the start of each episode; clear buffers here."""

    @abstractmethod
    def get_observation_space(self) -> gym.spaces.Space:
        ...

    @abstractmethod
    def build_state(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        ...

    @abstractmethod
    def preprocess_state(self, raw_state: np.ndarray) -> np.ndarray:
        ...

    def get_observation(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        return self.preprocess_state(self.build_state(metrics, safety_metrics, context))


class ActionStrategy(ABC):
    """Plugin interface for action application."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.invalid_action_penalty: float = 0.0
        self._setup()

    def _setup(self) -> None:
        """Override to initialise subclass-specific state."""

    def reset(self) -> None:
        """Called at the start of each episode."""

    @abstractmethod
    def get_action_space(self) -> gym.spaces.Space:
        ...

    @abstractmethod
    def apply_action(
        self,
        action: Any,
        metrics: Any,
    ) -> Tuple[Dict[str, float], float, Optional[str]]:
        """Return (speed_limits_ms, penalty, pattern_name)."""
        ...


class RewardFunction(ABC):
    """Plugin interface for reward calculation."""

    def __init__(self, config: Dict[str, Any], enable_safety_metrics: bool = False) -> None:
        self.config = config
        self.enable_safety_metrics = enable_safety_metrics
        self._setup()

    def _setup(self) -> None:
        """Override to initialise subclass-specific state."""

    @abstractmethod
    def calculate(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        ...

    def reset_metrics(self) -> None:
        """Optional reset hook called at episode start."""


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def create_state_representation(
    name: str,
    config: Dict[str, Any],
    enable_safety_metrics: bool = False,
) -> StateRepresentation:
    _load_registry()
    try:
        from sar_components.registry import get_state
        cls = get_state(name)
        return cls(config, enable_safety_metrics)
    except (ImportError, KeyError) as exc:
        raise ValueError(f"Unknown state representation: {name!r}") from exc


def create_action_strategy(
    name: str,
    config: Dict[str, Any],
) -> ActionStrategy:
    _load_registry()
    try:
        from sar_components.registry import get_action
        cls = get_action(name)
        return cls(config)
    except (ImportError, KeyError) as exc:
        raise ValueError(f"Unknown action strategy: {name!r}") from exc


def create_reward_function(
    name: str,
    config: Dict[str, Any],
    enable_safety_metrics: bool = False,
) -> RewardFunction:
    _load_registry()
    try:
        from sar_components.registry import get_reward
        cls = get_reward(name)
        return cls(config, enable_safety_metrics)
    except (ImportError, KeyError) as exc:
        raise ValueError(f"Unknown reward function: {name!r}") from exc
