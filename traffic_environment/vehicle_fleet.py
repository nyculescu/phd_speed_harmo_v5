# traffic_environment/vehicle_fleet.py
"""
Diversified vehicle fleet generator for v5.1 ramps_v2 topology.

Adapted from v4's rou_writer.py, which ran 700+ parallel SUMO workers
reliably with these parameter ranges. The v4 fleet produced realistic
merge dynamics without collision storms because:

  1. sigma stays at 0.20-0.50 (v4 never exceeded 0.5 for HDVs)
  2. tau ranges from 1.2-2.0s (higher than SUMO default 1.0s)
  3. Vehicle heterogeneity creates natural speed differentials
  4. Three HDV compliance groups model real-world driver diversity
  5. CAVs have sigma=0.0, tau=1.0 (deterministic, responsive)

Vehicle classes and their traffic role:
  - Passenger cars (60-70% of fleet): fast, small gap, variable compliance
  - Passenger vans (10-15%): slower acceleration, larger gap
  - Trucks (8-12%): slow, large, restrict to right lanes in practice
  - Truck-trailers (3-5%): very slow, very large, create speed differentials
  - Buses (2-5%): slow, large, frequent stops (if applicable)

HDV compliance groups (applied to each vehicle class):
  - Fully compliant (share varies): sigma=0.25, speedFactor=1.0, speedDev=0.0
  - Under-compliant (share varies):  sigma=0.20, speedFactor=1.0, speedDev=0.05
  - Non-compliant (share varies):    sigma=0.20, speedFactor=1.1, speedDev=0.6

Lane-change parameters from v4 (empirically stable):
  - lcStrategic:  0.4-0.7  (eagerness for mandatory lane changes)
  - lcCooperative: 0.2-1.0 (willingness to yield for merging vehicles)
  - lcSpeedGain:  2.0-8.0  (eagerness for discretionary lane changes)
  - lcAssertive:  0.5-1.0  (gap acceptance aggressiveness)

References:
  - Krauss model: sigma creates perturbations; sigma=0.5 gives stochastic
    breakdown at ~50 veh/km (SUMO docs/RoadCapacity)
  - tau = 1.2-2.0s: realistic human reaction time (Green, 2000;
    Johansson & Rumar, 1971: mean 1.5s for expected events)
  - Vehicle type distribution: FHWA Vehicle Classification (2014)
  - Compliance groups: Hua & Fan (2023): 50% HDV imperfection
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# ── Base vehicle specifications ──────────────────────────────────────────────
# Length, minGap, accel/decel ranges, sigma, maxSpeed range
# These match v4's _DEFAULT_BASE_SPECS exactly.

BASE_SPECS: Dict[str, Dict[str, Any]] = {
    "passenger": {
        "vClass": "passenger",
        "color": "1,1,0",
        "length": 4.5,
        "min_gap": 2.5,
        "accel_range": (2.4, 2.8),
        "decel_range": (4.3, 4.7),
        "sigma": 0.50,
        "max_speed_range": (35.0, 40.0),  # 126-144 kph
    },
    "passenger_van": {
        "vClass": "passenger",
        "color": "1,0.8,0",
        "length": 6.0,
        "min_gap": 3.0,
        "accel_range": (2.0, 2.4),
        "decel_range": (4.0, 4.5),
        "sigma": 0.50,
        "max_speed_range": (30.0, 35.0),  # 108-126 kph
    },
    "truck": {
        "vClass": "truck",
        "color": "0.5,0.5,0.5",
        "length": 7.5,
        "min_gap": 3.5,
        "accel_range": (1.8, 2.2),
        "decel_range": (3.5, 4.0),
        "sigma": 0.40,
        "max_speed_range": (27.0, 30.0),  # 97-108 kph
    },
    "truck_trailer": {
        "vClass": "trailer",
        "color": "0.3,0.3,0.3",
        "length": 16.5,
        "min_gap": 4.0,
        "accel_range": (1.2, 1.5),
        "decel_range": (3.0, 3.5),
        "sigma": 0.40,
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

# ── HDV compliance groups ────────────────────────────────────────────────────

COMPLIANCE_GROUPS: Dict[str, Dict[str, Any]] = {
    "fully_compliant": {
        "suffix": "fc",
        "sigma": 0.25,
        "speed_factor": 1.0,
        "speed_dev": 0.0,
        "max_speed_mult": 1.0,
        "share": 0.50,  # 50% of HDVs
    },
    "under_compliant": {
        "suffix": "uc",
        "sigma": 0.20,
        "speed_factor": 1.0,
        "speed_dev": 0.05,
        "max_speed_mult": 1.1,
        "share": 0.35,  # 35% of HDVs
    },
    "non_compliant": {
        "suffix": "nc",
        "sigma": 0.20,
        "speed_factor": 1.1,
        "speed_dev": 0.60,
        "max_speed_mult": 1.2,
        "share": 0.15,  # 15% of HDVs
    },
}

# ── Lane-change parameter ranges (from v4, empirically stable) ───────────────

LC_RANGES: Dict[str, Tuple[float, float]] = {
    "lcStrategic": (0.4, 0.7),
    "lcCooperative": (0.2, 1.0),
    "lcSpeedGain": (2.0, 8.0),
    "lcAssertive": (0.5, 1.0),
}

# ── HDV tau (reaction time) range ────────────────────────────────────────────
TAU_RANGE: Tuple[float, float] = (1.2, 2.0)
MIN_GAP_SCALE_RANGE: Tuple[float, float] = (0.9, 1.1)

# ── CAV multipliers ──────────────────────────────────────────────────────────
CAV_CONFIG: Dict[str, float] = {
    "accel_mult": 1.1,       # 10% better acceleration
    "decel_mult": 1.05,      # 5% better braking
    "min_gap_scale": 0.5,    # 50% smaller gaps (platoon-capable)
    "sigma": 0.0,            # No driving variability (deterministic)
    "tau": 1.0,              # Minimal reaction time
    "speed_factor": 1.0,
    "speed_dev": 0.0,
}


def generate_fleet_xml(
    n_variants_hdv: int = 10,
    n_variants_cav: int = 5,
    seed: int = 42,
    step_length: float = 1.0,
) -> str:
    """
    Generate XML vType definitions for a diversified vehicle fleet.

    Returns a string of <vType> elements ready to embed in a .rou.xml file.

    Each (vehicle_class × compliance_group) gets n_variants_hdv variants
    with randomized parameters within the specified ranges. CAVs get
    n_variants_cav variants per vehicle class.

    Total types generated:
      HDV: len(BASE_SPECS) × len(COMPLIANCE_GROUPS) × n_variants_hdv
      CAV: len(BASE_SPECS) × n_variants_cav
    """
    rng = np.random.RandomState(seed)
    lines = []

    # ── HDV variants ─────────────────────────────────────────────────────
    for vtype_name, specs in BASE_SPECS.items():
        accel_lo, accel_hi = specs["accel_range"]
        decel_lo, decel_hi = specs["decel_range"]
        spd_lo, spd_hi = specs["max_speed_range"]
        base_gap = specs["min_gap"]
        length = specs["length"]
        vclass = specs["vClass"]
        color = specs["color"]

        for grp_name, grp in COMPLIANCE_GROUPS.items():
            for i in range(n_variants_hdv):
                vid = f"HDV_{grp['suffix']}_{vtype_name}_v{i}"

                accel = rng.uniform(accel_lo, accel_hi)
                decel = rng.uniform(decel_lo, decel_hi)
                max_spd = rng.uniform(spd_lo, spd_hi) * grp["max_speed_mult"]
                gap = base_gap * rng.uniform(*MIN_GAP_SCALE_RANGE)
                tau = rng.uniform(*TAU_RANGE)

                # Action step from tau (v4 approach)
                max_steps = max(1, int(tau / max(step_length, 1e-6)))
                action_step = max(1, rng.randint(1, max_steps + 1)) * step_length

                lc_strategic = rng.uniform(*LC_RANGES["lcStrategic"])
                lc_cooperative = rng.uniform(*LC_RANGES["lcCooperative"])
                lc_speed_gain = rng.uniform(*LC_RANGES["lcSpeedGain"])
                lc_assertive = rng.uniform(*LC_RANGES["lcAssertive"])

                lines.append(
                    f'  <vType id="{vid}" carFollowModel="Krauss" '
                    f'vClass="{vclass}" color="{color}" '
                    f'length="{length:.1f}" minGap="{gap:.2f}" '
                    f'accel="{accel:.2f}" decel="{decel:.2f}" '
                    f'maxSpeed="{max_spd:.2f}" '
                    f'sigma="{grp["sigma"]:.2f}" tau="{tau:.2f}" '
                    f'actionStepLength="{action_step:.2f}" '
                    f'speedFactor="{grp["speed_factor"]:.2f}" '
                    f'speedDev="{grp["speed_dev"]:.2f}" '
                    f'laneChangeModel="LC2013" '
                    f'lcStrategic="{lc_strategic:.2f}" '
                    f'lcCooperative="{lc_cooperative:.2f}" '
                    f'lcSpeedGain="{lc_speed_gain:.2f}" '
                    f'lcAssertive="{lc_assertive:.2f}"/>'
                )

    # ── CAV variants ─────────────────────────────────────────────────────
    for vtype_name, specs in BASE_SPECS.items():
        accel_lo, accel_hi = specs["accel_range"]
        decel_lo, decel_hi = specs["decel_range"]
        spd_lo, spd_hi = specs["max_speed_range"]
        base_gap = specs["min_gap"]
        length = specs["length"]
        vclass = specs["vClass"]

        for i in range(n_variants_cav):
            vid = f"CAV_{vtype_name}_v{i}"

            accel = rng.uniform(accel_lo, accel_hi) * CAV_CONFIG["accel_mult"]
            decel = rng.uniform(decel_lo, decel_hi) * CAV_CONFIG["decel_mult"]
            max_spd = rng.uniform(spd_lo, spd_hi)
            gap = base_gap * CAV_CONFIG["min_gap_scale"]

            lines.append(
                f'  <vType id="{vid}" carFollowModel="Krauss" '
                f'vClass="{vclass}" color="0,1,0" '
                f'length="{length:.1f}" minGap="{gap:.2f}" '
                f'accel="{accel:.2f}" decel="{decel:.2f}" '
                f'maxSpeed="{max_spd:.2f}" '
                f'sigma="{CAV_CONFIG["sigma"]:.2f}" '
                f'tau="{CAV_CONFIG["tau"]:.2f}" '
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

    For HDVs: picks vehicle class by FLEET_MIX, then compliance group
    by COMPLIANCE_GROUPS shares, then a random variant index.

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
        # Pick compliance group
        grp_names = list(COMPLIANCE_GROUPS.keys())
        grp_shares = [COMPLIANCE_GROUPS[g]["share"] for g in grp_names]
        total = sum(grp_shares)
        grp_probs = [s / total for s in grp_shares]
        grp = grp_names[rng.choice(len(grp_names), p=grp_probs)]
        suffix = COMPLIANCE_GROUPS[grp]["suffix"]

        vi = rng.randint(0, n_variants_hdv)
        return f"HDV_{suffix}_{vclass}_v{vi}"
