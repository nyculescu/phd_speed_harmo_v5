"""V323: the candidates V322 found, on the final-stage seeds and demand ladder. usage: followup.py out_dir workers"""
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

CANDIDATES = {f"as{a}": {"lcAssertive": a} for a in (1.2, 1.3, 1.4, 1.5, 1.6, 1.75)}
CANDIDATES |= {"as1.5_s0.5": {"lcStrategic": 0.5, "lcAssertive": 1.5},
               "all96": {"lcStrategic": 0.5, "lcCooperative": 0.8, "lcAssertive": 1.5, "lcLookaheadLeft": 1, "tau_scale": 0.7, "asl_scale": 0.25},
               "s0.5_lane600": {"lcStrategic": 0.5, "accel_len": 600}}

if __name__ == "__main__":
    out = Path(sys.argv[1])
    ps.matrix(CANDIDATES, ps.LADDER, ps.SEEDS["D"], out / "stage_d2.jsonl", int(sys.argv[2]), str(out / "rd"))
    print("done", flush=True)
