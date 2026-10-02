"""CPU package temperature (coretemp 'Package id 0') and load helpers."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _package_input() -> Path | None:
    for h in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            if (h / "name").read_text().strip() != "coretemp":
                continue
        except OSError:
            continue
        for lab in h.glob("temp*_label"):
            try:
                if lab.read_text().strip() == "Package id 0":
                    return lab.with_name(lab.name.replace("_label", "_input"))
            except OSError:
                continue
    return None


def package_temp_c() -> float:
    p = _package_input()
    if p is None:
        return float("nan")
    try:
        return int(p.read_text().strip()) / 1000.0
    except (OSError, ValueError):
        return float("nan")


def load_fraction() -> float:
    """1-min load average as a fraction of logical CPUs."""
    return os.getloadavg()[0] / max(os.cpu_count() or 1, 1)
