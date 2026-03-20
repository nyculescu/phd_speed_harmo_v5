# traffic_environment/stochastic_demand.py
"""
Stochastic demand profile generator for v5.1 training.

Each episode samples a demand profile with three phases:
  Phase 1: Ramp-up    (0 → t_peak)     linear increase from base to peak
  Phase 2: Peak       (t_peak → t_decay) sustained high demand with noise
  Phase 3: Ramp-down  (t_decay → T)     linear decrease back to base

Parameters are sampled per episode from configurable distributions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass
class DemandProfile:
    """Per-second departure rates for mainline and ramp."""

    mainline_rates: np.ndarray  # shape (T,), veh/s
    ramp_rates: np.ndarray      # shape (T,), veh/s
    peak_demand_vph: float
    ramp_fraction: float
    t_peak_s: float
    t_decay_s: float
    seed: int


def generate_demand_profile(
    episode_duration_s: int = 3600,
    peak_demand_range: Tuple[float, float] = (5500.0, 8000.0),
    base_fraction_range: Tuple[float, float] = (0.4, 0.6),
    ramp_fraction_range: Tuple[float, float] = (0.20, 0.30),
    t_peak_frac_range: Tuple[float, float] = (0.15, 0.30),
    t_decay_frac_range: Tuple[float, float] = (0.65, 0.80),
    noise_std: float = 0.05,
    seed: Optional[int] = None,
) -> DemandProfile:
    """Sample a stochastic demand profile for one episode.

    Returns a DemandProfile with per-second mainline and ramp departure rates.
    """
    rng = np.random.default_rng(seed)

    # Sample episode parameters
    peak_vph = rng.uniform(*peak_demand_range)
    base_frac = rng.uniform(*base_fraction_range)
    ramp_frac = rng.uniform(*ramp_fraction_range)
    t_peak_frac = rng.uniform(*t_peak_frac_range)
    t_decay_frac = rng.uniform(*t_decay_frac_range)

    T = episode_duration_s
    t_peak = int(t_peak_frac * T)
    t_decay = int(t_decay_frac * T)

    base_vph = peak_vph * base_frac
    peak_vps = peak_vph / 3600.0
    base_vps = base_vph / 3600.0

    # Build per-second total demand rate
    total_rate = np.zeros(T, dtype=np.float64)

    # Phase 1: linear ramp-up
    if t_peak > 0:
        total_rate[:t_peak] = np.linspace(base_vps, peak_vps, t_peak)

    # Phase 2: sustained peak with noise
    peak_len = t_decay - t_peak
    if peak_len > 0:
        noise = rng.normal(0, noise_std * peak_vps, size=peak_len)
        total_rate[t_peak:t_decay] = peak_vps + noise

    # Phase 3: linear ramp-down
    tail_len = T - t_decay
    if tail_len > 0:
        total_rate[t_decay:] = np.linspace(peak_vps, base_vps, tail_len)

    # Clip to non-negative
    total_rate = np.clip(total_rate, 0.0, None)

    # Split into mainline and ramp
    ramp_rate = total_rate * ramp_frac
    mainline_rate = total_rate * (1.0 - ramp_frac)

    return DemandProfile(
        mainline_rates=mainline_rate.astype(np.float32),
        ramp_rates=ramp_rate.astype(np.float32),
        peak_demand_vph=peak_vph,
        ramp_fraction=ramp_frac,
        t_peak_s=float(t_peak),
        t_decay_s=float(t_decay),
        seed=seed if seed is not None else -1,
    )
