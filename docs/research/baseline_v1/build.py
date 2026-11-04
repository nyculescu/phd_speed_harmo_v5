"""V329: baseline v1 tables from the instrumented no-control runs. usage: build.py baseline_dir out_dir"""
import csv
import json
import shutil
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "baseline_v0"))
import build as b     # the baseline v0 builder: same definitions

X, T = Path(sys.argv[1]), Path(sys.argv[2])


if __name__ == "__main__":
    runs = sorted((X / "detail/runs").glob("*.json.gz"))
    P = defaultdict(list)
    demand = None
    with ProcessPoolExecutor(8) as ex:
        for o in ex.map(b.one_run, map(str, runs), chunksize=8):
            for k in ("delay", "lanes", "series", "lc", "times", "entry"):
                P[k] += o[k]
    b.write("detail_delay_per_run.csv.gz", P["delay"])
    b.write("detail_lanes_per_run.csv.gz", P["lanes"])
    dv = ("n", "finished_pct", "time_in_system_s", "insertion_wait_s", "delay_finished_s", "delay_p50_s", "delay_p95_s", "delay_max_s")
    b.write("detail_delay.csv", b.med_table(P["delay"], ("name", "q", "group"), dv))
    b.write("detail_lanes.csv", b.med_table(P["lanes"], ("name", "q", "lane"), ("density_veh_km", "speed_ms", "flow_veh_h", "halting")))
    b.write("detail_lane_timeseries.csv.gz", b.med_table(P["series"], ("name", "q", "lane", "bin_min"), ("density_veh_km", "speed_ms", "flow_veh_h", "halting")))
    b.write("detail_lane_changes.csv", b.med_table(P["lc"], ("name", "q", "edge", "type", "dir"), ("count",)))
    b.write("detail_edge_times.csv", b.med_table(P["times"], ("name", "q", "route", "type", "edge"), ("median_s", "p95_s")))
    b.write("detail_entry_lanes.csv", b.med_table(P["entry"], ("name", "q", "route", "type", "edge", "lane"), ("count",)))
    for f in ("constants.json", "plant_net.xml", "plant_add.xml", "plant_spec.json"):
        shutil.copy(X / "plant" / f, T / f)
    print(len(runs), "runs")
