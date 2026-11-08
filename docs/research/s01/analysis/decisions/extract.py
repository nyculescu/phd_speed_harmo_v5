"""Compact per-run table of the decision fields and the few outcome fields the decision analysis needs (read only)."""
import json
import pickle
import sys
from pathlib import Path

import numpy as np

DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(__file__).resolve().parent
DROP_PREFIX = ("m_vh_", "m_ah_", "m_minute", "m_mergepos", "m_offsets", "m_dur_", "m_peak_")
DROP = {"cfg", "flow_min", "v20_min", "pert_log"}


def main() -> int:
    T = {}
    for ph in ("test", "band", "s1"):
        for line in (DATA / f"rows_{ph}.jsonl").open():
            r = json.loads(line)
            row = {k: v for k, v in r.items() if k not in DROP and not k.startswith(DROP_PREFIX)}
            row["phase"] = ph
            row["pert_log"] = r.get("pert_log")
            z = np.load(DATA / "st" / r["m_st_file"])
            n = z["n"].astype(float)
            row["st_veh_s"] = float(n.sum())
            row["st_cells"] = list(n.shape)
            T[(ph, r["name"], r["q"], r["seed"])] = row
    pickle.dump(T, open(OUT / "compact.pkl", "wb"))
    print("rows", len(T), {ph: sum(k[0] == ph for k in T) for ph in ("test", "band", "s1")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
