# traffic_environment/scenario_pool.py
"""
Pre-generated scenario pool + process-safe ScenarioManager.

Adapted from v4's ScenarioManager (drl_vsl.py:2400-2514) which ran
700+ parallel SUMO workers reliably with multiprocessing.Manager().

Two-phase usage:
  1. Pre-generation: call generate_scenario_pool() once before training.
     This creates N scenario pairs (.rou.xml + .sumocfg) on disk.
  2. Runtime: create ScenarioManager(pool_dir), pass to each TrafficEnv.
     Workers call get_next_scenario() atomically; queue auto-refills.
"""
from __future__ import annotations

import logging
import multiprocessing
import os
import queue
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

logger = logging.getLogger(__name__)


class ScenarioManager:
    """Lightweight scenario cycling for parallel SUMO workers.

    Each worker gets its own independent iterator over the scenario pool.
    Scenarios are shuffled per-cycle with a worker-specific seed to ensure
    diversity across workers without requiring inter-process communication.

    This design avoids multiprocessing.Manager() which cannot be created
    inside SubprocVecEnv daemon workers.
    """

    def __init__(
        self,
        pool_dir: str,
        prefix: str = "scenario",
        shuffle: bool = True,
        worker_seed: int = 0,
    ) -> None:
        pool_path = Path(pool_dir)
        if not pool_path.is_dir():
            raise FileNotFoundError(f"Scenario pool directory not found: {pool_dir}")

        # Scan for .sumocfg files
        cfgs = sorted(
            str(p.resolve())
            for p in pool_path.glob(f"{prefix}_*.sumocfg")
            if p.is_file()
        )
        if not cfgs:
            raise FileNotFoundError(
                f"No {prefix}_*.sumocfg files found in {pool_dir}"
            )

        self._scenarios: List[str] = list(cfgs)
        self._shuffle = shuffle
        self._rng = random.Random(worker_seed)
        self._idx = 0
        self._order: List[str] = []
        self._refill()

        logger.info(
            "ScenarioManager: loaded %d scenarios from %s (worker_seed=%d)",
            len(self._scenarios), pool_dir, worker_seed,
        )

    @property
    def n_scenarios(self) -> int:
        return len(self._scenarios)

    def get_next_scenario(self) -> str:
        """Get the next scenario .sumocfg path, cycling + reshuffling as needed."""
        if self._idx >= len(self._order):
            self._refill()
        path = self._order[self._idx]
        self._idx += 1
        return path

    def _refill(self) -> None:
        """Reshuffle and restart from the beginning."""
        self._order = list(self._scenarios)
        if self._shuffle:
            self._rng.shuffle(self._order)
        self._idx = 0


def generate_scenario_pool(
    output_dir: str,
    n_scenarios: int = 200,
    duration_s: int = 3600,
    bin_seconds: int = 30,
    cav_pct: float = 50.0,
    seed_offset: int = 0,
    n_workers: int = 1,
    demand_kwargs: Optional[Dict[str, Any]] = None,
    prefix: str = "scenario",
    weather_mix: Optional[Dict[str, float]] = None,
) -> List[str]:
    """Pre-generate scenario .rou.xml + .sumocfg pairs to disk.

    Args:
        output_dir: Directory to write files into (created if needed).
        n_scenarios: Number of scenario pairs to generate.
        duration_s: Episode duration in seconds.
        bin_seconds: Demand bin width.
        cav_pct: CAV penetration percentage (0-100).
        seed_offset: Base seed offset for reproducibility.
        n_workers: Parallel workers for generation (1=sequential).
        demand_kwargs: Extra kwargs passed to generate_demand_profile().
        prefix: Filename prefix for scenarios.

    Returns:
        List of .sumocfg file paths.
    """
    from traffic_environment.demand_profiles import generate_demand_profile

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    demand_kw = demand_kwargs or {}

    # Weather sampling: default 100% clear if not specified
    w_mix = weather_mix or {"clear": 1.0}
    w_names = list(w_mix.keys())
    w_weights = np.array([w_mix[w] for w in w_names], dtype=float)
    w_weights /= w_weights.sum()

    def _generate_one(idx: int) -> str:
        seed = seed_offset + idx
        rng = np.random.RandomState(seed)

        # Sample weather for this scenario
        weather = rng.choice(w_names, p=w_weights)

        profile = generate_demand_profile(
            duration_s=duration_s,
            bin_seconds=bin_seconds,
            seed=seed,
            weather=weather,
            **demand_kw,
        )

        # Write route file
        rou_name = (
            f"{prefix}_{idx:04d}_D{int(profile.peak_demand_vph)}"
            f"_R{profile.ramp_fraction:.0%}_{weather}_s{seed}"
        )
        rou_path = out_path / f"{rou_name}.rou.xml"
        cfg_path = out_path / f"{rou_name}.sumocfg"

        from tests._sumo_helpers import generate_sumocfg
        _write_route_file(rou_path, profile, cav_pct, seed, weather=weather)
        generate_sumocfg(cfg_path, rou_path, duration_s)

        return str(cfg_path)

    if n_workers <= 1:
        cfg_paths = []
        for i in range(n_scenarios):
            p = _generate_one(i)
            cfg_paths.append(p)
            if (i + 1) % 50 == 0 or i == n_scenarios - 1:
                logger.info("Generated %d/%d scenarios", i + 1, n_scenarios)
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        cfg_paths = [None] * n_scenarios
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            futures = {pool.submit(_generate_one, i): i for i in range(n_scenarios)}
            done = 0
            for future in as_completed(futures):
                idx = futures[future]
                cfg_paths[idx] = future.result()
                done += 1
                if done % 50 == 0 or done == n_scenarios:
                    logger.info("Generated %d/%d scenarios", done, n_scenarios)

    logger.info("Scenario pool: %d scenarios in %s", n_scenarios, output_dir)
    return [p for p in cfg_paths if p is not None]


