"""Central registries and decorators for SAR components."""

from __future__ import annotations

import logging
from typing import Callable, Dict, Type

logger = logging.getLogger(__name__)

STATE_REGISTRY: Dict[str, Type] = {}
ACTION_REGISTRY: Dict[str, Type] = {}
REWARD_REGISTRY: Dict[str, Type] = {}


def _register(registry: Dict[str, Type], kind: str, name: str, cls: Type) -> Type:
    existing = registry.get(name)
    if existing and existing is not cls:
        logger.warning("Replacing %s component '%s' (%s -> %s)", kind, name, existing, cls)
    registry[name] = cls
    return cls


def register_state(name: str) -> Callable[[Type], Type]:
    """Decorator to register a state representation by name."""

    def decorator(cls: Type) -> Type:
        return _register(STATE_REGISTRY, "state", name, cls)

    return decorator


def register_action(name: str) -> Callable[[Type], Type]:
    """Decorator to register an action strategy by name."""

    def decorator(cls: Type) -> Type:
        return _register(ACTION_REGISTRY, "action", name, cls)

    return decorator


def register_reward(name: str) -> Callable[[Type], Type]:
    """Decorator to register a reward function by name."""

    def decorator(cls: Type) -> Type:
        return _register(REWARD_REGISTRY, "reward", name, cls)

    return decorator


def get_state(name: str) -> Type:
    return STATE_REGISTRY[name]


def get_action(name: str) -> Type:
    return ACTION_REGISTRY[name]


def get_reward(name: str) -> Type:
    return REWARD_REGISTRY[name]


def list_states() -> Dict[str, Type]:
    return dict(STATE_REGISTRY)


def list_actions() -> Dict[str, Type]:
    return dict(ACTION_REGISTRY)


def list_rewards() -> Dict[str, Type]:
    return dict(REWARD_REGISTRY)

