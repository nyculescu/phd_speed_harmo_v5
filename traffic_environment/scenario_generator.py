# traffic_environment/scenario_generator.py
"""Scenario generation utilities for SUMO-based training/evaluation."""

from __future__ import annotations

import logging
import multiprocessing as mp
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
try:
    from tqdm import tqdm  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    def tqdm(iterable=None, *args, **kwargs):  # type: ignore[no-redef]
        return iterable if iterable is not None else []

from .demand_profiles import make_counts_from_profile
from .rou_writer import flow_generation_single_file

logger = logging.getLogger(__name__)

SUMO_DIR = Path(__file__).resolve().parent / "sumo"
GUI_SETTINGS_FILENAME = "colored.view.xml"

_TOPOLOGY_FILES: Dict[str, Dict[str, str]] = {
    "merge_4_to_3_v0": {
        "net": "4_3_merge.net.xml",
        "detectors": "loops_detectors_m43_v0.add.xml",
    },
}

_TOPOLOGY_POSTFIX: Dict[str, str] = {
    "merge_4_to_3_v0": "_m43v0",
}


def _normalize_network_topology(value: Any) -> str:
    if value in (None, "", False):
        return "merge_4_to_3_v0"
    raw = str(value).strip().lower()
    cleaned = raw.replace("-", "_")
    if cleaned in {"merge_4_to_3_v0", "m43v0", "merge43v0", "merge_4_to_3", "merge43", "m43"}:
        return "merge_4_to_3_v0"
    return cleaned


def _resolve_topology_files(network_topology: Any) -> Tuple[str, str]:
    topology = _normalize_network_topology(network_topology)
    files = _TOPOLOGY_FILES.get(topology)
    if not files:
        supported = ", ".join(sorted(_TOPOLOGY_FILES.keys()))
        raise ValueError(f"Unknown network_topology={network_topology!r}. Supported: {supported}")
    return files["net"], files["detectors"]


def _resolve_topology_postfix(network_topology: Any) -> str:
    topology = _normalize_network_topology(network_topology)
    postfix = _TOPOLOGY_POSTFIX.get(topology)
    if postfix is None:
        supported = ", ".join(sorted(_TOPOLOGY_POSTFIX.keys()))
        raise ValueError(f"Unknown network_topology={network_topology!r}. Supported: {supported}")
    return postfix


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


_PREFIX_SLUG_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _curriculum_label(level_name: Optional[str]) -> str:
    if level_name in (None, "", False):
        return "NA"
    name = str(level_name)
    match = re.search(r"(\d+)(?!.*\d)", name)
    if match:
        return match.group(1)
    slug = _PREFIX_SLUG_RE.sub("-", name.strip()).strip("-")
    return slug or "NA"


def compose_scenario_prefix(base_prefix: str, level_name: Optional[str]) -> str:
    label = _curriculum_label(level_name)
    return f"{base_prefix}_CL-{label}"


def _normalize_obedience_level(value: Any) -> Optional[float]:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        return None
    if 0.0 <= raw <= 1.0:
        raw *= 100.0
    return max(0.0, min(100.0, raw))


def _format_percent_label(value: Optional[float]) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.1f}"