def generate_focused_pool(
    output_dir: str,
    n_scenarios: int = 200,
    duration_s: int = 3600,
    bin_seconds: int = 30,
    cav_pct: float = 50.0,
    seed_offset: int = 0,
    demand_band: Tuple[float, float] = (5500.0, 7250.0),
    noise_std_vph: float = 200.0,
    ramp_fraction_range: Tuple[float, float] = (0.20, 0.30),
    prefix: str = "scenario",
    weather_mix: Optional[Dict[str, float]] = None,
) -> List[str]:
    """Generate scenarios with flat demand in a specific band + slight noise.

    This is the training-first mode: demand stays within the band where
    VSL actually makes a difference (from feasibility data). Each scenario
    samples a base demand uniformly from the band, then adds per-bin
    Gaussian noise (±noise_std_vph) for slight variability.

    Switch to generate_scenario_pool() with full Hermite profiles later
    for generalization testing.

    Args:
        output_dir: Output directory for scenario files.
        n_scenarios: Number of scenarios to generate.
        duration_s: Episode duration in seconds.
        bin_seconds: Bin width in seconds.
        cav_pct: CAV penetration (0-100).
        seed_offset: Base seed.
        demand_band: (min_vph, max_vph) — the trainable demand range.
        noise_std_vph: Gaussian noise std on top of the flat demand.
        ramp_fraction_range: (min, max) ramp fraction per scenario.
        prefix: Filename prefix.
        weather_mix: Dict of weather→probability, e.g. {"clear": 0.7, "rain": 0.3}.

    Returns:
        List of .sumocfg paths.
    """
    from traffic_environment.demand_profiles import DemandProfile, _largest_remainder

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    w_mix = weather_mix or {"clear": 1.0}
    w_names = list(w_mix.keys())
    w_weights = np.array([w_mix[w] for w in w_names], dtype=float)
    w_weights /= w_weights.sum()

    n_bins = max(1, duration_s // bin_seconds)
    cfg_paths = []

    for idx in range(n_scenarios):
        seed = seed_offset + idx
        rng = np.random.RandomState(seed)

        # Sample base demand uniformly from the band
        base_vph = rng.uniform(*demand_band)

        # Per-bin demand with slight noise
        bin_demands = np.clip(
            rng.normal(base_vph, noise_std_vph, size=n_bins),
            demand_band[0] * 0.8,
            demand_band[1] * 1.2,
        )

        # Convert to vehicle counts per bin
        bin_vehs_float = bin_demands * (bin_seconds / 3600.0)
        total_vehicles = max(1, int(round(bin_vehs_float.sum())))

        # Split mainline/ramp
        ramp_frac = rng.uniform(*ramp_fraction_range)
        total_ramp = max(0, int(round(total_vehicles * ramp_frac)))
        total_mainline = total_vehicles - total_ramp

        mainline_counts = _largest_remainder(bin_vehs_float, total_mainline)
        ramp_counts = _largest_remainder(bin_vehs_float, total_ramp)

        # Sample weather
        weather = str(rng.choice(w_names, p=w_weights))

        profile = DemandProfile(
            duration_s=duration_s,
            bin_seconds=bin_seconds,
            mainline_counts=mainline_counts,
            ramp_counts=ramp_counts,
            control_points_t=np.array([0.0, float(duration_s)]),
            control_points_vph=np.array([base_vph, base_vph]),
            ramp_fraction=ramp_frac,
            total_vehicles=total_vehicles,
            peak_demand_vph=float(bin_demands.max()),
            seed=seed,
            noise_randomness=noise_std_vph / max(base_vph, 1.0),
            weather=weather,
            metadata={"mode": "focused_band", "base_vph": base_vph},
        )

        rou_name = (
            f"{prefix}_{idx:04d}_D{int(base_vph)}"
            f"_R{ramp_frac:.0%}_{weather}_s{seed}"
        )
        rou_path = out_path / f"{rou_name}.rou.xml"
        cfg_path = out_path / f"{rou_name}.sumocfg"

        from tests._sumo_helpers import generate_sumocfg
        _write_route_file(rou_path, profile, cav_pct, seed, weather=weather)
        generate_sumocfg(cfg_path, rou_path, duration_s)
        cfg_paths.append(str(cfg_path))

        if (idx + 1) % 50 == 0 or idx == n_scenarios - 1:
            logger.info("Generated %d/%d focused scenarios", idx + 1, n_scenarios)

    logger.info(
        "Focused pool: %d scenarios in %s (band=%d-%d vph, noise=±%.0f)",
        n_scenarios, output_dir, demand_band[0], demand_band[1], noise_std_vph,
    )
    return cfg_paths


def _write_route_file(
    output_path: Path,
    profile,
    cav_pct: float,
    seed: int,
    weather: str = "clear",
) -> None:
    """Write a .rou.xml from a DemandProfile using the Hermite-generated counts."""
    from traffic_environment.vehicle_fleet import generate_fleet_xml, pick_vehicle_type

    fleet_xml = generate_fleet_xml(seed=seed, weather=weather)
    rng = np.random.RandomState(seed + 10_000)

    vehicles = []
    veh_id = 0

    RAMP_DELAY_S = 100

    n_bins = profile.n_bins
    for bin_idx in range(n_bins):
        t0 = bin_idx * profile.bin_seconds
        bs = profile.bin_seconds

        # Mainline vehicles in this bin
        n_main = int(profile.mainline_counts[bin_idx])
        if n_main > 0:
            step = bs / n_main
            for i in range(n_main):
                dep = t0 + (i + 0.5) * step
                if dep > profile.duration_s:
                    break
                vehicles.append((dep, "mainline_through", veh_id))
                veh_id += 1

        # Ramp vehicles in this bin (delayed start)
        n_ramp = int(profile.ramp_counts[bin_idx])
        if n_ramp > 0:
            # Shift ramp departures by RAMP_DELAY_S
            ramp_t0 = max(t0, RAMP_DELAY_S)
            ramp_bs = max(1.0, t0 + bs - ramp_t0)
            step = ramp_bs / n_ramp
            for i in range(n_ramp):
                dep = ramp_t0 + (i + 0.5) * step
                if dep > profile.duration_s:
                    break
                vehicles.append((dep, "ramp_on_through", veh_id))
                veh_id += 1

    vehicles.sort(key=lambda v: v[0])

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append("<routes>")
    lines.append(fleet_xml)
    lines.append('  <route id="mainline_through" '
                 'edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"/>')
    lines.append('  <route id="ramp_on_through" '
                 'edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')
    lines.append('  <route id="ramp_route" '
                 'edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')

    for _, (depart, route_id, _vid) in enumerate(vehicles):
        is_cav = rng.random() * 100.0 < cav_pct
        vtype = pick_vehicle_type(rng, is_cav=is_cav)
        lines.append(
            f'  <vehicle id="veh_{_vid}" type="{vtype}" '
            f'route="{route_id}" depart="{depart:.2f}" '
            f'departPos="last" departLane="best" '
            f'departSpeed="desired" insertionChecks="none"/>'
        )

    lines.append("</routes>")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
