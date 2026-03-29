#!/usr/bin/env python3
"""
Generate scenario pools for training/evaluation.

Usage:
  # Focused band (training — demand stays where VSL works):
  python generate_scenarios.py focused --n 200 --band 5500 7250 --noise 200

  # Full Hermite (generalization testing — messy realistic demand):
  python generate_scenarios.py hermite --n 200 --peak-range 5500 8000

  # Both share the same output structure — just swap the pool directory
  # in the training config to switch between them.
"""
import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    parser = argparse.ArgumentParser(description="Generate scenario pools")
    sub = parser.add_subparsers(dest="mode", required=True)

    # Focused band mode
    p_focused = sub.add_parser("focused", help="Flat demand in a specific band + noise")
    p_focused.add_argument("--n", type=int, default=200, help="Number of scenarios")
    p_focused.add_argument("--band", type=float, nargs=2, default=[5500, 7250],
                           help="Demand band [min max] vph")
    p_focused.add_argument("--noise", type=float, default=200,
                           help="Gaussian noise std (vph)")
    p_focused.add_argument("--duration", type=int, default=3600, help="Episode seconds")
    p_focused.add_argument("--cav", type=float, default=50.0, help="CAV percent")
    p_focused.add_argument("--seed", type=int, default=0, help="Base seed")
    p_focused.add_argument("--weather", type=str, default="clear:1.0",
                           help="Weather mix, e.g. 'clear:0.7,rain:0.3'")
    p_focused.add_argument("-o", "--output", type=str, default=None,
                           help="Output directory")

    # Hermite mode
    p_hermite = sub.add_parser("hermite", help="Full piecewise Hermite profiles")
    p_hermite.add_argument("--n", type=int, default=200, help="Number of scenarios")
    p_hermite.add_argument("--peak-range", type=float, nargs=2, default=[5500, 8000],
                           help="Peak demand range [min max] vph")
    p_hermite.add_argument("--base-range", type=float, nargs=2, default=[2500, 4000],
                           help="Base demand range [min max] vph")
    p_hermite.add_argument("--points", type=int, nargs=2, default=[5, 10],
                           help="Control points range [min max]")
    p_hermite.add_argument("--noise", type=float, default=0.5,
                           help="Noise randomness [0-1]")
    p_hermite.add_argument("--duration", type=int, default=3600, help="Episode seconds")
    p_hermite.add_argument("--cav", type=float, default=50.0, help="CAV percent")
    p_hermite.add_argument("--seed", type=int, default=0, help="Base seed")
    p_hermite.add_argument("--weather", type=str, default="clear:1.0",
                           help="Weather mix, e.g. 'clear:0.7,rain:0.3'")
    p_hermite.add_argument("-o", "--output", type=str, default=None,
                           help="Output directory")

    args = parser.parse_args()

    # Parse weather mix
    weather_mix = {}
    for pair in args.weather.split(","):
        parts = pair.strip().split(":")
        if len(parts) == 2:
            weather_mix[parts[0].strip()] = float(parts[1].strip())
    if not weather_mix:
        weather_mix = {"clear": 1.0}

    t0 = time.time()

    if args.mode == "focused":
        from traffic_environment.scenario_pool import generate_focused_pool

        output = args.output or f"scenario_pools/focused_{int(args.band[0])}-{int(args.band[1])}_n{args.n}"
        paths = generate_focused_pool(
            output_dir=output,
            n_scenarios=args.n,
            duration_s=args.duration,
            cav_pct=args.cav,
            seed_offset=args.seed,
            demand_band=tuple(args.band),
            noise_std_vph=args.noise,
            weather_mix=weather_mix,
        )

    elif args.mode == "hermite":
        from traffic_environment.scenario_pool import generate_scenario_pool

        output = args.output or f"scenario_pools/hermite_{int(args.peak_range[0])}-{int(args.peak_range[1])}_n{args.n}"
        paths = generate_scenario_pool(
            output_dir=output,
            n_scenarios=args.n,
            duration_s=args.duration,
            cav_pct=args.cav,
            seed_offset=args.seed,
            weather_mix=weather_mix,
            demand_kwargs={
                "peak_demand_range": tuple(args.peak_range),
                "base_demand_range": tuple(args.base_range),
                "n_points_range": tuple(args.points),
                "noise_randomness": args.noise,
            },
        )

    dt = time.time() - t0
    logging.info("Done: %d scenarios in %.1fs → %s", len(paths), dt, output)


if __name__ == "__main__":
    main()
