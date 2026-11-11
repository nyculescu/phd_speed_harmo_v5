import gzip, json, sys, collections
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/"
files = ["phase1/step1_test.jsonl.gz", "phase1/step2_eval.jsonl.gz", "phase1/step3_eval.jsonl.gz", "phase2/oracle_rows.jsonl.gz", "phase2/hw_rows.jsonl.gz", "phase2/stepa_rows.jsonl.gz", "phase2/confirm_rows.jsonl.gz", "phase2/type_rows.jsonl.gz", "phase3/eval_rows.jsonl.gz", "phase3/rulecheck_rows.jsonl.gz", "phase3/shot_rows.jsonl.gz"]
for f in files:
    rows = [json.loads(l) for l in gzip.open(R + f, "rt")]
    keys = collections.Counter()
    plant = collections.Counter()
    names = collections.Counter()
    qs = collections.Counter()
    seeds = set()
    for r in rows:
        keys.update(r.keys())
        c = r.get("cfg", {})
        p = c.get("plant") if isinstance(c, dict) else None
        plant[json.dumps(p, sort_keys=True)] += 1
        names[r.get("name")] += 1
        qs[r.get("q")] += 1
        seeds.add(r.get("seed"))
    print("==", f, len(rows), "rows; seeds", min(seeds), max(seeds), len(seeds), "q", dict(qs))
    want = ["N", "dist", "dist_step", "delay", "all_delay", "finished_pct", "passed", "arrived", "ttc_net", "b45_net", "b7_net", "delay_ramp"]
    print("  has:", {k: keys.get(k, 0) for k in want})
    print("  plant:", dict(plant))
    print("  cfg keys:", sorted({k for r in rows for k in (r.get("cfg") or {}).keys()}))
    print("  n names:", len(names), list(names)[:14])
