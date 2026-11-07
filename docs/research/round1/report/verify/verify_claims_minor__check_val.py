"""F18: validation arms against os1_15_10 and no control (95 %), stored rows only."""
import sys
from pathlib import Path
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/round1")
from common1 import LEARNERS, arm_mean, load, raw  # noqa: E402

OUT = Path("/home/catalin/work/phd/v5b1_runs/round1_remote/out")
V = load(OUT / "val" / "validation.jsonl")
P95 = (2.5, 97.5)
ch = {"inc": [500] * 5, "w": [250, 250, 500, 500, 500], "r": [500, 500, 250, 500, 500], "a": [250, 500, 250, 500, 250]}
for c in ("X1", "X2"):
    R, nc = V[(f"{c}|os1_15_10", 5300.0)], V[(f"{c}|nc", 5300.0)]
    for lab, p in (("baseline-v3", "d"), ("v3w", "w"), ("res", "r"), ("attr", "a")):
        cks = ch["inc"] if p == "d" else ch[p]
        A = arm_mean(V, [f"{c}|{p}{i}u{cks[i]}" for i in range(LEARNERS)])
        t = [round(x, 1) for x in raw(A, R, "ttc_net", pct=P95)]
        tn = [round(x, 1) for x in raw(A, nc, "ttc_net", pct=P95)]
        dn = [round(x, 1) for x in raw(A, nc, "all_delay", pct=P95)]
        print(c, lab, "ttc vs os1_15_10", t, "| ttc vs nc", tn, "| delay vs nc", dn)
