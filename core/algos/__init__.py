"""
Lightweight registry for algorithm-specific builders used during training.

Each algorithm module within this package should import ``register`` and
decorate a factory function that returns an instantiated Stable-Baselines3
model when provided with the training vectorised environment and configuration.
"""
from importlib import import_module
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple

from stable_baselines3.common.vec_env import VecEnv

AlgorithmBuilder = Callable[[VecEnv, "Config"], "BaseAlgorithm"]

REGISTRY: Dict[str, AlgorithmBuilder] = {}


def register(name: str) -> Callable[[AlgorithmBuilder], AlgorithmBuilder]:
    """Decorator used by algorithm modules to register their builders."""

    normalized = name.strip()

    def decorator(builder: AlgorithmBuilder) -> AlgorithmBuilder:
        REGISTRY[normalized] = builder
        return builder

    return decorator


def create_algorithm(name: str, train_env: VecEnv, config: "Config"):
    """Instantiate the requested algorithm using a registered builder."""
    try:
        builder = REGISTRY[name]
    except KeyError as exc:
        available = ", ".join(sorted(REGISTRY)) or "<none>"
        raise ValueError(
            f"Unknown algorithm '{name}'. Available algorithms: {available}"
        ) from exc
    return builder(train_env, config)


def available_algorithms() -> Tuple[str, ...]:
    """Return registered algorithm names."""
    return tuple(sorted(REGISTRY))


def _auto_import_modules():
    package_dir = Path(__file__).resolve().parent
    for module_path in package_dir.glob("*.py"):
        stem = module_path.stem
        if stem in {"__init__", "_base"} or stem.startswith("_"):
            continue
        import_module(f"{__name__}.{stem}")


# Discover algorithm modules on import.
_auto_import_modules()


# Avoid circular import typing issues
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from train_eval.drl_vsl_train import Config  # noqa: F401
    from stable_baselines3.common.base_class import BaseAlgorithm  # noqa: F401
