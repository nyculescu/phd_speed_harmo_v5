# traffic_environment/vehicle_fleet.py
"""
Diversified vehicle fleet generator for v5.1 ramps_v2 topology.

Fleet composition:
  - Normal HDVs (95-97% of HDV population): standard Krauss parameters
  - Reckless outliers (3-5% of HDV population): aggressive drivers that
    ignore safe following distances, exceed speed limits, and make
    assertive lane changes — the kind of driver that triggers merge
    conflicts and shockwaves unpredictably
  - CAVs: deterministic, responsive, directly controlled by the agent

Vehicle classes and their traffic role:
  - Passenger cars (70% of fleet): fast, small gap, variable behavior
  - Passenger vans (12%): slower acceleration, larger gap
  - Trucks (12%): slow, large, restrict to right lanes in practice
  - Truck-trailers (6%): very slow, very large, create speed differentials

Reckless outlier model (replaces v4's compliance groups):
  - speedFactor = 1.15-1.25 (15-25% over the limit)
  - sigma = 0.6 (high driving variability / imperfection)
  - tau = 0.6-0.9 (dangerously short reaction time)
  - minGap × 0.5-0.7 (tailgating)
  - lcAssertive = 1.5-3.0 (aggressive gap acceptance)
  - lcSpeedGain = 5.0-12.0 (frequent discretionary lane changes)

Weather effects modify all vehicle types:
  - Rain: lower accel/decel, larger gaps, slower speeds, longer tau
  - Heavy rain: more severe than rain
  - Fog: reduced visibility proxy via larger tau and speed reduction

References:
  - Krauss model: SUMO docs/Models/Car-Following-Models/Krauss
  - Reaction time: Green (2000); Johansson & Rumar (1971): mean 1.5s
  - Vehicle distribution: FHWA Vehicle Classification (2014)
  - Reckless drivers: Hua & Fan (2023): 50% HDV imperfection;
    our 3-5% reckless is more targeted — represents true outliers
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# ── Base vehicle specifications ──────────────────────────────────────────────

BASE_SPECS: Dict[str, Dict[str, Any]] = {
    "passenger": {
        "vClass": "passenger",
        "color": "1,1,0",
        "length": 4.5,
        "min_gap": 2.5,
        "accel_range": (2.4, 2.8),
        "decel_range": (4.3, 4.7),
        "sigma": 0.40,
        "max_speed_range": (35.0, 40.0),  # 126-144 kph
    },
    "passenger_van": {
        "vClass": "passenger",
        "color": "1,0.8,0",
        "length": 6.0,
        "min_gap": 3.0,
        "accel_range": (2.0, 2.4),
        "decel_range": (4.0, 4.5),
        "sigma": 0.40,
        "max_speed_range": (30.0, 35.0),  # 108-126 kph
    },
    "truck": {
        "vClass": "truck",
        "color": "0.5,0.5,0.5",
        "length": 7.5,
        "min_gap": 3.5,
        "accel_range": (1.8, 2.2),
        "decel_range": (3.5, 4.0),
        "sigma": 0.35,
        "max_speed_range": (27.0, 30.0),  # 97-108 kph
    },
    "truck_trailer": {
        "vClass": "trailer",
        "color": "0.3,0.3,0.3",
        "length": 16.5,
        "min_gap": 4.0,
        "accel_range": (1.2, 1.5),
        "decel_range": (3.0, 3.5),
        "sigma": 0.35,
        "max_speed_range": (23.0, 25.0),  # 83-90 kph
    },
}

# Fleet composition probabilities (must sum to 1.0)
FLEET_MIX: Dict[str, float] = {
    "passenger": 0.70,
    "passenger_van": 0.12,
    "truck": 0.12,
    "truck_trailer": 0.06,
}

# ── Lane-change parameter ranges (from v4, empirically stable) ───────────────

LC_RANGES_NORMAL: Dict[str, Tuple[float, float]] = {
    "lcStrategic": (0.4, 0.7),
    "lcCooperative": (0.3, 1.0),
    "lcSpeedGain": (2.0, 8.0),
    "lcAssertive": (0.5, 1.0),
}

LC_RANGES_RECKLESS: Dict[str, Tuple[float, float]] = {
    "lcStrategic": (0.6, 1.0),
    "lcCooperative": (0.0, 0.3),   # uncooperative
    "lcSpeedGain": (5.0, 12.0),    # aggressive lane-hopping
    "lcAssertive": (1.5, 3.0),     # forces into small gaps
}

# ── HDV parameters ──────────────────────────────────────────────────────────

NORMAL_HDV: Dict[str, Any] = {
    "sigma_range": (0.30, 0.50),
    "tau_range": (1.2, 2.0),
    "min_gap_scale_range": (0.9, 1.1),
    "speed_factor": 1.0,
    "speed_dev": 0.05,
    "share": 0.96,  # 96% of HDVs are normal
}

RECKLESS_HDV: Dict[str, Any] = {
    "sigma": 0.60,
    "tau_range": (0.6, 0.9),
    "min_gap_scale_range": (0.5, 0.7),   # tailgating
    "speed_factor_range": (1.15, 1.25),   # 15-25% over limit
    "speed_dev": 0.10,
    "share": 0.04,  # 4% of HDVs are reckless
}

# ── CAV configuration ───────────────────────────────────────────────────────

CAV_CONFIG: Dict[str, float] = {
    "accel_mult": 1.1,
    "decel_mult": 1.05,
    "min_gap_scale": 0.5,
    "sigma": 0.0,
    "tau": 1.0,
    "speed_factor": 1.0,
    "speed_dev": 0.0,
}

# ── Weather profiles ────────────────────────────────────────────────────────
# Multipliers applied to base vehicle parameters.
# Values < 1.0 = reduced capability; > 1.0 = increased.

WEATHER_PROFILES: Dict[str, Dict[str, float]] = {
    "clear": {
        "accel_mult": 1.0,
        "decel_mult": 1.0,
        "min_gap_mult": 1.0,
        "tau_mult": 1.0,
        "speed_factor_mult": 1.0,
        "sigma_add": 0.0,
    },
    "rain": {
        "accel_mult": 0.85,       # reduced acceleration (wet road)
        "decel_mult": 0.80,       # much reduced braking (wet road)
        "min_gap_mult": 1.30,     # larger following gaps
        "tau_mult": 1.25,         # slower reactions (spray, wipers)
        "speed_factor_mult": 0.90, # 10% speed reduction
        "sigma_add": 0.05,        # more driving variability
    },
    "heavy_rain": {
        "accel_mult": 0.75,
        "decel_mult": 0.70,
        "min_gap_mult": 1.50,
        "tau_mult": 1.50,
        "speed_factor_mult": 0.80,
        "sigma_add": 0.10,
    },
    "fog": {
        "accel_mult": 0.90,
        "decel_mult": 0.85,
        "min_gap_mult": 1.40,
        "tau_mult": 1.60,         # much slower reactions (visibility)
        "speed_factor_mult": 0.75, # 25% speed reduction
        "sigma_add": 0.08,
    },
}


def _apply_weather(
    accel: float, decel: float, min_gap: float, tau: float,
    sigma: float, speed_factor: float,
    weather: str,
) -> Tuple[float, float, float, float, float, float]:
    """Apply weather multipliers to a set of vehicle parameters."""
    wp = WEATHER_PROFILES.get(weather, WEATHER_PROFILES["clear"])
    return (
        accel * wp["accel_mult"],
        decel * wp["decel_mult"],
        min_gap * wp["min_gap_mult"],
        tau * wp["tau_mult"],
        min(sigma + wp["sigma_add"], 1.0),
        speed_factor * wp["speed_factor_mult"],
    )


def generate_fleet_xml(
    n_variants_hdv: int = 10,
    n_variants_cav: int = 5,
    seed: int = 42,
    step_length: float = 1.0,
    weather: str = "clear",
) -> str:
    """
    Generate XML vType definitions for a diversified vehicle fleet.

    Returns a string of <vType> elements ready to embed in a .rou.xml file.

    Fleet structure:
      - Normal HDV: BASE_SPECS × n_variants_hdv per vehicle class
      - Reckless HDV: BASE_SPECS × n_variants_hdv per vehicle class
        (same count, but picked less often by pick_vehicle_type)
      - CAV: BASE_SPECS × n_variants_cav per vehicle class

    Total types:
      Normal HDV:  len(BASE_SPECS) × n_variants_hdv
      Reckless HDV: len(BASE_SPECS) × n_variants_hdv
      CAV:          len(BASE_SPECS) × n_variants_cav
    """
    rng = np.random.RandomState(seed)
    lines = []

    for vtype_name, specs in BASE_SPECS.items():
        accel_lo, accel_hi = specs["accel_range"]
        decel_lo, decel_hi = specs["decel_range"]
        spd_lo, spd_hi = specs["max_speed_range"]
        base_gap = specs["min_gap"]
        length = specs["length"]
        vclass = specs["vClass"]
        color = specs["color"]

        # ── Normal HDV variants ─────────────────────────────────────────
        for i in range(n_variants_hdv):
            vid = f"HDV_normal_{vtype_name}_v{i}"

            accel = rng.uniform(accel_lo, accel_hi)
            decel = rng.uniform(decel_lo, decel_hi)
            max_spd = rng.uniform(spd_lo, spd_hi)
            sigma = rng.uniform(*NORMAL_HDV["sigma_range"])
            tau = rng.uniform(*NORMAL_HDV["tau_range"])
            gap = base_gap * rng.uniform(*NORMAL_HDV["min_gap_scale_range"])
            speed_factor = NORMAL_HDV["speed_factor"]
            speed_dev = NORMAL_HDV["speed_dev"]

            # Apply weather
            accel, decel, gap, tau, sigma, speed_factor = _apply_weather(
                accel, decel, gap, tau, sigma, speed_factor, weather,
            )

            # Action step from tau
            max_steps = max(1, int(tau / max(step_length, 1e-6)))
            action_step = max(1, rng.randint(1, max_steps + 1)) * step_length

            lc = LC_RANGES_NORMAL
            lines.append(
                f'  <vType id="{vid}" carFollowModel="Krauss" '
                f'vClass="{vclass}" color="{color}" '
                f'length="{length:.1f}" minGap="{gap:.2f}" '
                f'accel="{accel:.2f}" decel="{decel:.2f}" '
                f'maxSpeed="{max_spd:.2f}" '
                f'sigma="{sigma:.2f}" tau="{tau:.2f}" '
                f'actionStepLength="{action_step:.2f}" '
                f'speedFactor="{speed_factor:.2f}" '
                f'speedDev="{speed_dev:.2f}" '
                f'laneChangeModel="LC2013" '
                f'lcStrategic="{rng.uniform(*lc["lcStrategic"]):.2f}" '
                f'lcCooperative="{rng.uniform(*lc["lcCooperative"]):.2f}" '
                f'lcSpeedGain="{rng.uniform(*lc["lcSpeedGain"]):.2f}" '
                f'lcAssertive="{rng.uniform(*lc["lcAssertive"]):.2f}"/>'
            )

        # ── Reckless HDV variants ───────────────────────────────────────
        for i in range(n_variants_hdv):
            vid = f"HDV_reckless_{vtype_name}_v{i}"

            accel = rng.uniform(accel_lo, accel_hi) * 1.1  # slightly faster accel
            decel = rng.uniform(decel_lo, decel_hi)
            max_spd = rng.uniform(spd_lo, spd_hi) * 1.15  # higher top speed
            sigma = RECKLESS_HDV["sigma"]
            tau = rng.uniform(*RECKLESS_HDV["tau_range"])
            gap = base_gap * rng.uniform(*RECKLESS_HDV["min_gap_scale_range"])
            speed_factor = rng.uniform(*RECKLESS_HDV["speed_factor_range"])
            speed_dev = RECKLESS_HDV["speed_dev"]

            # Apply weather (even reckless drivers slow down in rain — somewhat)
            accel, decel, gap, tau, sigma, speed_factor = _apply_weather(
                accel, decel, gap, tau, sigma, speed_factor, weather,
            )

            action_step = max(1, int(tau / max(step_length, 1e-6))) * step_length

            lc = LC_RANGES_RECKLESS
            lines.append(
                f'  <vType id="{vid}" carFollowModel="Krauss" '
                f'vClass="{vclass}" color="1,0,0" '  # red = reckless
                f'length="{length:.1f}" minGap="{gap:.2f}" '
                f'accel="{accel:.2f}" decel="{decel:.2f}" '
                f'maxSpeed="{max_spd:.2f}" '
                f'sigma="{sigma:.2f}" tau="{tau:.2f}" '
                f'actionStepLength="{action_step:.2f}" '
                f'speedFactor="{speed_factor:.2f}" '
                f'speedDev="{speed_dev:.2f}" '
                f'laneChangeModel="LC2013" '
                f'lcStrategic="{rng.uniform(*lc["lcStrategic"]):.2f}" '
                f'lcCooperative="{rng.uniform(*lc["lcCooperative"]):.2f}" '
                f'lcSpeedGain="{rng.uniform(*lc["lcSpeedGain"]):.2f}" '
                f'lcAssertive="{rng.uniform(*lc["lcAssertive"]):.2f}"/>'
            )

        # ── CAV variants ────────────────────────────────────────────────
        for i in range(n_variants_cav):
            vid = f"CAV_{vtype_name}_v{i}"

            accel = rng.uniform(accel_lo, accel_hi) * CAV_CONFIG["accel_mult"]
            decel = rng.uniform(decel_lo, decel_hi) * CAV_CONFIG["decel_mult"]
            max_spd = rng.uniform(spd_lo, spd_hi)
            gap = base_gap * CAV_CONFIG["min_gap_scale"]

            # CAVs are less affected by weather (sensor-based, not visual)
            # but still affected by road conditions (traction)
            cav_accel, cav_decel, cav_gap, _, _, _ = _apply_weather(
                accel, decel, gap, CAV_CONFIG["tau"],
                CAV_CONFIG["sigma"], CAV_CONFIG["speed_factor"], weather,
            )
            # CAVs keep their tau and sigma regardless of weather
            cav_tau = CAV_CONFIG["tau"]
            cav_sigma = CAV_CONFIG["sigma"]

            lines.append(
                f'  <vType id="{vid}" carFollowModel="Krauss" '
                f'vClass="{vclass}" color="0,1,0" '
                f'length="{length:.1f}" minGap="{cav_gap:.2f}" '
                f'accel="{cav_accel:.2f}" decel="{cav_decel:.2f}" '
                f'maxSpeed="{max_spd:.2f}" '
                f'sigma="{cav_sigma:.2f}" '
                f'tau="{cav_tau:.2f}" '
                f'actionStepLength="{step_length:.2f}" '
                f'speedFactor="{CAV_CONFIG["speed_factor"]:.2f}" '
                f'speedDev="{CAV_CONFIG["speed_dev"]:.2f}" '
                f'laneChangeModel="LC2013" '
                f'lcStrategic="1.00" '
                f'lcCooperative="1.00" '
                f'lcSpeedGain="1.00" '
                f'lcAssertive="1.00"/>'
            )

    return "\n".join(lines)


def pick_vehicle_type(
    rng: np.random.RandomState,
    is_cav: bool,
    n_variants_hdv: int = 10,
    n_variants_cav: int = 5,
) -> str:
    """
    Pick a vehicle type ID for a new departure.

    For HDVs: picks vehicle class by FLEET_MIX, then normal vs reckless
    by their share probabilities, then a random variant index.

    For CAVs: picks vehicle class by FLEET_MIX, then a random variant.
    """
    # Pick vehicle class
    classes = list(FLEET_MIX.keys())
    probs = [FLEET_MIX[c] for c in classes]
    vclass = classes[rng.choice(len(classes), p=probs)]

    if is_cav:
        vi = rng.randint(0, n_variants_cav)
        return f"CAV_{vclass}_v{vi}"
    else:
        # Normal vs reckless
        is_reckless = rng.random() < RECKLESS_HDV["share"]
        prefix = "HDV_reckless" if is_reckless else "HDV_normal"
        vi = rng.randint(0, n_variants_hdv)
        return f"{prefix}_{vclass}_v{vi}"
