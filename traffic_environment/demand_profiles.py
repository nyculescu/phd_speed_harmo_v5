# traffic_environment/demand_profiles.py
"""
Piecewise Hermite spline demand profile generator.

Generates realistic, messy, multi-hour traffic demand curves by:
  1. Sampling N random control points (time, demand_vph) — the "red dots"
  2. Interpolating between them with cubic Hermite splines
  3. Adding heteroscedastic jitter + low-frequency wander noise
  4. Converting the continuous curve to integer vehicle counts per time bin

The result is a demand profile that looks like real loop-detector data:
irregular peaks, secondary surges, dips within plateaus, asymmetric
rise/fall — not a clean bell curve.

Adapted from v4's demand_profiles.py (Hermite basis + noise model).
Extended to support:
  - Multi-hour episodes (up to 24h = 1440 minutes)
  - Piecewise control points (4-12) instead of single up/down direction
  - Configurable demand floor and ceiling
  - Separate mainline and ramp count output

References:
  - Hermite interpolation: Burden & Faires, Numerical Analysis (2011)
  - Traffic demand patterns: Highway Capacity Manual 6th Ed., Ch. 11
  - v4 implementation: phd_speed_harmo_v4/traffic_environment/demand_profiles.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

__all__ = ["DemandProfile", "generate_demand_profile"]


@dataclass
class DemandProfile:
    """A complete demand profile for one episode."""

    duration_s: int
    """Episode duration in seconds."""

    bin_seconds: int
    """Aggregation bin width in seconds."""

    mainline_counts: np.ndarray
    """Integer vehicle counts per bin for mainline route."""

    ramp_counts: np.ndarray
    """Integer vehicle counts per bin for ramp route."""

    control_points_t: np.ndarray
    """Control point times (seconds) — the 'red dots' x-coordinates."""

    control_points_vph: np.ndarray
    """Control point demand levels (vph) — the 'red dots' y-coordinates."""

    ramp_fraction: float
    """Fraction of total demand routed to the ramp."""

    total_vehicles: int
    """Total vehicles across mainline + ramp."""

    peak_demand_vph: float
    """Maximum demand level in the profile (for metadata)."""

    seed: int
    """Random seed used to generate this profile."""

    noise_randomness: float
    """Noise intensity used (0=clean, 1=very noisy)."""

    weather: str = "clear"
    """Weather condition label."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Arbitrary metadata (weather params, anomaly info, etc.)."""

    @property
    def n_bins(self) -> int:
        return len(self.mainline_counts)

    @property
    def total_mainline(self) -> int:
        return int(self.mainline_counts.sum())

    @property
    def total_ramp(self) -> int:
        return int(self.ramp_counts.sum())


# ── Hermite basis functions ─────────────────────────────────────────────────

def _hermite_interpolate(
    t: np.ndarray,
    t0: float, t1: float,
    p0: float, p1: float,
    m0: float, m1: float,
) -> np.ndarray:
    """Cubic Hermite interpolation between two control points.

    Args:
        t: Array of times to evaluate (must be in [t0, t1]).
        t0, t1: Start and end times of the segment.
        p0, p1: Demand values at t0 and t1.
        m0, m1: Tangent (slope) values at t0 and t1.

    Returns:
        Interpolated demand values at each t.
    """
    dt = max(t1 - t0, 1e-9)
    s = (t - t0) / dt  # normalised to [0, 1]
    s = np.clip(s, 0.0, 1.0)

    # Hermite basis functions
    h00 = 2 * s**3 - 3 * s**2 + 1
    h10 = s**3 - 2 * s**2 + s
    h01 = -2 * s**3 + 3 * s**2
    h11 = s**3 - s**2

    return h00 * p0 + h10 * (m0 * dt) + h01 * p1 + h11 * (m1 * dt)


# ── Control point generation ────────────────────────────────────────────────

