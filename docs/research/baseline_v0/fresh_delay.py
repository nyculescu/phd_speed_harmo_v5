"""V307: per-run tables for the instrumented re-run on seeds 7,419,960-979. usage: fresh_delay.py baseline_dir out_dir"""
import sys
from concurrent.futures import ProcessPoolExecutor

import build as b

if __name__ == "__main__":
    runs = sorted((b.X / "detail_fresh/runs").glob("*.json.gz"))
    P = {"delay": [], "lanes": []}
    with ProcessPoolExecutor(8) as ex:
        for o in ex.map(b.one_run, map(str, runs), chunksize=8):
            P["delay"] += o["delay"]
            P["lanes"] += o["lanes"]
    b.write("fresh_detail_delay_per_run.csv.gz", P["delay"])
    b.write("fresh_detail_lanes.csv", b.med_table(P["lanes"], ("name", "q", "lane"), ("density_veh_km", "speed_ms", "flow_veh_h", "halting")))
    print(len(runs), file=sys.stderr)
