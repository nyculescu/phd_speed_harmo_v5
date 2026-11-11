import gzip, json
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/"
for f in ["phase2/oracle_rows.jsonl.gz", "phase2/hw_rows.jsonl.gz", "phase2/confirm_rows.jsonl.gz", "phase3/eval_rows.jsonl.gz", "phase3/rulecheck_rows.jsonl.gz", "phase3/shot_rows.jsonl.gz"]:
    s = []
    for l in gzip.open(R + f, "rt"):
        n = json.loads(l)["name"]
        if n not in s: s.append(n)
    print(f, len(s)); print("  ", " ".join(s))
import os
print(os.listdir(R + "r2m3"))
