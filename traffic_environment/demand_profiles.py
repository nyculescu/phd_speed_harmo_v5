"""Demand profile generation utilities (Hermite trend + stochastic noise)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np

__all__ = ["make_counts_from_profile"]

_DEFAULT_PROFILE: Dict[str, Any] = {
    "sampling_rate_hz": 1.0,
    "active_duration_s": None,
    "cooldown_duration_s": 0.0,
    "shape_randomness": 0.5,
    "noise_randomness": 0.0,
    "trend_direction": "down",
    "min_view_width": 0.05,
    "view_start": {"base": 0.1, "spread": 0.1},
    "view_end": {"base": 0.85, "spread": 0.1},
    "start_steepness": {"base": 15.0, "spread": 5.0},
    "end_steepness": {"base": 10.0, "spread": 5.0},
    "jitter_intensity": 0.08,
    "wander_intensity": 0.03,
    "hetero_offset": 0.2,
}


def _to_plain(value: Any) -> Any:
    if hasattr(value, "items"):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_to_plain(v) for v in value)
    return value


def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _resolve_profile_cfg(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = _to_plain(profile) if profile else {}
    merged = _deep_merge_dicts(_DEFAULT_PROFILE, cfg)
    return merged


def _resolve_param(cfg: Dict[str, Any], key: str, default_base: float, default_spread: float) -> Tuple[float, float]:
    entry = cfg.get(key, {})
    base = default_base
    spread = default_spread
    if isinstance(entry, dict):
        base = entry.get("base", base)
        spread = entry.get("spread", spread)
    elif isinstance(entry, (list, tuple)) and len(entry) == 2:
        base, spread = entry
    try:
        base = float(base)
    except (TypeError, ValueError):
        base = float(default_base)
    try:
        spread = float(spread)
    except (TypeError, ValueError):
        spread = float(default_spread)
    return base, abs(spread)


def _randomized_param(
    base: float,
    spread: float,
    randomness: float,
    rng: np.random.Generator,
) -> float:
    if randomness <= 0.0 or spread <= 0.0:
        return float(base)
    deviation = rng.uniform(-spread, spread)
    return float(base) + float(deviation) * float(randomness)


def _resolve_trend_direction(pattern: Any, profile_cfg: Dict[str, Any]) -> str:
    raw = profile_cfg.get("trend_direction") or profile_cfg.get("direction")
    if isinstance(raw, str) and raw.strip():
        return "down" if raw.strip().lower().startswith("d") else "up"
    if isinstance(pattern, str):
        lowered = pattern.lower()
        if "up" in lowered and "down" not in lowered:
            return "up"
        if "down" in lowered:
            return "down"
    return "down"


def _generate_trend_curve(
    duration_s: float,
    sampling_rate: float,
    direction: str,
    profile_cfg: Dict[str, Any],
    rng: np.random.Generator,
    shape_randomness: float,
) -> np.ndarray:
    if duration_s <= 0.0:
        return np.zeros(0, dtype=float)

    num_points = max(2, int(round(duration_s * sampling_rate)))
    t_master = np.linspace(0.0, 1.0, num_points)

    view_start_base, view_start_spread = _resolve_param(profile_cfg, "view_start", 0.1, 0.1)
    view_end_base, view_end_spread = _resolve_param(profile_cfg, "view_end", 0.85, 0.1)
    start_steep_base, start_steep_spread = _resolve_param(profile_cfg, "start_steepness", 15.0, 5.0)
    end_steep_base, end_steep_spread = _resolve_param(profile_cfg, "end_steepness", 10.0, 5.0)

    view_start = _randomized_param(view_start_base, view_start_spread, shape_randomness, rng)
    view_end = _randomized_param(view_end_base, view_end_spread, shape_randomness, rng)
    start_steep = _randomized_param(start_steep_base, start_steep_spread, shape_randomness, rng)
    end_steep = _randomized_param(end_steep_base, end_steep_spread, shape_randomness, rng)

    view_start = float(np.clip(view_start, 0.0, 0.9))
    min_width = float(profile_cfg.get("min_view_width", 0.05))
    view_end = float(np.clip(view_end, view_start + min_width, 1.0))

    direction_sign = -1.0 if str(direction).lower().startswith("d") else 1.0
    p0, p1 = (0.0, 1.0) if direction_sign > 0 else (1.0, 0.0)
    m0 = float(start_steep) * direction_sign
    m1 = float(end_steep) * direction_sign

    h00 = 2 * t_master**3 - 3 * t_master**2 + 1
    h10 = t_master**3 - 2 * t_master**2 + t_master
    h01 = -2 * t_master**3 + 3 * t_master**2
    h11 = t_master**3 - t_master**2
    y_master = (h00 * p0) + (h10 * m0) + (h01 * p1) + (h11 * m1)

    idx_start = int(view_start * (num_points - 1))
    idx_end = int(view_end * (num_points - 1))
    if idx_end <= idx_start:
        idx_end = min(num_points - 1, idx_start + 1)
    y_cropped = y_master[idx_start:idx_end]
    if y_cropped.size < 2:
        y_cropped = y_master

    if y_cropped.size != num_points:
        x_old = np.linspace(0.0, 1.0, y_cropped.size)
        x_new = np.linspace(0.0, 1.0, num_points)
        y_cropped = np.interp(x_new, x_old, y_cropped)

    y_min = float(np.min(y_cropped))
    y_max = float(np.max(y_cropped))
    if y_max - y_min < 1e-9:
        return np.zeros_like(y_cropped, dtype=float)
    return (y_cropped - y_min) / (y_max - y_min)


def _apply_noise(
    y_active: np.ndarray,
    *,
    noise_randomness: float,
    profile_cfg: Dict[str, Any],
    rng: np.random.Generator,
) -> np.ndarray:
    if y_active.size == 0:
        return y_active
    if noise_randomness <= 0.0:
        return np.clip(y_active, 0.0, None)

    jitter_base = float(profile_cfg.get("jitter_intensity", 0.08))
    wander_base = float(profile_cfg.get("wander_intensity", 0.03))
    hetero_offset = float(profile_cfg.get("hetero_offset", 0.2))

    jitter_intensity = jitter_base * noise_randomness
    wander_intensity = wander_base * noise_randomness

    white_noise = rng.normal(0.0, jitter_intensity, size=y_active.size)
    hetero_noise = white_noise * (y_active + hetero_offset)

    random_walk = np.cumsum(rng.normal(0.0, wander_intensity, size=y_active.size))
    if y_active.size > 1:
        trend = np.polyfit(np.arange(y_active.size), random_walk, 1)
        detrended_walk = random_walk - np.poly1d(trend)(np.arange(y_active.size))
    else:
        detrended_walk = random_walk

    y_noisy = y_active + hetero_noise + detrended_walk
    return np.clip(y_noisy, 0.0, None)


def _largest_remainder(weights: np.ndarray, total: int) -> np.ndarray:
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


def make_counts_from_profile(
    total_vehicles: int,
    episode_duration_s: int,
    bin_seconds: int,
    pattern: str,
    *,
    demand_profile: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Generate integer vehicle counts per bin using a single Hermite + noise profile."""
    total = max(0, int(round(total_vehicles)))
    duration_s = max(0.0, float(episode_duration_s))
    bin_seconds = max(1, int(bin_seconds))

    bins = int(np.ceil(duration_s / float(bin_seconds))) if duration_s > 0 else 0
    if total == 0 or bins == 0:
        return np.zeros(max(0, bins), dtype=int)

    profile_cfg = _resolve_profile_cfg(demand_profile)
    sampling_rate = float(profile_cfg.get("sampling_rate_hz", 1.0))
    if sampling_rate <= 0.0:
        sampling_rate = 1.0

    cooldown_duration = float(profile_cfg.get("cooldown_duration_s", 0.0) or 0.0)
    active_duration = profile_cfg.get("active_duration_s")
    if active_duration in (None, "", False):
        active_duration = duration_s - cooldown_duration
    try:
        active_duration = float(active_duration)
    except (TypeError, ValueError):
        active_duration = duration_s

    if active_duration < 0.0:
        active_duration = duration_s
        cooldown_duration = 0.0
    if active_duration + cooldown_duration > duration_s:
        cooldown_duration = max(0.0, min(cooldown_duration, duration_s))
        active_duration = max(0.0, duration_s - cooldown_duration)

    shape_randomness = float(profile_cfg.get("shape_randomness", 0.0))
    shape_randomness = float(np.clip(shape_randomness, 0.0, 1.0))
    noise_randomness = float(profile_cfg.get("noise_randomness", 0.0))
    noise_randomness = float(np.clip(noise_randomness, 0.0, 1.0))

    if seed is None:
        shape_rng = np.random.default_rng()
        noise_rng = np.random.default_rng()
    else:
        seed_seq = np.random.SeedSequence(int(seed))
        seeds = seed_seq.spawn(2)
        shape_rng = np.random.default_rng(seeds[0])
        noise_rng = np.random.default_rng(seeds[1])

    direction = _resolve_trend_direction(pattern, profile_cfg)
    y_active = _generate_trend_curve(
        active_duration, sampling_rate, direction, profile_cfg, shape_rng, shape_randomness
    )

    y_noisy = _apply_noise(y_active, noise_randomness=noise_randomness, profile_cfg=profile_cfg, rng=noise_rng)

    dt = 1.0 / sampling_rate
    current_integral = float(np.sum(y_noisy)) * dt
    if current_integral <= 0.0:
        return np.zeros(max(0, bins), dtype=int)

    scaling_factor = float(total) * 3600.0 / current_integral
    y_scaled = y_noisy * scaling_factor

    total_samples = max(1, int(round(duration_s * sampling_rate)))
    active_samples = int(round(active_duration * sampling_rate))
    cooldown_samples = int(round(cooldown_duration * sampling_rate))
    pad_samples = max(0, total_samples - active_samples - cooldown_samples)
    if active_samples < y_scaled.size:
        y_scaled = y_scaled[:active_samples]
    elif active_samples > y_scaled.size:
        pad = np.zeros(active_samples - y_scaled.size, dtype=float)
        y_scaled = np.concatenate([y_scaled, pad])

    y_final = np.concatenate(
        [y_scaled, np.zeros(cooldown_samples + pad_samples, dtype=float)]
    )
    if y_final.size < total_samples:
        y_final = np.concatenate(
            [y_final, np.zeros(total_samples - y_final.size, dtype=float)]
        )

    expected = y_final / 3600.0 * dt
    weights = np.zeros(bins, dtype=float)
    for idx, exp in enumerate(expected):
        t = idx * dt
        if t >= duration_s:
            break
        bin_idx = min(int(t // bin_seconds), bins - 1)
        weights[bin_idx] += float(exp)

    return _largest_remainder(weights, total)
