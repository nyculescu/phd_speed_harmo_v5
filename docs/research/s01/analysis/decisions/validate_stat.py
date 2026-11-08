"""The reimplemented statistic against conf3/common.py raw (imported read only, no bytecode written), on round 2's
X1 reading v3w vs nc (round_2_result.md: delay +27.3, TTC -16.6), and the measured rows against round 2's stored rows."""
import json
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, "/home/catalin/work/phd/wt/r2-metrics/docs/research/conf3")
import numpy as np  # noqa: E402
from common import raw as raw_ref, load  # noqa: E402

from common_dec import GROUPS, load_table, arm_values, raw  # noqa: E402

M = load_table()
k = ("test", "X1", 5300.0)
for f in ("all_delay", "ttc_net"):
    A = arm_values(M, k, GROUPS["v3w"], f)
    O = arm_values(M, k, ["nc"], f)
    mine = raw(A, O, -1, (2.5, 97.5))
    ref = raw_ref({s: {f: v} for s, v in A.items()}, {s: {f: v} for s, v in O.items()}, f, -1, (2.5, 97.5))
    print(f, "mine", [round(x, 3) for x in mine[:3]], "conf3 raw", [round(x, 3) for x in ref], "equal", np.allclose(mine[:3], ref))

# measured rows equal the stored round-2 rows on the keys both carry
S = load("/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl", "/home/catalin/work/phd/v5b1_runs/round2/band/rows_6c49e7e.jsonl")
bad = n = 0
keys = ("all_delay", "ttc_net", "passed", "lv", "lv_sum_4", "lv_n_4", "tau_on_match", "N")
for ph in ("test", "band"):
    for line in open(f"/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_{ph}.jsonl"):
        r = json.loads(line)
        ref = S.get((r["name"], r["q"]), {}).get(r["seed"])
        if ref is None:
            continue
        n += 1
        bad += any(ref.get(x) != r.get(x) for x in keys)
print("rows compared", n, "rows differing on", keys, ":", bad)