def _generate_control_points(
    duration_s: int,
    rng: np.random.Generator,
    n_points_range: Tuple[int, int] = (5, 10),
    demand_floor_vph: float = 2500.0,
    demand_ceil_vph: float = 8500.0,
    peak_demand_range: Tuple[float, float] = (5500.0, 8000.0),
    base_demand_range: Tuple[float, float] = (2500.0, 4000.0),
    boundary_demand_range: Tuple[float, float] = (2500.0, 3500.0),
    steepness_range: Tuple[float, float] = (0.5, 4.0),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate random control points for a demand profile.

    Returns:
        (times_s, demands_vph, slopes_vph_per_s) — arrays of length N.
    """
    n_points = int(rng.integers(n_points_range[0], n_points_range[1] + 1))

    # Always pin start and end at low demand
    start_demand = float(rng.uniform(*boundary_demand_range))
    end_demand = float(rng.uniform(*boundary_demand_range))

    # Interior points: random times (sorted), random demands
    if n_points > 2:
        # Generate interior times, avoiding too-close points
        interior_fracs = np.sort(rng.uniform(0.08, 0.92, size=n_points - 2))
        # Ensure minimum spacing of 5% of duration
        for i in range(1, len(interior_fracs)):
            if interior_fracs[i] - interior_fracs[i - 1] < 0.05:
                interior_fracs[i] = interior_fracs[i - 1] + 0.05
        interior_fracs = np.clip(interior_fracs, 0.05, 0.95)
        interior_times = interior_fracs * duration_s
    else:
        interior_times = np.array([])

    times = np.concatenate([[0.0], interior_times, [float(duration_s)]])

    # Generate interior demands — mix of base and peak levels
    demands = np.zeros(len(times))
    demands[0] = start_demand
    demands[-1] = end_demand

    # Decide which interior points are "peak" vs "base"
    n_interior = len(times) - 2
    if n_interior > 0:
        n_peaks = max(1, int(rng.integers(1, max(2, n_interior))))
        peak_indices = rng.choice(n_interior, size=min(n_peaks, n_interior), replace=False)

        for i in range(n_interior):
            idx = i + 1  # skip start point
            if i in peak_indices:
                demands[idx] = float(rng.uniform(*peak_demand_range))
            else:
                demands[idx] = float(rng.uniform(*base_demand_range))

    # Clip all demands to floor/ceiling
    demands = np.clip(demands, demand_floor_vph, demand_ceil_vph)

    # Generate slopes at each control point (tangent values)
    slopes = np.zeros(len(times))
    for i in range(len(times)):
        base_slope = 0.0
        if 0 < i < len(times) - 1:
            # Finite difference estimate as base, then randomise
            dt_prev = times[i] - times[i - 1]
            dt_next = times[i + 1] - times[i]
            if dt_prev > 0 and dt_next > 0:
                slope_left = (demands[i] - demands[i - 1]) / dt_prev
                slope_right = (demands[i + 1] - demands[i]) / dt_next
                base_slope = (slope_left + slope_right) / 2.0

        # Randomise the slope magnitude
        steepness_mult = float(rng.uniform(*steepness_range))
        slopes[i] = base_slope * steepness_mult

    # Boundary slopes: gentle approach/departure
    slopes[0] = float(rng.uniform(0.0, 1.0))
    slopes[-1] = float(rng.uniform(-1.0, 0.0))

    return times, demands, slopes


# ── Noise model (from v4) ───────────────────────────────────────────────────

def _apply_noise(
    y: np.ndarray,
    noise_randomness: float,
    rng: np.random.Generator,
    jitter_intensity: float = 0.06,
    wander_intensity: float = 0.025,
    hetero_offset: float = 0.15,
) -> np.ndarray:
    """Add heteroscedastic jitter + low-frequency wander noise.

    From v4's demand_profiles._apply_noise():
      - White noise scaled by signal level (louder at peaks)
      - Detrended random walk for slow oscillations
    """
    if y.size == 0 or noise_randomness <= 0.0:
        return np.clip(y, 0.0, None)

    jitter = jitter_intensity * noise_randomness
    wander = wander_intensity * noise_randomness

    # Heteroscedastic white noise (louder where demand is higher)
    y_max = max(float(np.max(y)), 1.0)
    y_norm = y / y_max
    white = rng.normal(0.0, jitter, size=y.size)
    hetero = white * (y_norm + hetero_offset) * y_max

    # Low-frequency wander (detrended random walk)
    walk = np.cumsum(rng.normal(0.0, wander * y_max * 0.01, size=y.size))
    if y.size > 1:
        trend_coeffs = np.polyfit(np.arange(y.size), walk, 1)
        walk = walk - np.poly1d(trend_coeffs)(np.arange(y.size))

    return np.clip(y + hetero + walk, 0.0, None)


# ── Largest remainder (from v4) ─────────────────────────────────────────────

def _largest_remainder(weights: np.ndarray, total: int) -> np.ndarray:
    """Distribute `total` items proportionally to `weights` (exact sum).

    Uses the largest-remainder method: floor each proportional share,
    then distribute the remaining items to bins with the largest
    fractional parts. Guarantees sum(result) == total.
    """
    weights = weights.astype(float)
    wsum = float(np.sum(weights))
    if wsum <= 0.0:
        return np.zeros_like(weights, dtype=int)

    scaled = weights * (float(total) / wsum)
    base = np.floor(scaled).astype(int)
    remainder = int(total - base.sum())

    if remainder > 0:
        frac = scaled - base
        idx = np.argsort(-frac)[:remainder]
        base[idx] += 1

    return base


# ── Main API ────────────────────────────────────────────────────────────────

def generate_demand_profile(
    duration_s: int = 3600,
    bin_seconds: int = 30,
    seed: int = 42,
    ramp_fraction_range: Tuple[float, float] = (0.20, 0.30),
    n_points_range: Tuple[int, int] = (5, 10),
    demand_floor_vph: float = 2500.0,
    demand_ceil_vph: float = 8500.0,
    peak_demand_range: Tuple[float, float] = (5500.0, 8000.0),
    base_demand_range: Tuple[float, float] = (2500.0, 4000.0),
    boundary_demand_range: Tuple[float, float] = (2500.0, 3500.0),
    steepness_range: Tuple[float, float] = (0.5, 4.0),
    noise_randomness: float = 0.5,
    weather: str = "clear",
    weather_params: Optional[Dict[str, float]] = None,
) -> DemandProfile:
    """Generate a complete demand profile with piecewise Hermite interpolation.

    The profile consists of N random control points connected by cubic
    Hermite splines, producing realistic messy demand curves with:
      - Irregular peaks and secondary surges
      - Dips within plateaus
      - Asymmetric rise/fall patterns
      - Heteroscedastic noise (louder at peaks)

    Args:
        duration_s: Episode duration in seconds (up to 86400 for 24h).
        bin_seconds: Aggregation bin width for vehicle counts.
        seed: Random seed for reproducibility.
        ramp_fraction_range: (min, max) fraction of total demand on ramp.
        n_points_range: (min, max) number of control points.
        demand_floor_vph: Minimum demand level (vph).
        demand_ceil_vph: Maximum demand level (vph).
        peak_demand_range: (min, max) demand for "peak" control points.
        base_demand_range: (min, max) demand for "base" control points.
        boundary_demand_range: (min, max) demand at episode start/end.
        steepness_range: (min, max) multiplier for control point slopes.
        noise_randomness: Noise intensity in [0, 1]. 0=clean, 1=very noisy.
        weather: Weather condition label (for metadata).
        weather_params: Optional weather parameters dict.

    Returns:
        DemandProfile with mainline_counts and ramp_counts arrays.
    """
    rng = np.random.default_rng(seed)

    # ── Step 1: Generate control points ──────────────────────────────────
    cp_times, cp_demands, cp_slopes = _generate_control_points(
        duration_s=duration_s,
        rng=rng,
        n_points_range=n_points_range,
        demand_floor_vph=demand_floor_vph,
        demand_ceil_vph=demand_ceil_vph,
        peak_demand_range=peak_demand_range,
        base_demand_range=base_demand_range,
        boundary_demand_range=boundary_demand_range,
        steepness_range=steepness_range,
    )

    # ── Step 2: Interpolate with piecewise Hermite splines ───────────────
    # Sample at 1 Hz resolution, then aggregate to bins
    t_1hz = np.arange(0, duration_s, dtype=float)
    y_1hz = np.zeros_like(t_1hz)

    for seg_idx in range(len(cp_times) - 1):
        t0, t1 = float(cp_times[seg_idx]), float(cp_times[seg_idx + 1])
        p0, p1 = float(cp_demands[seg_idx]), float(cp_demands[seg_idx + 1])
        m0, m1 = float(cp_slopes[seg_idx]), float(cp_slopes[seg_idx + 1])

        mask = (t_1hz >= t0) & (t_1hz < t1)
        if seg_idx == len(cp_times) - 2:
            mask = (t_1hz >= t0) & (t_1hz <= t1)

        if mask.any():
            y_1hz[mask] = _hermite_interpolate(
                t_1hz[mask], t0, t1, p0, p1, m0, m1,
            )

    # Clip to floor/ceiling
    y_1hz = np.clip(y_1hz, demand_floor_vph * 0.5, demand_ceil_vph * 1.2)

    # ── Step 3: Add noise ────────────────────────────────────────────────
    y_noisy = _apply_noise(y_1hz, noise_randomness, rng)

    # Final clip
    y_noisy = np.clip(y_noisy, 0.0, demand_ceil_vph * 1.3)

    # ── Step 4: Convert to vehicle counts per bin ────────────────────────
    n_bins = max(1, duration_s // bin_seconds)

    # Aggregate 1Hz demand rate into bin weights
    bin_weights = np.zeros(n_bins)
    for i, rate_vph in enumerate(y_noisy):
        bin_idx = min(i // bin_seconds, n_bins - 1)
        # rate_vph is vehicles/hour; each second contributes rate_vph/3600
        bin_weights[bin_idx] += rate_vph / 3600.0

    # Total vehicles = integral of rate curve
    total_vehicles = max(1, int(round(float(np.sum(bin_weights)))))

    # Split mainline / ramp
    ramp_fraction = float(rng.uniform(*ramp_fraction_range))
    total_ramp = max(0, int(round(total_vehicles * ramp_fraction)))
    total_mainline = total_vehicles - total_ramp

    # Distribute into bins using largest remainder
    mainline_counts = _largest_remainder(bin_weights, total_mainline)
    ramp_counts = _largest_remainder(bin_weights, total_ramp)

    return DemandProfile(
        duration_s=duration_s,
        bin_seconds=bin_seconds,
        mainline_counts=mainline_counts,
        ramp_counts=ramp_counts,
        control_points_t=cp_times,
        control_points_vph=cp_demands,
        ramp_fraction=ramp_fraction,
        total_vehicles=total_vehicles,
        peak_demand_vph=float(np.max(cp_demands)),
        seed=seed,
        noise_randomness=noise_randomness,
        weather=weather,
        metadata={
            "weather_params": weather_params or {},
            "n_control_points": len(cp_times),
            "n_bins": n_bins,
            "steepness_range": steepness_range,
        },
    )
