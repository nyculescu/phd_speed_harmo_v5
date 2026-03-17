# traffic_environment/rou_writer.py
"""Helpers for emitting SUMO route files."""

from __future__ import annotations

import logging
import os
import platform
import tempfile
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger(__name__)

__all__ = [
    "flow_generation_single_file",
    "create_vehicle_types_with_variants",
    "create_homogeneous_vehicle_types",
    "write_file_atomic",
    "prettify_xml",
]

NETWORK_CONFIG_FILE_4_TO_3 = Path(__file__).parent / "sumo" / "network_config_4_3.yaml"


def _to_plain(value: Any) -> Any:
    if hasattr(value, "items"):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_to_plain(v) for v in value)
    return value


def _normalize_network_topology(value: Any) -> str:
    if value in (None, "", False):
        return "merge_4_to_3_v0"
    raw = str(value).strip().lower()
    cleaned = raw.replace("-", "_")
    if cleaned in {"merge_4_to_3_v0", "m43v0", "merge43v0", "merge_4_to_3", "merge43", "m43"}:
        return "merge_4_to_3_v0"
    return cleaned


_DEFAULT_BASE_SPECS: Dict[str, Dict[str, Any]] = {
    "passenger": {
        "vClass": "passenger",
        "color": "1,1,0",
        "length": 4.5,
        "min_gap": 2.5,
        "accel_range": (2.4, 2.8),
        "decel_range": (4.3, 4.7),
        "sigma": 0.5,
        "max_speed_range": (35.0, 40.0),
    },
    "passenger_van": {
        "vClass": "passenger",
        "color": "1,0.8,0",
        "length": 6.0,
        "min_gap": 3.0,
        "accel_range": (2.0, 2.4),
        "decel_range": (4.0, 4.5),
        "sigma": 0.5,
        "max_speed_range": (30.0, 35.0),
    },
    "bus": {
        "vClass": "bus",
        "color": "0,0,1",
        "length": 12.0,
        "min_gap": 3.5,
        "accel_range": (1.5, 1.8),
        "decel_range": (3.5, 4.0),
        "sigma": 0.4,
        "max_speed_range": (25.0, 28.0),
    },
    "truck": {
        "vClass": "truck",
        "color": "0.5,0.5,0.5",
        "length": 7.5,
        "min_gap": 3.5,
        "accel_range": (1.8, 2.2),
        "decel_range": (3.5, 4.0),
        "sigma": 0.4,
        "max_speed_range": (27.0, 30.0),
    },
    "truck_trailer": {
        "vClass": "trailer",
        "color": "0.3,0.3,0.3",
        "length": 16.5,
        "min_gap": 4.0,
        "accel_range": (1.2, 1.5),
        "decel_range": (3.0, 3.5),
        "sigma": 0.4,
        "max_speed_range": (23.0, 25.0),
    },
}

_DEFAULT_HEAVY_SCALARS: Dict[str, float] = {
    "passenger": 1.3,
    "passenger_van": 1.2,
    "bus": 0.4,
    "truck": 0.3,
    "truck_trailer": 0.2,
}

_DEFAULT_COMPLIANCE_GROUPS: Dict[str, Dict[str, Any]] = {
    "fully_compliant": {
        "id_suffix": "fc",
        "id_prefix": "HDV_fc",
        "sigma": 0.25,
        "speed_factor": 1.0,
        "speed_dev": 0.0,
        "max_speed_multiplier": 1.0,
        "share": 1.0,
    },
    "under_compliant": {
        "id_suffix": "uc",
        "id_prefix": "HDV_uc",
        "sigma": 0.20,
        "speed_factor": 1.0,
        "speed_dev": 0.05,
        "max_speed_multiplier": 1.1,
        "share": 1.0,
    },
    "non_compliant": {
        "id_suffix": "nc",
        "id_prefix": "HDV_nc",
        "sigma": 0.20,
        "speed_factor": 1.1,
        "speed_dev": 0.6,
        "max_speed_multiplier": 1.2,
        "share": 1.0,
    },
}


