"""Pull the per-run values the V2/V3 readings need out of s6_rows.jsonl into one compact table."""
import json, sys, collections
import numpy as np

SRC = "/home/catalin/work/phd/v5b1_runs/vv_remote/vv_screen/s6_rows.jsonl"
MERGE = {"3a", "ramp1", "4a", "ramp2"}
road_keys = collections.Counter()
recs = []
with open(SRC) as f:
    for line in f:
        r = json.loads(line)
        length, arm = r["name"].split("|")
        rt = r.get("m_road_ttc3", {})
        grp = {"merge": 0, "e1": 0, "rest": 0}
        m1 = m2 = 0
        for road, per in rt.items():
            road_keys[road] += 1
            n = sum(per.values())
            if road in MERGE:
                grp["merge"] += n
            elif road == "1":
                grp["e1"] += n
            else:
                grp["rest"] += n
            if road in ("3a", "ramp1"):
                m1 += n
            if road in ("4a", "ramp2"):
                m2 += n
        sn = r.get("vv_stand_n", {}) or {}
        recs.append(dict(L=length, arm=arm, seed=r["seed"], learner=r.get("learner"), cell=r.get("cell"),
                         ttc_net=r["ttc_net"], m_ttc3_all=r.get("m_ttc3_all"), road_sum=sum(grp.values()),
                         merge=grp["merge"], e1=grp["e1"], rest=grp["rest"], m1=m1, m2=m2,
                         vv_m_time=r.get("vv_m_time"), vv_m_step=r.get("vv_m_step"), vv_m_whole=r.get("vv_m_whole"),
                         vv_m_half=r.get("vv_m_half"), ttc_half=r.get("ttc_half"), main=r.get("vv_ttc3_main"),
                         enc=r.get("vv_enc"), end_stop=r.get("end_stop"), end_stop2=r.get("end_stop2"),
                         stand_n1=sn.get("3a_0"), stand_n2=sn.get("4a_0"),
                         len3a=(r.get("vv_lanes") or {}).get("3a_0"), len4a=(r.get("vv_lanes") or {}).get("4a_0"),
                         all_delay=r.get("all_delay"), collisions=r.get("collisions"), passed=r.get("passed")))
print("rows", len(recs))
print("road keys in m_road_ttc3:", dict(road_keys))
json.dump(recs, open("runs.json", "w"))