_DEFAULT_WEATHER_PROFILES: Dict[str, Dict[str, float]] = {
    "clear": {"visibility": 0.0, "slippery": 0.0, "wind": 0.0},
    "fog": {"visibility": 0.4, "slippery": 0.0, "wind": 0.0},
    "smoke": {"visibility": 0.3, "slippery": 0.0, "wind": 0.0},
    "rain": {"visibility": 0.2, "slippery": 0.35, "wind": 0.05},
    "heavy_rain": {"visibility": 0.5, "slippery": 0.45, "wind": 0.10},
    "snow": {"visibility": 0.5, "slippery": 0.55, "wind": 0.10},
    "ice": {"visibility": 0.1, "slippery": 0.55, "wind": 0.0},
    "black_ice": {"visibility": 0.0, "slippery": 0.60, "wind": 0.0},
    "wind": {"visibility": 0.0, "slippery": 0.0, "wind": 0.4},
}
_DEFAULT_WEATHER_WEIGHTS: Dict[str, float] = {
    "clear": 0.35,
    "fog": 0.1,
    "smoke": 0.05,
    "rain": 0.15,
    "heavy_rain": 0.05,
    "snow": 0.05,
    "ice": 0.05,
    "black_ice": 0.05,
    "wind": 0.1,
}
_DEFAULT_WEATHER_MAX_EFFECT = 0.6


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _resolve_weather_cfg(weather_cfg: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = _to_plain(weather_cfg or {})
    enabled = bool(cfg.get("enabled", False))
    sampling = str(cfg.get("sampling", "weighted")).strip().lower() or "weighted"
    fixed_type = cfg.get("fixed_type") or cfg.get("fixedType")
    default_type = str(cfg.get("default_type", "clear") or "clear")
    max_effect = _safe_float(cfg.get("max_effect", _DEFAULT_WEATHER_MAX_EFFECT), _DEFAULT_WEATHER_MAX_EFFECT)
    profiles = _deep_merge_dicts(_DEFAULT_WEATHER_PROFILES, _to_plain(cfg.get("profiles") or {}))
    weights = dict(_DEFAULT_WEATHER_WEIGHTS)
    weights.update(_to_plain(cfg.get("weights") or {}))
    return {
        "enabled": enabled,
        "sampling": sampling,
        "fixed_type": fixed_type,
        "default_type": default_type,
        "max_effect": max_effect,
        "profiles": profiles,
        "weights": weights,
    }


def _clip_weather_effects(vis: float, slip: float, wind: float, max_effect: float) -> Tuple[float, float, float]:
    cap = max(0.0, float(max_effect))
    return (
        float(np.clip(vis, 0.0, cap)),
        float(np.clip(slip, 0.0, cap)),
        float(np.clip(wind, 0.0, cap)),
    )


def _compute_weather_multipliers(vis: float, slip: float, wind: float) -> Dict[str, Dict[str, float]]:
    def _clamp(value: float, lo: float, hi: float) -> float:
        return float(np.clip(value, lo, hi))

    hdv = {
        "speed_factor": _clamp(1.0 - (0.15 * vis + 0.08 * slip + 0.05 * wind), 0.83, 1.0),
        "speed_dev": _clamp(1.0 + (0.15 * vis + 0.10 * slip + 0.30 * wind), 1.0, 1.40),
        "tau": _clamp(1.0 + (0.25 * vis + 0.30 * slip + 0.10 * wind), 1.0, 1.40),
        "min_gap": _clamp(1.0 + (0.12 * vis + 0.18 * slip + 0.08 * wind), 1.0, 1.25),
        "accel": _clamp(1.0 - (0.20 * slip + 0.05 * wind), 0.85, 1.0),
        "decel": _clamp(1.0 - (0.25 * slip + 0.05 * wind), 0.80, 1.0),
        "sigma": _clamp(1.0 + (0.20 * vis + 0.10 * slip + 0.25 * wind), 1.0, 1.40),
    }
    cav = {
        "speed_factor": _clamp(1.0 - (0.08 * vis + 0.05 * slip + 0.03 * wind), 0.90, 1.0),
        "speed_dev": _clamp(1.0 + (0.08 * vis + 0.05 * slip + 0.15 * wind), 1.0, 1.20),
        "tau": _clamp(1.0 + (0.12 * vis + 0.18 * slip + 0.05 * wind), 1.0, 1.30),
        "min_gap": _clamp(1.0 + (0.08 * vis + 0.12 * slip + 0.04 * wind), 1.0, 1.20),
        "accel": _clamp(1.0 - (0.12 * slip + 0.03 * wind), 0.88, 1.0),
        "decel": _clamp(1.0 - (0.15 * slip + 0.03 * wind), 0.85, 1.0),
        "sigma": _clamp(1.0 + (0.10 * vis + 0.05 * slip + 0.15 * wind), 1.0, 1.20),
    }
    return {"hdv": hdv, "cav": cav}


def _choose_weather_type(cfg: Dict[str, Any], rng: np.random.Generator) -> str:
    if not cfg.get("enabled"):
        return cfg.get("default_type", "clear")
    fixed = cfg.get("fixed_type")
    if fixed:
        return str(fixed)
    profiles = cfg.get("profiles") or {}
    weights = cfg.get("weights") or {}
    candidates = [key for key in weights.keys() if key in profiles]
    if not candidates:
        candidates = list(profiles.keys())
    if not candidates:
        return cfg.get("default_type", "clear")
    sampling = str(cfg.get("sampling", "weighted")).strip().lower()
    if sampling == "uniform":
        return str(rng.choice(candidates))
    weight_arr = np.asarray([_safe_float(weights.get(key, 1.0), 1.0) for key in candidates], dtype=float)
    if not np.isfinite(weight_arr).all() or np.all(weight_arr <= 0.0):
        weight_arr = np.ones(len(candidates), dtype=float)
    weight_arr = weight_arr / weight_arr.sum()
    return str(rng.choice(candidates, p=weight_arr))


def _resolve_weather_for_scenario(weather_cfg: Optional[Dict[str, Any]], seed: Optional[int]) -> Dict[str, Any]:
    cfg = _resolve_weather_cfg(weather_cfg)
    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    weather_type = _choose_weather_type(cfg, rng)
    profiles = cfg.get("profiles") or {}
    profile = profiles.get(weather_type) or profiles.get(cfg.get("default_type", "clear"), {}) or {}
    vis = _safe_float(profile.get("visibility", profile.get("vis", 0.0)))
    slip = _safe_float(profile.get("slippery", profile.get("slip", 0.0)))
    wind = _safe_float(profile.get("wind", 0.0))
    vis, slip, wind = _clip_weather_effects(vis, slip, wind, cfg.get("max_effect", _DEFAULT_WEATHER_MAX_EFFECT))
    multipliers = _compute_weather_multipliers(vis, slip, wind)
    return {
        "type": str(weather_type),
        "visibility": vis,
        "slippery": slip,
        "wind": wind,
        "multipliers": multipliers,
    }


def _normalize_curriculum_levels(
    levels_raw: Any,
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    levels: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    if isinstance(levels_raw, dict):
        for key, value in levels_raw.items():
            name = str(key)
            levels[name] = _to_plain(value) if isinstance(value, dict) else {}
            order.append(name)
    elif isinstance(levels_raw, list):
        for idx, entry in enumerate(levels_raw):
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or f"level_{idx}"
            name = str(name)
            levels[name] = _to_plain(entry)
            order.append(name)
    return levels, order


def _select_curriculum_level(
    curriculum_cfg: Dict[str, Any],
    levels: Dict[str, Dict[str, Any]],
    order: List[str],
    *,
    mode: str,
) -> Optional[str]:
    if not levels:
        return None
    enabled = curriculum_cfg.get("enabled")
    if isinstance(enabled, bool) and not enabled:
        return None
    if mode == "eval":
        level_key = curriculum_cfg.get("eval_level") or curriculum_cfg.get("evaluation_level")
    else:
        level_key = curriculum_cfg.get("active_level") or curriculum_cfg.get("train_level")
    if level_key in (None, "", False):
        level_key = curriculum_cfg.get("level") or curriculum_cfg.get("current_level")
    if level_key in (None, "", False):
        return None
    if isinstance(level_key, (int, float)) or (isinstance(level_key, str) and level_key.isdigit()):
        idx = int(level_key)
        if 0 <= idx < len(order):
            return order[idx]
        candidate = f"curr_learn_level_{idx}"
        return candidate if candidate in levels else None
    level_name = str(level_key)
    if level_name in levels:
        return level_name
    lower_lookup = {name.lower(): name for name in levels}
    return lower_lookup.get(level_name.lower())


def resolve_curriculum_settings(
    scenario_cfg: Optional[Dict[str, Any]],
    *,
    mode: str = "train",
) -> Dict[str, Any]:
    scenario_cfg = _to_plain(scenario_cfg or {})
    curriculum_cfg = _to_plain(scenario_cfg.get("curriculum") or {})
    levels, order = _normalize_curriculum_levels(curriculum_cfg.get("levels") or {})
    level_name = _select_curriculum_level(curriculum_cfg, levels, order, mode=mode)
    level_cfg = _to_plain(levels.get(level_name) or {})

    base_demand_profile = _to_plain(
        scenario_cfg.get("demand_profile") or scenario_cfg.get("demand_shape_params") or {}
    )
    demand_profile = _deep_merge_dicts(
        base_demand_profile,
        _to_plain(level_cfg.get("demand_profile_overrides") or level_cfg.get("demand_profile") or {}),
    )
    if "demand_noise_randomness" in level_cfg:
        try:
            demand_profile["noise_randomness"] = float(level_cfg["demand_noise_randomness"])
        except (TypeError, ValueError):
            pass
    elif "noise_randomness" in level_cfg:
        try:
            demand_profile["noise_randomness"] = float(level_cfg["noise_randomness"])
        except (TypeError, ValueError):
            pass
    if "demand_shape_randomness" in level_cfg:
        try:
            demand_profile["shape_randomness"] = float(level_cfg["demand_shape_randomness"])
        except (TypeError, ValueError):
            pass
    elif "shape_randomness" in level_cfg:
        try:
            demand_profile["shape_randomness"] = float(level_cfg["shape_randomness"])
        except (TypeError, ValueError):
            pass

    if mode == "eval":
        eval_overrides = _to_plain(
            scenario_cfg.get("eval_demand_profile_overrides")
            or scenario_cfg.get("evaluation_demand_profile_overrides")
            or {}
        )
        if eval_overrides:
            demand_profile = _deep_merge_dicts(demand_profile, eval_overrides)

    vehicle_randomization = _deep_merge_dicts(
        _to_plain(scenario_cfg.get("vehicle_randomization") or {}),
        _to_plain(
            level_cfg.get("vehicle_randomization_overrides")
            or level_cfg.get("vehicle_randomization")
            or {}
        ),
    )
    if not vehicle_randomization:
        vehicle_randomization = None

    vehicle_type_proportions = _deep_merge_dicts(
        _to_plain(scenario_cfg.get("vehicle_type_proportions") or {}),
        _to_plain(
            level_cfg.get("vehicle_type_proportions_overrides")
            or level_cfg.get("vehicle_type_proportions")
            or {}
        ),
    )
    if not vehicle_type_proportions:
        vehicle_type_proportions = None

    obedience_level = level_cfg.get("obedience_level_HDV", scenario_cfg.get("obedience_level_HDV"))

    return {
        "level_name": level_name,
        "demand_profile": demand_profile,
        "vehicle_randomization": vehicle_randomization,
        "vehicle_type_proportions": vehicle_type_proportions,
        "obedience_level_HDV": obedience_level,
    }


def _delete_quiet(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


def _coerce_positive_int(value: Any) -> Optional[int]:
    try:
        val = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    return val if val > 0 else None


def _resolve_demand_bounds(
    min_value: Any,
    max_value: Any,
    *,
    default_vph: int = 2000,
) -> Tuple[int, int]:
    min_vph = _coerce_positive_int(min_value)
    max_vph = _coerce_positive_int(max_value)

    if min_vph is None and max_vph is None:
        return int(default_vph), int(default_vph)
    if min_vph is None:
        min_vph = max_vph
    if max_vph is None:
        max_vph = min_vph
    if min_vph > max_vph:
        min_vph, max_vph = max_vph, min_vph
    return int(min_vph), int(max_vph)




def _measure_departure_backlog(
    cfg_path: Path,
    *,
    sumo_binary: str = "sumo",
    step_length: float = 1.0,
    horizon_s: Optional[int] = None,
    cap_veh: Optional[int] = None,
    extra_sumo_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Measure "insertion backlog" (vehicles loaded for departure but not yet inserted).

    Uses TraCI counters:
      - loaded_total := Σ getLoadedNumber()
      - departed_total := Σ getDepartedNumber()
      - backlog_now := loaded_total - departed_total

    If cap_veh is provided, the run may early-exit once backlog exceeds the cap.
    """
    try:
        import traci  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Departure backlog validation requires TraCI (python module 'traci') to be installed."
        ) from exc

    cmd = [
        str(sumo_binary),
        "-c",
        str(cfg_path),
        "--start",
        "--quit-on-end",
        "--step-length",
        str(float(step_length)),
    ]
    if extra_sumo_args:
        cmd.extend(list(extra_sumo_args))

    loaded_total = 0
    departed_total = 0
    backlog_max = 0
    backlog_end = 0

    traci.start(cmd)
    try:
        if horizon_s is None:
            end_time = float(traci.simulation.getEndTime())
            horizon = None if end_time < 0 else float(end_time)
        else:
            horizon = float(horizon_s)

        while True:
            traci.simulationStep()
            t = float(traci.simulation.getTime())
            loaded_total += int(traci.simulation.getLoadedNumber())
            departed_total += int(traci.simulation.getDepartedNumber())
            backlog_end = int(loaded_total - departed_total)
            backlog_max = max(backlog_max, backlog_end)

            if cap_veh is not None and backlog_max > int(cap_veh):
                break
            if horizon is not None and t + 1e-9 >= horizon:
                break
    finally:
        try:
            traci.close(False)
        except Exception:
            pass

    return {
        "loaded_total": int(loaded_total),
        "departed_total": int(departed_total),
        "backlog_end_veh": int(backlog_end),
        "backlog_max_veh": int(backlog_max),
    }


def _generate_single_scenario_pair_worker(args: Dict[str, Any]) -> bool:
    """Generate one `.rou.xml`/`.sumocfg` pair on a worker process."""
    index = int(args["index"])
    prefix: str = args["prefix"]
    network_topology = args.get("network_topology", "merge_3_to_2")
    cfg_output_dir = Path(args["cfg_output_dir"])
    rou_output_dir = Path(args["rou_output_dir"])
    episode_duration = int(args["episode_duration"])
    cav_percentage = float(args["cav_percentage"])

    pattern = args.get("pattern", "nonmonotonic_transient")
    # Demand contract: demand levels are specified as an average inflow rate (veh/hour),
    # converted to a per-episode vehicle count based on the episode duration.
    raw_demand_vph = args.get("demand_vph", args.get("demand_total", 2000))
    try:
        demand_vph = float(raw_demand_vph)
    except (TypeError, ValueError):
        demand_vph = 2000.0
    demand_vph_int = int(round(demand_vph))
    bin_seconds = int(args.get("bin_seconds", 150))
    vehicle_type_proportions = _to_plain(args.get("vehicle_type_proportions"))
    vehicle_randomization = _to_plain(args.get("vehicle_randomization"))
    demand_profile = _to_plain(args.get("demand_profile") or {})
    if not demand_profile:
        demand_profile = _to_plain(args.get("demand_shape_params") or {})
    departure_backlog_cap_veh = args.get("departure_backlog_cap_veh")
    if departure_backlog_cap_veh in (None, "", False):
        departure_backlog_cap_veh = None
    else:
        departure_backlog_cap_veh = int(departure_backlog_cap_veh)

    validation_horizon_s = args.get("validation_horizon_s")
    if validation_horizon_s in (None, "", False):
        validation_horizon_s = None
    else:
        validation_horizon_s = int(validation_horizon_s)

    sumo_binary_for_validation = str(args.get("sumo_binary_for_validation") or "sumo")
    sumo_validation_extra_args = args.get("sumo_validation_extra_args") or []
    if not isinstance(sumo_validation_extra_args, list):
        sumo_validation_extra_args = []

    validation_max_attempts = args.get("validation_max_attempts")
    if validation_max_attempts in (None, "", False):
        validation_max_attempts = 1
    validation_max_attempts = max(1, int(validation_max_attempts))

    sim_step_length = float(args.get("sim_step_length", args.get("step_length", 1.0)))

    obedience_raw = args.get("obedience_level_hdv")
    obedience_pct = _normalize_obedience_level(obedience_raw)
    obedience_label = _format_percent_label(obedience_pct)
    cav_label = _format_percent_label(cav_percentage)

    topology_postfix = _resolve_topology_postfix(network_topology)
    base_name = (
        f"{prefix}_D-{demand_vph_int}_CAV-{cav_label}_"
        f"HDVob-{obedience_label}_TT-{episode_duration}_{index:03d}{topology_postfix}"
    )

    seed_base = f"{prefix}_{pattern}_{demand_vph_int}_{episode_duration}_{cav_percentage}_{index}"
    weather_seed = hash(f"{seed_base}_weather") % (2**31)
    weather = _resolve_weather_for_scenario(args.get("weather"), weather_seed)
    weather_type = weather.get("type", "clear")
    weather_vis = float(weather.get("visibility", 0.0))
    weather_slip = float(weather.get("slippery", 0.0))
    weather_wind = float(weather.get("wind", 0.0))

    legacy_car_follow = args.get("car_following_model", "Krauss")
    car_follow_hdv = args.get("car_following_model_hdv") or legacy_car_follow
    car_follow_cav = args.get("car_following_model_cav") or legacy_car_follow
    homogeneous_hdv = bool(args.get("use_homogeneous_hdv_fleet", args.get("use_homogeneous_fleet", False)))
    homogeneous_cav = bool(args.get("use_homogeneous_cav_fleet", args.get("use_homogeneous_fleet", False)))

    cfg_output_dir.mkdir(parents=True, exist_ok=True)

    # Hard validation: reject scenarios whose insertion backlog exceeds the cap.
    for attempt in range(validation_max_attempts):
        # Convert average rate to per-episode count (integer, exact sum enforced by allocator).
        total_vehicles = max(0, int(round(demand_vph * (episode_duration / 3600.0))))

        # Include duration and attempt so retries can explore a new realization.
        seed_key = seed_base if attempt == 0 else f"{seed_base}_retry{attempt}"
        seed = hash(seed_key) % (2**31)
        counts = make_counts_from_profile(
            total_vehicles=total_vehicles,
            episode_duration_s=episode_duration,
            bin_seconds=bin_seconds,
            pattern=pattern,
            demand_profile=demand_profile,
            seed=seed,
        )

        rou_path = flow_generation_single_file(
            file_name=base_name,
            hourly_demand=None,
            episode_duration=episode_duration,
            cav_percent=cav_percentage,
            network_topology=network_topology,
            output_dir=str(rou_output_dir),
            use_homogeneous_fleet=args.get("use_homogeneous_fleet", None),
            use_homogeneous_hdv_fleet=homogeneous_hdv,
            use_homogeneous_cav_fleet=homogeneous_cav,
            sim_step_length=sim_step_length,
            car_following_model_hdv=car_follow_hdv,
            car_following_model_cav=car_follow_cav,
            car_following_model=legacy_car_follow,
            counts=counts,
            bin_seconds=bin_seconds,
            vehicle_type_proportions=vehicle_type_proportions,
            vehicle_randomization=vehicle_randomization,
            weather=weather,
        )

        sumo_root = SUMO_DIR
        net_filename, detector_filename = _resolve_topology_files(network_topology)
        net_file_abs_path = (sumo_root / net_filename).resolve()
        detector_file_abs_path = (sumo_root / detector_filename).resolve()
        gui_settings_abs_path = (sumo_root / GUI_SETTINGS_FILENAME).resolve()
        route_file_abs_path = Path(rou_path).resolve()

        meta_comment = (
            f"<!-- scenario_meta pattern={pattern} demand_vph={demand_vph_int} "
            f"cav_percent={cav_label} hdv_obedience={obedience_label} "
            f"duration_s={episode_duration} topology={_normalize_network_topology(network_topology)} "
            f"weather={weather_type} "
            f"w_vis={weather_vis:.3f} w_slip={weather_slip:.3f} w_wind={weather_wind:.3f} -->"
        )
        config_template = f"""<?xml version="1.0" encoding="UTF-8"?>
{meta_comment}
<configuration>
    <input>
        <net-file value="{net_file_abs_path}"/>
        <route-files value="{route_file_abs_path}"/>
        <additional-files value="{detector_file_abs_path}"/>
        <gui-settings-file value="{gui_settings_abs_path}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{episode_duration}"/>
    </time>
</configuration>
"""
        cfg_path = cfg_output_dir / f"{base_name}.sumocfg"
        with cfg_path.open("w", encoding="utf-8") as cfg_file:
            cfg_file.write(config_template)

        if departure_backlog_cap_veh is None:
            return True

        metrics = _measure_departure_backlog(
            cfg_path,
            sumo_binary=sumo_binary_for_validation,
            step_length=sim_step_length,
            horizon_s=validation_horizon_s,
            cap_veh=departure_backlog_cap_veh,
            extra_sumo_args=sumo_validation_extra_args,
        )
        if int(metrics["backlog_max_veh"]) <= int(departure_backlog_cap_veh):
            return True

        _delete_quiet(Path(rou_path))
        _delete_quiet(cfg_path)

    raise RuntimeError(
        f"Scenario rejected by departure backlog cap after {validation_max_attempts} attempts: "
        f"pattern={pattern} demand_vph={demand_vph_int} cap={departure_backlog_cap_veh}"
    )


def generate_scenario_pairs_parallel(
    num_scenarios: int,
    rou_output_dir: str,
    cfg_output_dir: str,
    episode_duration: int,
    cav_percentage: float,
    network_topology: str = "merge_3_to_2",
    prefix: str = "train",
    pattern: Optional[str] = None,
    demand_levels: Optional[Iterable[int]] = None,
    use_homogeneous_fleet: bool = False,
    use_homogeneous_hdv_fleet: Optional[bool] = None,
    use_homogeneous_cav_fleet: Optional[bool] = None,
    car_following_model_hdv: str = "Krauss",
    car_following_model_cav: str = "Krauss",
    car_following_model: Optional[str] = None,
    sim_step_length: float = 1.0,
    bin_seconds: int = 150,
    vehicle_type_proportions: Optional[Dict[str, float]] = None,
    vehicle_randomization: Optional[Dict[str, Any]] = None,
    weather: Optional[Dict[str, Any]] = None,
    demand_profile: Optional[Dict[str, Any]] = None,
    obedience_level_hdv: Optional[Any] = None,
    demand_shape_params: Optional[Dict[str, Any]] = None,
    desc: str = "Generating scenarios",
    **kwargs: Any,
) -> None:
    """
    Generate scenario files across multiple worker processes.

    Demand contract: ``demand_levels`` values are interpreted as an average inflow
    rate in vehicles/hour (veh/h). The generator converts each demand value to a
    per-episode vehicle count using ``episode_duration``.
    """
    if car_following_model is not None:
        car_following_model_hdv = car_following_model_cav = car_following_model
    network_topology = _normalize_network_topology(network_topology)

    # Backwards-compatibility shim: some callers historically used `step_length=...`.
    if "step_length" in kwargs and kwargs["step_length"] is not None:
        try:
            sim_step_length = float(kwargs.pop("step_length"))
        except (TypeError, ValueError):
            kwargs.pop("step_length", None)

    if vehicle_type_proportions:
        vehicle_type_proportions = _to_plain(vehicle_type_proportions)
    if vehicle_randomization:
        vehicle_randomization = _to_plain(vehicle_randomization)
    if weather:
        weather = _to_plain(weather)
    if demand_profile:
        demand_profile = _to_plain(demand_profile)
    elif demand_shape_params:
        demand_profile = _to_plain(demand_shape_params)

    if pattern in (None, "", False):
        pattern = "nonmonotonic_transient"
    demand_levels = list(demand_levels) if demand_levels is not None else None
    dynamic_demand_enabled = (demand_levels is None) or (len(demand_levels) == 0)

    if dynamic_demand_enabled:
        min_vph, max_vph = _resolve_demand_bounds(
            kwargs.get("overall_min_demand_per_ep_per_hr"),
            kwargs.get("overall_max_demand_per_ep_per_hr"),
        )
        if min_vph == max_vph or num_scenarios <= 1:
            demand_by_index = [int(max_vph) for _ in range(num_scenarios)]
        else:
            grid = np.linspace(float(min_vph), float(max_vph), num_scenarios)
            demand_by_index = [int(round(float(x))) for x in grid]
    else:
        demand_by_index = [int(demand_levels[i % len(demand_levels)]) for i in range(num_scenarios)]

    tasks: List[Dict[str, Any]] = []
    pattern = str(pattern)
    for i in range(num_scenarios):
        demand = demand_by_index[i]
        tasks.append(
            {
                "index": i,
                "pattern": pattern,
                "demand_vph": demand,
                "rou_output_dir": rou_output_dir,
                "cfg_output_dir": cfg_output_dir,
                "episode_duration": episode_duration,
                "cav_percentage": cav_percentage,
                "prefix": prefix,
                "network_topology": network_topology,
                "use_homogeneous_fleet": use_homogeneous_fleet,
                "use_homogeneous_hdv_fleet": use_homogeneous_hdv_fleet,
                "use_homogeneous_cav_fleet": use_homogeneous_cav_fleet,
                "car_following_model_hdv": car_following_model_hdv,
                "car_following_model_cav": car_following_model_cav,
                "car_following_model": car_following_model,
                "sim_step_length": sim_step_length,
                "bin_seconds": bin_seconds,
                  "vehicle_type_proportions": vehicle_type_proportions,
                  "vehicle_randomization": vehicle_randomization,
                  "weather": weather,
                  "demand_profile": demand_profile,
                  "obedience_level_hdv": obedience_level_hdv,
                  **kwargs,
              }
          )

    Path(rou_output_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg_output_dir).mkdir(parents=True, exist_ok=True)

    num_workers = max(1, mp.cpu_count() - 2)
    if kwargs.get("departure_backlog_cap_veh") not in (None, "", False):
        max_workers = kwargs.get("validation_max_workers")
        if max_workers not in (None, "", False):
            num_workers = max(1, min(num_workers, int(max_workers)))
    try:
        with mp.Pool(processes=num_workers) as pool:
            results = list(
                tqdm(
                    pool.imap_unordered(_generate_single_scenario_pair_worker, tasks),
                    total=num_scenarios,
                    desc=desc,
                )
            )
    except (PermissionError, OSError) as exc:  # pragma: no cover
        logger.warning(
            "Parallel scenario generation unavailable (%s). Falling back to sequential generation.",
            exc,
        )
        results = [
            _generate_single_scenario_pair_worker(task)
            for task in tqdm(tasks, total=num_scenarios, desc=desc)
        ]
    if not all(bool(x) for x in results):
        bad = sum(1 for x in results if not bool(x))
        raise RuntimeError(f"Scenario generation failed for {bad}/{len(results)} tasks.")