def _ensure_range(value: Any, default: tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return float(value[0]), float(value[1])
        except (TypeError, ValueError):
            return default
    return default


def _resolve_vehicle_randomization(random_cfg: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = _to_plain(random_cfg) if random_cfg else {}

    base_specs = deepcopy(_DEFAULT_BASE_SPECS)
    base_overrides = cfg.get("hdv_base_specs", {}) or {}
    for name, overrides in base_overrides.items():
        overrides = overrides or {}
        target = base_specs.get(name, {
            "vClass": str(overrides.get("vClass", name)),
            "color": overrides.get("color", "1,1,0"),
            "length": 4.5,
            "min_gap": 2.5,
            "accel_range": (2.0, 2.5),
            "decel_range": (3.5, 4.0),
            "sigma": 0.4,
            "max_speed_range": (25.0, 35.0),
        })
        if "vClass" in overrides:
            target["vClass"] = overrides["vClass"]
        if "color" in overrides:
            target["color"] = overrides["color"]
        if "length" in overrides:
            target["length"] = float(overrides["length"])
        if "min_gap" in overrides or "minGap" in overrides:
            target["min_gap"] = float(overrides.get("min_gap", overrides.get("minGap", target["min_gap"])))
        target["accel_range"] = _ensure_range(overrides.get("accel_range"), _ensure_range(overrides.get("accelRange"), target["accel_range"]))
        target["decel_range"] = _ensure_range(overrides.get("decel_range"), _ensure_range(overrides.get("decelRange"), target["decel_range"]))
        target["max_speed_range"] = _ensure_range(overrides.get("max_speed_range"), _ensure_range(overrides.get("maxSpeed_range"), target["max_speed_range"]))
        if "sigma" in overrides:
            target["sigma"] = float(overrides["sigma"])
        base_specs[name] = target

    compliance_cfg = cfg.get("hdv_compliance_groups", {}) or {}
    compliance_groups: List[Dict[str, Any]] = []
    seen_groups: set[str] = set()

    def _merge_compliance(name: str, defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        merged = defaults.copy()
        overrides = overrides or {}
        suffix = overrides.get("id_suffix", overrides.get("idSuffix", merged.get("id_suffix", name)))
        prefix = overrides.get("id_prefix", overrides.get("idPrefix", merged.get("id_prefix", f"HDV_{suffix}")))
        merged.update({
            "id_suffix": str(suffix),
            "id_prefix": str(prefix),
            "sigma": float(overrides.get("sigma", merged.get("sigma", 0.25))),
            "speed_factor": float(overrides.get("speed_factor", overrides.get("speedFactor", merged.get("speed_factor", 1.0)))),
            "speed_dev": float(overrides.get("speed_dev", overrides.get("speedDev", merged.get("speed_dev", 0.0)))),
            "max_speed_multiplier": float(overrides.get("max_speed_multiplier", overrides.get("maxSpeed_multiplier", merged.get("max_speed_multiplier", 1.0)))),
            "share": float(overrides.get("share", merged.get("share", 1.0))),
        })
        return merged

    for name, defaults in _DEFAULT_COMPLIANCE_GROUPS.items():
        merged = _merge_compliance(name, defaults, compliance_cfg.get(name, {}))
        compliance_groups.append({"name": name, **merged})
        seen_groups.add(name)

    for name, overrides in compliance_cfg.items():
        if name in seen_groups:
            continue
        merged = _merge_compliance(name, {
            "id_suffix": name,
            "id_prefix": f"HDV_{name}",
            "sigma": 0.25,
            "speed_factor": 1.0,
            "speed_dev": 0.0,
            "max_speed_multiplier": 1.0,
            "share": 1.0,
        }, overrides)
        compliance_groups.append({"name": name, **merged})
        seen_groups.add(name)

    if not compliance_groups:
        for name, defaults in _DEFAULT_COMPLIANCE_GROUPS.items():
            compliance_groups.append({"name": name, **defaults})

    sigma_scale_range = _ensure_range(cfg.get("hdv_sigma_scale_range"), (0.8, 1.2))
    min_gap_scale_range = _ensure_range(cfg.get("hdv_min_gap_scale_range"), (0.9, 1.1))
    tau_range = _ensure_range(cfg.get("hdv_tau_range"), (1.2, 2.0))
    reaction_steps_min = max(1, int(cfg.get("hdv_reaction_steps_min", 1)))

    lane_ranges_cfg = cfg.get("hdv_lane_change_ranges", {}) or {}
    lane_ranges = {
        "lcStrategic": _ensure_range(lane_ranges_cfg.get("lcStrategic"), (0.4, 0.7)),
        "lcCooperative": _ensure_range(lane_ranges_cfg.get("lcCooperative"), (0.2, 1.0)),
        "lcSpeedGain": _ensure_range(lane_ranges_cfg.get("lcSpeedGain"), (2.0, 8.0)),
        "lcAssertive": _ensure_range(lane_ranges_cfg.get("lcAssertive"), (0.5, 1.0)),
    }

    cav_cfg_raw = cfg.get("cav_multipliers", {}) or {}
    cav_cfg = {
        "accel": float(cav_cfg_raw.get("accel", 1.1)),
        "decel": float(cav_cfg_raw.get("decel", 1.05)),
        "min_gap_scale": float(cav_cfg_raw.get("min_gap_scale", cav_cfg_raw.get("minGap_scale", 0.5))),
        "sigma": float(cav_cfg_raw.get("sigma", 0.0)),
        "tau": float(cav_cfg_raw.get("tau", 1.0)),
        "speed_factor": float(cav_cfg_raw.get("speed_factor", cav_cfg_raw.get("speedFactor", 1.0))),
        "speed_dev": float(cav_cfg_raw.get("speed_dev", cav_cfg_raw.get("speedDev", 0.0))),
        "max_speed_multiplier": float(cav_cfg_raw.get("max_speed_multiplier", cav_cfg_raw.get("maxSpeed_multiplier", 1.0))),
    }

    generated_variants = max(1, int(cfg.get("generated_variants_per_type", 20)))
    variant_pick_upper = max(1, min(int(cfg.get("variant_pick_upper", generated_variants)), generated_variants))
    passenger_heavy_chance = max(0.0, float(cfg.get("passenger_heavy_chance", 0.15)))
    uniform_variation_pct = max(0.0, float(cfg.get("uniform_variation_pct", 0.15)))

    heavy_cfg = cfg.get("passenger_heavy_scalars", {}) or {}
    heavy_scalars: Dict[str, float] = {}
    for name in set(base_specs.keys()) | set(_DEFAULT_HEAVY_SCALARS.keys()) | set(heavy_cfg.keys()):
        heavy_scalars[name] = float(heavy_cfg.get(name, _DEFAULT_HEAVY_SCALARS.get(name, 1.0)))

    distribution_cfg_raw = cfg.get("hdv_compliance_distribution", {}) or {}
    compliance_distribution: Dict[str, Dict[str, float]] = {}
    for base_name, mapping in distribution_cfg_raw.items():
        plain = _to_plain(mapping) or {}
        compliance_distribution[base_name] = {k: float(v) for k, v in plain.items()}

    compliance_lookup = {group["name"]: group for group in compliance_groups}

    return {
        "base_specs": base_specs,
        "compliance_groups": compliance_groups,
        "compliance_lookup": compliance_lookup,
        "sigma_scale_range": sigma_scale_range,
        "min_gap_scale_range": min_gap_scale_range,
        "tau_range": tau_range,
        "reaction_steps_min": reaction_steps_min,
        "lane_ranges": lane_ranges,
        "cav_cfg": cav_cfg,
        "generated_variants": generated_variants,
        "variant_pick_upper": variant_pick_upper,
        "passenger_heavy_chance": passenger_heavy_chance,
        "uniform_variation_pct": uniform_variation_pct,
        "heavy_scalars": heavy_scalars,
        "compliance_distribution": compliance_distribution,
    }


def _apply_weather_to_randomization(
    resolved_randomization: Dict[str, Any],
    weather: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not weather:
        return resolved_randomization

    multipliers = (weather.get("multipliers") or {}) if isinstance(weather, dict) else {}
    hdv_mult = multipliers.get("hdv") or {}
    cav_mult = multipliers.get("cav") or {}

    out = deepcopy(resolved_randomization)

    hdv_accel = float(hdv_mult.get("accel", 1.0))
    hdv_decel = float(hdv_mult.get("decel", 1.0))
    hdv_min_gap = float(hdv_mult.get("min_gap", 1.0))
    hdv_tau = float(hdv_mult.get("tau", 1.0))
    hdv_speed_factor = float(hdv_mult.get("speed_factor", 1.0))
    hdv_speed_dev = float(hdv_mult.get("speed_dev", 1.0))

    for specs in out.get("base_specs", {}).values():
        accel_range = specs.get("accel_range", (1.0, 1.0))
        decel_range = specs.get("decel_range", (1.0, 1.0))
        specs["accel_range"] = (
            max(0.1, float(accel_range[0]) * hdv_accel),
            max(0.1, float(accel_range[1]) * hdv_accel),
        )
        specs["decel_range"] = (
            max(0.1, float(decel_range[0]) * hdv_decel),
            max(0.1, float(decel_range[1]) * hdv_decel),
        )
        specs["min_gap"] = max(0.1, float(specs.get("min_gap", 1.0)) * hdv_min_gap)

    tau_range = out.get("tau_range", (1.0, 1.0))
    out["tau_range"] = (
        max(0.1, float(tau_range[0]) * hdv_tau),
        max(0.1, float(tau_range[1]) * hdv_tau),
    )

    for group in out.get("compliance_groups", []):
        group["speed_factor"] = max(0.1, float(group.get("speed_factor", 1.0)) * hdv_speed_factor)
        group["speed_dev"] = max(0.0, float(group.get("speed_dev", 0.0)) * hdv_speed_dev)
        # FIXME: sigma multipliers are defined in the weather model but are not applied
        # to avoid IDM ambiguity. Revisit when using non-IDM models or empirical calibration.

    cav_accel = float(cav_mult.get("accel", 1.0))
    cav_decel = float(cav_mult.get("decel", 1.0))
    cav_min_gap = float(cav_mult.get("min_gap", 1.0))
    cav_tau = float(cav_mult.get("tau", 1.0))
    cav_speed_factor = float(cav_mult.get("speed_factor", 1.0))
    cav_speed_dev = float(cav_mult.get("speed_dev", 1.0))

    cav_cfg = out.get("cav_cfg", {})
    cav_cfg["accel"] = max(0.05, float(cav_cfg.get("accel", 1.0)) * cav_accel)
    cav_cfg["decel"] = max(0.05, float(cav_cfg.get("decel", 1.0)) * cav_decel)
    cav_cfg["min_gap_scale"] = max(0.1, float(cav_cfg.get("min_gap_scale", 0.5)) * cav_min_gap)
    cav_cfg["tau"] = max(0.1, float(cav_cfg.get("tau", 1.0)) * cav_tau)
    cav_cfg["speed_factor"] = max(0.1, float(cav_cfg.get("speed_factor", 1.0)) * cav_speed_factor)
    cav_cfg["speed_dev"] = max(0.0, float(cav_cfg.get("speed_dev", 0.0)) * cav_speed_dev)
    out["cav_cfg"] = cav_cfg

    return out


def write_file_atomic(content: str, target_path: str, use_sync: bool = True) -> None:
    """Write file atomically and drop a ``.complete`` marker."""
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=str(target_path.parent),
            delete=False,
            suffix=".tmp",
            encoding="utf-8",
        ) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(content)
            tmp_file.flush()
            if use_sync:
                os.fsync(tmp_file.fileno())

        if platform.system() == "Windows" and target_path.exists():
            target_path.unlink()
        os.replace(tmp_path, str(target_path))

        marker_path = target_path.with_suffix(target_path.suffix + ".complete")
        with marker_path.open("w", encoding="utf-8") as marker:
            marker.write(str(time.time()))
    except Exception:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def prettify_xml(elem: ET.Element) -> str:
    """Return a formatted XML string."""
    rough_string = ET.tostring(elem, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def create_vehicle_types_with_variants(
    num_variants: int = 5,
    num_variants_hdv: Optional[int] = None,
    num_variants_cav: Optional[int] = None,
    car_following_model_hdv: str = "Krauss",
    car_following_model_cav: str = "Krauss",
    car_following_model: Optional[str] = None,
    sim_step_length: float = 1.0,
    randomization_cfg: Optional[Dict[str, Any]] = None,
    resolved_randomization: Optional[Dict[str, Any]] = None,
) -> List[ET.Element]:
    """Build a heterogeneous fleet with HDV compliance sub-types and CAV variants."""
    if car_following_model is not None:
        car_following_model_hdv = car_following_model_cav = car_following_model

    resolved = resolved_randomization or _resolve_vehicle_randomization(randomization_cfg)

    base_specs = resolved["base_specs"]
    compliance_groups = resolved["compliance_groups"]
    min_gap_scale_range = resolved["min_gap_scale_range"]
    tau_range = resolved["tau_range"]
    reaction_steps_min = resolved["reaction_steps_min"]
    lane_ranges = resolved["lane_ranges"]
    cav_cfg = resolved["cav_cfg"]
    generated_variants = max(1, resolved.get("generated_variants", num_variants))
    hdv_variants = max(1, num_variants_hdv if num_variants_hdv is not None else generated_variants)
    cav_variants = max(1, num_variants_cav if num_variants_cav is not None else generated_variants)

    lc_strategic_range = lane_ranges["lcStrategic"]
    lc_cooperative_range = lane_ranges["lcCooperative"]
    lc_speed_gain_range = lane_ranges["lcSpeedGain"]
    lc_assertive_range = lane_ranges["lcAssertive"]

    cav_accel_mult = cav_cfg.get("accel", 1.1)
    cav_decel_mult = cav_cfg.get("decel", 1.05)
    cav_min_gap_scale = cav_cfg.get("min_gap_scale", 0.5)
    cav_speed_factor = cav_cfg.get("speed_factor", 1.0)
    cav_speed_dev = cav_cfg.get("speed_dev", 0.0)
    cav_sigma = cav_cfg.get("sigma", 0.0)
    cav_tau = cav_cfg.get("tau", 1.0)
    cav_max_speed_multiplier = cav_cfg.get("max_speed_multiplier", 1.0)

    all_vehicle_types: List[ET.Element] = []

    for vtype_name, specs in base_specs.items():
        accel_range = specs["accel_range"]
        decel_range = specs["decel_range"]
        max_speed_range = specs["max_speed_range"]
        min_gap_base = float(specs["min_gap"])
        length = float(specs["length"])
        vclass = str(specs["vClass"])
        color = str(specs["color"])

        for group in compliance_groups:
            group_prefix = group["id_prefix"]
            group_sigma = group["sigma"]
            group_speed_factor = group["speed_factor"]
            group_speed_dev = group["speed_dev"]
            group_speed_multiplier = group["max_speed_multiplier"]

            for i in range(hdv_variants):
                hdv_elem = ET.Element(
                    "vType",
                    carFollowModel=car_following_model_hdv,
                    id=f"{group_prefix}_{vtype_name}_v{i}",
                    vClass=vclass,
                    color=color,
                    length=f"{length:.2f}",
                )
                hdv_elem.set("accel", f"{np.random.uniform(*accel_range):.2f}")
                hdv_elem.set("decel", f"{np.random.uniform(*decel_range):.2f}")
                hdv_elem.set(
                    "maxSpeed",
                    f"{np.random.uniform(*max_speed_range) * group_speed_multiplier:.2f}",
                )
                hdv_elem.set("sigma", f"{group_sigma:.2f}")
                hdv_elem.set(
                    "minGap",
                    f"{min_gap_base * np.random.uniform(*min_gap_scale_range):.2f}",
                )
                tau_val = np.random.uniform(*tau_range)
                hdv_elem.set("tau", f"{tau_val:.2f}")
                max_reaction_steps = max(
                    reaction_steps_min, int(tau_val / max(sim_step_length, 1e-6))
                )
                if max_reaction_steps <= reaction_steps_min:
                    reaction_steps = reaction_steps_min
                else:
                    reaction_steps = np.random.randint(
                        reaction_steps_min, max_reaction_steps + 1
                    )
                hdv_elem.set("actionStepLength", f"{reaction_steps * sim_step_length:.2f}")
                hdv_elem.set("lcStrategic", f"{np.random.uniform(*lc_strategic_range):.2f}")
                hdv_elem.set(
                    "lcCooperative", f"{np.random.uniform(*lc_cooperative_range):.2f}"
                )
                hdv_elem.set("lcSpeedGain", f"{np.random.uniform(*lc_speed_gain_range):.2f}")
                hdv_elem.set("lcAssertive", f"{np.random.uniform(*lc_assertive_range):.2f}")
                hdv_elem.set("speedFactor", f"{group_speed_factor:.2f}")
                hdv_elem.set("speedDev", f"{group_speed_dev:.2f}")
                all_vehicle_types.append(hdv_elem)

        for i in range(cav_variants):
            cav_elem = ET.Element(
                "vType",
                carFollowModel=car_following_model_cav,
                id=f"CAV_{vtype_name}_v{i}",
                vClass=vclass,
                color="0,1,0",
                length=f"{length:.2f}",
            )
            cav_elem.set("accel", f"{np.random.uniform(*accel_range) * cav_accel_mult:.2f}")
            cav_elem.set("decel", f"{np.random.uniform(*decel_range) * cav_decel_mult:.2f}")
            cav_elem.set(
                "maxSpeed",
                f"{np.random.uniform(*max_speed_range) * cav_max_speed_multiplier:.2f}",
            )
            cav_elem.set("sigma", f"{cav_sigma:.2f}")
            cav_elem.set("minGap", f"{min_gap_base * cav_min_gap_scale:.2f}")
            cav_elem.set("tau", f"{cav_tau:.2f}")
            cav_elem.set("actionStepLength", f"{sim_step_length:.2f}")
            cav_elem.set("speedFactor", f"{cav_speed_factor:.2f}")
            cav_elem.set("speedDev", f"{cav_speed_dev:.2f}")
            all_vehicle_types.append(cav_elem)

    return all_vehicle_types


def create_homogeneous_vehicle_types(
    car_following_model_hdv: str = "Krauss",
    car_following_model_cav: str = "Krauss",
    car_following_model: Optional[str] = None,
    sim_step_length: float = 1.0,
    randomization_cfg: Optional[Dict[str, Any]] = None,
    resolved_randomization: Optional[Dict[str, Any]] = None,
) -> List[ET.Element]:
    """Create homogeneous HDV compliance variants and CAV counterparts."""
    if car_following_model is not None:
        car_following_model_hdv = car_following_model_cav = car_following_model

    resolved = resolved_randomization or _resolve_vehicle_randomization(randomization_cfg)

    base_specs = resolved["base_specs"]
    compliance_groups = resolved["compliance_groups"]
    cav_cfg = resolved["cav_cfg"]
    tau_mid = sum(resolved["tau_range"]) / 2.0

    cav_accel_mult = cav_cfg.get("accel", 1.1)
    cav_decel_mult = cav_cfg.get("decel", 1.05)
    cav_min_gap_scale = cav_cfg.get("min_gap_scale", 0.5)
    cav_speed_factor = cav_cfg.get("speed_factor", 1.0)
    cav_speed_dev = cav_cfg.get("speed_dev", 0.0)
    cav_sigma = cav_cfg.get("sigma", 0.0)
    cav_tau = cav_cfg.get("tau", 1.0)
    cav_max_speed_multiplier = cav_cfg.get("max_speed_multiplier", 1.0)

    vehicle_types: List[ET.Element] = []

    for vtype_name, specs in base_specs.items():
        accel_mean = sum(specs["accel_range"]) / 2.0
        decel_mean = sum(specs["decel_range"]) / 2.0
        max_speed_mean = sum(specs["max_speed_range"]) / 2.0
        min_gap = float(specs["min_gap"])
        length = float(specs["length"])
        vclass = str(specs["vClass"])
        color = str(specs["color"])

        for group in compliance_groups:
            hdv_elem = ET.Element(
                "vType",
                carFollowModel=car_following_model_hdv,
                id=f"{group['id_prefix']}_{vtype_name}",
                vClass=vclass,
                color=color,
                length=f"{length:.2f}",
            )
            hdv_elem.set("accel", f"{accel_mean:.2f}")
            hdv_elem.set("decel", f"{decel_mean:.2f}")
            hdv_elem.set("maxSpeed", f"{max_speed_mean * group['max_speed_multiplier']:.2f}")
            hdv_elem.set("sigma", f"{group['sigma']:.2f}")
            hdv_elem.set("minGap", f"{min_gap:.2f}")
            hdv_elem.set("tau", f"{tau_mid:.2f}")
            hdv_elem.set("actionStepLength", f"{sim_step_length:.2f}")
            hdv_elem.set("speedFactor", f"{group['speed_factor']:.2f}")
            hdv_elem.set("speedDev", f"{group['speed_dev']:.2f}")
            vehicle_types.append(hdv_elem)

        cav_elem = ET.Element(
            "vType",
            carFollowModel=car_following_model_cav,
            id=f"CAV_{vtype_name}",
            vClass=vclass,
            color="0,1,0",
            length=f"{length:.2f}",
        )
        cav_elem.set("accel", f"{accel_mean * cav_accel_mult:.2f}")
        cav_elem.set("decel", f"{decel_mean * cav_decel_mult:.2f}")
        cav_elem.set("maxSpeed", f"{max_speed_mean * cav_max_speed_multiplier:.2f}")
        cav_elem.set("sigma", f"{cav_sigma:.2f}")
        cav_elem.set("minGap", f"{min_gap * cav_min_gap_scale:.2f}")
        cav_elem.set("tau", f"{cav_tau:.2f}")
        cav_elem.set("actionStepLength", f"{sim_step_length:.2f}")
        cav_elem.set("speedFactor", f"{cav_speed_factor:.2f}")
        cav_elem.set("speedDev", f"{cav_speed_dev:.2f}")
        vehicle_types.append(cav_elem)

    return vehicle_types



def flow_generation_single_file(
    file_name: str,
    hourly_demand: Optional[List[int]],
    episode_duration: int,
    cav_percent: float = 0.0,
    network_topology: str = "merge_4_to_3_v0",
    output_dir: Optional[str] = None,
    use_homogeneous_fleet: Optional[bool] = None,
    sim_step_length: float = 1.0,
    car_following_model_hdv: str = "Krauss",
    car_following_model_cav: str = "Krauss",
    car_following_model: Optional[str] = None,
    counts: Optional[List[int]] = None,
    bin_seconds: int = 3600,
    vehicle_type_proportions: Optional[Dict[str, float]] = None,
    vehicle_randomization: Optional[Dict[str, Any]] = None,
    weather: Optional[Dict[str, Any]] = None,
    use_homogeneous_hdv_fleet: Optional[bool] = None,
    use_homogeneous_cav_fleet: Optional[bool] = None,
) -> str:
    """Generate a SUMO route file for a single episode."""
    if car_following_model is not None:
        car_following_model_hdv = car_following_model_cav = car_following_model
    if not 0 <= cav_percent <= 100:
        raise ValueError(f"cav_percent must be between 0 and 100, got {cav_percent}")

    output_dir = output_dir or os.path.join(
        "traffic_environment", "sumo", "generated_flows"
    )
    os.makedirs(output_dir, exist_ok=True)

    network_topology = _normalize_network_topology(network_topology)

    route_defs: Dict[str, str] = {}
    try:
        with NETWORK_CONFIG_FILE_4_TO_3.open("r", encoding="utf-8") as cfg_file:
            network_config = yaml.safe_load(cfg_file)
        segment_ids = list(network_config["segments"].keys())
        route_defs["route_1"] = " ".join(segment_ids)
    except Exception as exc:
        raise RuntimeError(
            f"Could not read or parse network config at {NETWORK_CONFIG_FILE_4_TO_3}: {exc}"
        ) from exc

    episode_hours = episode_duration // 3600
    logger.debug(
        "Generating flow file for %s (%sh) with %.1f%% CAVs",
        file_name,
        episode_hours,
        cav_percent,
    )

    resolved_randomization = _resolve_vehicle_randomization(vehicle_randomization)
    resolved_randomization = _apply_weather_to_randomization(resolved_randomization, weather)
    base_specs = resolved_randomization["base_specs"]
    compliance_groups = resolved_randomization["compliance_groups"]
    compliance_lookup = resolved_randomization["compliance_lookup"]
    generated_variants = max(1, resolved_randomization["generated_variants"])
    homogeneous_hdv = use_homogeneous_hdv_fleet
    homogeneous_cav = use_homogeneous_cav_fleet
    if use_homogeneous_fleet is not None:
        homogeneous_hdv = homogeneous_cav = bool(use_homogeneous_fleet)
    if homogeneous_hdv is None:
        homogeneous_hdv = False
    if homogeneous_cav is None:
        homogeneous_cav = False

    variant_pick_upper_base = max(1, resolved_randomization["variant_pick_upper"])
    hdv_variants = 1 if homogeneous_hdv else generated_variants
    cav_variants = 1 if homogeneous_cav else generated_variants
    variant_pick_upper_hdv = max(1, min(variant_pick_upper_base, hdv_variants))
    variant_pick_upper_cav = max(1, min(variant_pick_upper_base, cav_variants))
    passenger_heavy_chance = resolved_randomization["passenger_heavy_chance"]
    uniform_variation_pct = resolved_randomization["uniform_variation_pct"]
    heavy_scalars = resolved_randomization["heavy_scalars"]
    compliance_distribution_cfg = resolved_randomization["compliance_distribution"]

    default_base_proportions = {
        "passenger": 0.60,
        "passenger_van": 0.20,
        "bus": 0.05,
        "truck": 0.10,
        "truck_trailer": 0.05,
    }
    type_order = list(default_base_proportions.keys())
    for base in base_specs.keys():
        if base not in type_order:
            type_order.append(base)

    base_proportions = {
        base: float(default_base_proportions.get(base, 0.05)) for base in type_order
    }
    if vehicle_type_proportions:
        vehicle_type_proportions = _to_plain(vehicle_type_proportions)
        for vtype, value in vehicle_type_proportions.items():
            try:
                base_proportions[vtype] = max(float(value), 0.0)
                if vtype not in type_order:
                    type_order.append(vtype)
            except (TypeError, ValueError):
                logger.warning("Ignoring invalid vehicle proportion for %s: %s", vtype, value)

    routes = ET.Element("routes")
    routes.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    routes.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")

    if homogeneous_hdv and homogeneous_cav:
        routes.extend(
            create_homogeneous_vehicle_types(
                car_following_model_hdv=car_following_model_hdv,
                car_following_model_cav=car_following_model_cav,
                car_following_model=car_following_model,
                sim_step_length=sim_step_length,
                randomization_cfg=vehicle_randomization,
                resolved_randomization=resolved_randomization,
            )
        )
        vehicle_proportions = {base: 0.0 for base in type_order}
        vehicle_proportions["passenger"] = 1.0
        variant_pick_upper_hdv = variant_pick_upper_cav = 1
    else:
        routes.extend(
            create_vehicle_types_with_variants(
                num_variants=generated_variants,
                num_variants_hdv=hdv_variants,
                num_variants_cav=cav_variants,
                car_following_model_hdv=car_following_model_hdv,
                car_following_model_cav=car_following_model_cav,
                car_following_model=car_following_model,
                sim_step_length=sim_step_length,
                randomization_cfg=vehicle_randomization,
                resolved_randomization=resolved_randomization,
            )
        )
        passenger_heavy = passenger_heavy_chance > 0.0 and np.random.random() < passenger_heavy_chance
        if passenger_heavy:
            varied = {
                base: base_proportions.get(base, 0.0) * heavy_scalars.get(base, 1.0)
                for base in type_order
            }
            logger.debug("Generating passenger-heavy traffic scenario")
        else:
            variation = max(0.0, uniform_variation_pct)
            varied = {
                base: base_proportions.get(base, 0.0)
                * (1 + np.random.uniform(-variation, variation))
                for base in type_order
            }
        varied = {base: max(0.0, value) for base, value in varied.items()}
        total_prop = sum(varied.values())
        if total_prop <= 0:
            varied = {base: base_proportions.get(base, 0.0) for base in type_order}
            total_prop = sum(varied.values()) or 1.0
        vehicle_proportions = {
            base: varied.get(base, 0.0) / total_prop for base in type_order
        }

    def _normalized(values: Dict[str, float]) -> Dict[str, float]:
        total = sum(values.values())
        if total <= 0:
            size = max(1, len(values))
            return {key: 1.0 / size for key in values}
        return {key: values[key] / total for key in values}

    default_compliance_shares = {
        group["name"]: float(group.get("share", 1.0)) for group in compliance_groups
    }

    def _distribution_for(base: str) -> Dict[str, float]:
        base_cfg = compliance_distribution_cfg.get(base)
        if base_cfg is None:
            base_cfg = compliance_distribution_cfg.get("default")
        if base_cfg:
            raw = {name: float(base_cfg.get(name, 0.0)) for name in compliance_lookup}
        else:
            raw = default_compliance_shares.copy()
        return _normalized(raw)

    type_order = list(vehicle_proportions.keys())
    compliance_probabilities = {base: _distribution_for(base) for base in type_order}

    for route_id, edges_str in route_defs.items():
        ET.SubElement(routes, "route", id=route_id, edges=edges_str)

    if counts is not None:
        per_bin = [int(c) for c in counts]
    else:
        if hourly_demand is None:
            raise ValueError("Either 'counts' or 'hourly_demand' must be provided")
        per_bin = [int(c) for c in hourly_demand]
        bin_seconds = 3600

    veh_id = 0
    total_bins = len(per_bin)
    fallback_group = compliance_groups[0] if compliance_groups else {"id_prefix": "HDV", "sigma": 0.2, "speed_factor": 1.0, "speed_dev": 0.0, "max_speed_multiplier": 1.0}

    for bin_index, count in enumerate(per_bin):
        if count <= 0:
            continue
        t0 = float(bin_index) * float(bin_seconds)
        step = float(bin_seconds) / float(max(count, 1))
        for i in range(count):
            depart_time = t0 + (i + 0.5) * step
            if depart_time > float(episode_duration):
                break

            base_weights = np.array([vehicle_proportions.get(base, 0.0) for base in type_order], dtype=float)
            if base_weights.sum() <= 0:
                base_weights = np.full(len(type_order), 1.0 / max(1, len(type_order)))
            else:
                base_weights = base_weights / base_weights.sum()
            base_class = np.random.choice(type_order, p=base_weights)

            comp_probs = compliance_probabilities.get(base_class, {})
            group_names = list(comp_probs.keys())
            if not group_names:
                group_cfg = fallback_group
            else:
                weights = np.array([comp_probs[name] for name in group_names], dtype=float)
                if weights.sum() <= 0:
                    weights = np.full(len(group_names), 1.0 / len(group_names))
                else:
                    weights = weights / weights.sum()
                selected_group = np.random.choice(group_names, p=weights)
                group_cfg = compliance_lookup.get(selected_group, fallback_group)

            is_cav = (np.random.random() * 100.0) < cav_percent
            if is_cav:
                variant_idx = 0 if homogeneous_cav else np.random.randint(0, variant_pick_upper_cav)
            else:
                variant_idx = 0 if homogeneous_hdv else np.random.randint(0, variant_pick_upper_hdv)

            if is_cav:
                veh_type = (
                    f"CAV_{base_class}"
                    if homogeneous_cav
                    else f"CAV_{base_class}_v{variant_idx}"
                )
            else:
                veh_type = (
                    f"{group_cfg['id_prefix']}_{base_class}"
                    if homogeneous_hdv
                    else f"{group_cfg['id_prefix']}_{base_class}_v{variant_idx}"
                )

            route_id = "route_1"

            ET.SubElement(
                routes,
                "vehicle",
                id=f"veh_{veh_id}",
                type=veh_type,
                route=route_id,
                depart=f"{depart_time:.2f}",
                departPos="last",
                departLane="best",
                departSpeed="desired",
                insertionChecks="none",
            )
            veh_id += 1

    output_path = os.path.join(output_dir, f"{file_name}.rou.xml")
    write_file_atomic(prettify_xml(routes), output_path)
    logger.debug("Generated flow file at %s with %d vehicles", output_path, veh_id)
    return output_path
