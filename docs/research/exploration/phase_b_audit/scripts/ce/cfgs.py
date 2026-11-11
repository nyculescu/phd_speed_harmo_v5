import gzip, json
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/"
def show(f, names):
    seen = {}
    for l in gzip.open(R + f, "rt"):
        r = json.loads(l)
        if r["name"] in names and r["name"] not in seen:
            c = dict(r["cfg"]); ctrl = c.get("ctrl")
            s = json.dumps(c, sort_keys=True)
            seen[r["name"]] = s[:420]
    print("==", f)
    for k, v in seen.items(): print("  ", k, "::", v)
show("phase1/step2_eval.jsonl.gz", {"p0", "p333", "a333", "d0"})
show("phase1/step3_eval.jsonl.gz", {"p333v90", "d0"})
show("phase2/confirm_rows.jsonl.gz", {"p333", "p333h10", "lr", "oracle_slow25"})
show("phase2/hw_rows.jsonl.gz", {"p333_slow25", "hw25_d500_l1"})
show("phase2/oracle_rows.jsonl.gz", {"p333_slow25", "p333_slow25_o500_80"})
show("phase3/eval_rows.jsonl.gz", {"r2m3|X1|p333", "r2m3|X1|d0", "r2m3|X1|lr", "r1m3|S|p333"})
show("phase3/shot_rows.jsonl.gz", {"X1|p333", "X1|r4a1", "X1|d0"})
show("r2m3/test_rows.jsonl.gz", {"p33333", "p13333", "nc"})
