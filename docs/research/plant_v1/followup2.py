"""V326: the smooth no-undertaking rule crossed with lane-change assertiveness and human undertaking. usage: followup2.py out_dir workers"""
import sys
from pathlib import Path

from v5b.fleet import plant_sweep as ps

ALL96 = {"lcStrategic": 0.5, "lcCooperative": 0.8, "lcAssertive": 1.5, "lcLookaheadLeft": 1, "tau_scale": 0.7, "asl_scale": 0.25}
CANDIDATES = {"base": {}, "as1.4": {"lcAssertive": 1.4}, "all96": ALL96}
for h in (0, 0.5):
    tag = {"human_undertake": h} if h else {}
    CANDIDATES[f"sm_h{h}"] = {"smooth": True, **tag}
    for a in (1.3, 1.4, 1.5):
        CANDIDATES[f"sm_as{a}_h{h}"] = {"smooth": True, "lcAssertive": a, **tag}
    CANDIDATES[f"sm_all96_h{h}"] = {"smooth": True, **ALL96, **tag}

if __name__ == "__main__":
    out = Path(sys.argv[1])
    ps.matrix(CANDIDATES, ps.LADDER, ps.SEEDS["D"], out / "stage_d3.jsonl", int(sys.argv[2]), str(out / "rd"))
    print("done", flush=True)
