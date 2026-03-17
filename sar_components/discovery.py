"""Utilities for discovering SAR components dynamically."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from types import ModuleType
from typing import Iterable, List, Tuple

logger = logging.getLogger(__name__)

_DISCOVERED = False
_DISCOVERY_ERRORS: List[Tuple[str, str]] = []


def _iter_modules(package: ModuleType) -> Iterable[str]:
    prefix = package.__name__ + "."
    for module_info in pkgutil.iter_modules(package.__path__, prefix):
        name = module_info.name
        if module_info.ispkg:
            continue
        if name.rsplit('.', 1)[-1].startswith('_'):
            continue
        yield name


def discover_components(force: bool = False) -> None:
    """Import all SAR component modules so they can self-register."""

    global _DISCOVERED
    global _DISCOVERY_ERRORS

    if force:
        _DISCOVERED = False

    if _DISCOVERED:
        return

    _DISCOVERY_ERRORS = []

    packages: List[str] = [
        'sar_components.states',
        'sar_components.actions',
        'sar_components.rewards',
    ]

    for pkg_name in packages:
        try:
            package = importlib.import_module(pkg_name)
        except ImportError as exc:  # pragma: no cover - optional packages
            msg = f"{exc.__class__.__name__}: {exc}"
            logger.warning("Failed to import package '%s': %s", pkg_name, exc)
            _DISCOVERY_ERRORS.append((pkg_name, msg))
            continue

        for module_name in _iter_modules(package):
            try:
                importlib.import_module(module_name)
            except ImportError as exc:  # pragma: no cover - defensive logging
                msg = f"{exc.__class__.__name__}: {exc}"
                logger.error("Failed to import SAR component module '%s': %s", module_name, exc)
                _DISCOVERY_ERRORS.append((module_name, msg))

    _DISCOVERED = True


def get_discovery_errors() -> List[Tuple[str, str]]:
    """Return diagnostics collected during the most recent discovery pass."""
    return list(_DISCOVERY_ERRORS)
