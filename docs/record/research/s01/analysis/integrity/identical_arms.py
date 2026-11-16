"""Arms whose runs are identical trajectories (every plant field equal on a seed): per cell and level, which arm pairs share
how many seeds exactly. Read only."""
import hashlib
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

M = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(__file__).resolve().parent
SKIP = {"name", "cfg", "m_st_file"}


def h(r, plant_only):
    keep = {k: v for k, v in r.items() if k not in SKIP and not (plant_only and k.startswith("m_"))}
    return hashlib.sha1(json.dumps(keep, sort_keys=True).encode()).hexdigest()


def main():
    res = {}
    for ph in ("test", "band", "s1"):
        G = defaultdict(lambda: defaultdict(dict))
        for line in open(M / f"rows_{ph}.jsonl"):
            r = json.loads(line)
            c = r["name"].split("|")[0]
            G[(c, r["q"])][r["name"].split("|")[1]][r["seed"]] = (h(r, True), r["all_delay"], r["ttc_net"])
        out = {}
        for (c, q), A in sorted(G.items()):
            pairs = []
            for a, b in combinations(sorted(A), 2):
                ds = sorted(set(A[a]) & set(A[b]))
                same = sum(A[a][s][0] == A[b][s][0] for s in ds)
                same_delay = sum(A[a][s][1] == A[b][s][1] for s in ds)
                if same or same_delay:
                    pairs.append({"a": a, "b": b, "seeds": len(ds), "identical_rows": same, "equal_all_delay": same_delay})
            out[f"{c}|{q:.0f}"] = pairs
            if pairs:
                print(ph, c, q, [(p["a"], p["b"], f"{p['identical_rows']}/{p['seeds']}", f"delay= {p['equal_all_delay']}") for p in pairs])
        res[ph] = out
    (OUT / "identical_arms.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
