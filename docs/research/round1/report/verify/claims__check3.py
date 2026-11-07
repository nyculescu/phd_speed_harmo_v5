"""Aggregates only: are baseline-v3 final rows identical to its u500 rows on every numeric key?"""
import sys
from pathlib import Path
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/conf3")
from common import load  # noqa: E402
T = load(Path("/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl"))
diff = 0
n = 0
for c in ("X1", "X2"):
    for i in range(5):
        F, D = T[(f"{c}|f{i}", 5300.0)], T[(f"{c}|d{i}", 5300.0)]
        for s in D:
            n += 1
            ks = {k for k, v in {**F[s], **D[s]}.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and k not in ("seed",)}
            diff += any(F[s].get(k) != D[s].get(k) for k in ks)
print("row pairs", n, "pairs with any numeric difference", diff)
