"""Bottleneck-anchored network screen (docs/plans/day_pattern_corridor_selection_protocol_v1.md, committed first).

python -m vsl_lab.data.bn_screen pull      # counts for the screening lane-days (14,488 new requests, <= 5 req/s)
python -m vsl_lab.data.bn_screen screen    # detection, feasibility, ranking -> docs/plans/day_pattern_bnscreen_v1.json
"""
from __future__ import annotations

import gzip
import json
import math
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from vsl_lab.data.mndot import (CONFIG, DATA_ROOT, Fetcher, _dist, available_cached, screening_dates, windows)

OUT = Path(__file__).resolve().parents[2] / "docs" / "plans" / "day_pattern_bnscreen_v1.json"


def screen_lane(date: str, dets: list) -> str | None:
    """The screening's lane for a station-day: available that day, middle lane first, with cached non-null occupancy."""
    av = set(available_cached(date))
    ds = [d for d in dets if d in av]
    for det in sorted(ds, key=lambda d: abs(ds.index(d) - (len(ds) - 1) / 2)):
        f = DATA_ROOT / "mayfly" / date[:4] / date / f"{det}.occupancy.json"
        if f.exists() and f.read_text() != "null":
            return det
    return None


def pull() -> dict:
    st = {s["node"]: s["dets"] for w in windows() for s in w["stations"]}
    f = Fetcher()
    t0 = time.time()
    log = DATA_ROOT / "bnscreen_pull_progress.log"
    dates = screening_dates()
    for i, d in enumerate(dates):
        for node, ds in st.items():
            det = screen_lane(d, ds)
            if det is not None:
                f.get("counts", d, det)
        with open(log, "a") as fh:
            fh.write(f"{time.strftime('%H:%M:%S')} date {i + 1}/{len(dates)} {d} req={f.n_req} cached={f.n_cached} "
                     f"404={f.n_404} err={f.n_err} elapsed={time.time() - t0:.0f}s\n")
    return {"req": f.n_req, "cached": f.n_cached, "404": f.n_404, "err": f.n_err}


def main(argv=None) -> int:
    what = (argv or sys.argv[1:] or ["screen"])[0]
    if what == "pull":
        print(json.dumps(pull()))
        return 0
    from vsl_lab.data.bn_screen_analysis import screen   # analysis kept separate so the pull can start first
    res = screen()
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in ("n_pairs", "n_candidates", "n_feasible")} | {"top3": [
        (c["route"], c["dir"], c["u_label"], c["share"]) for c in res["top3"]]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
