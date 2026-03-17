# sar_components/__init__.py
"""SAR components with auto-discovery and registries."""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from .discovery import discover_components
from .registry import (
    ACTION_REGISTRY,
    REWARD_REGISTRY,
    STATE_REGISTRY,
    list_actions,
    list_rewards,
    list_states,
    register_action,
    register_reward,
    register_state,
)

__all__ = [
    "discover_components",
    "STATE_REGISTRY",
    "ACTION_REGISTRY",
    "REWARD_REGISTRY",
    "register_state",
    "register_action",
    "register_reward",
    "list_states",
    "list_actions",
    "list_rewards",
]
