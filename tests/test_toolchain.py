"""The project runs only on the pinned toolchain (CLAUDE.md, Toolchain): a version drift changes simulation results."""
import importlib.metadata as md
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PINS = {"libsumo": "1.27.1", "sumolib": "1.27.1", "stable_baselines3": "2.8.0", "gymnasium": "1.2.3"}


def test_package_imports():
    import v5b
    assert v5b.__version__


@pytest.mark.parametrize("dist,version", sorted(PINS.items()))
def test_pinned_version(dist, version):
    assert md.version(dist) == version
