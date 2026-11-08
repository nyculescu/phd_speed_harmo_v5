import json, torch
D = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/"
paths = set()
for f in ("job_test.json", "job_band.json", "job_s1.json"):
    for n, a in json.load(open(D + f))["arms"].items():
        c = a.get("ctrl", {})
        for k in ("pt",):
            if k in c: paths.add(c[k])
        for p in c.get("pts", []): paths.add(p)
        if "switch" in c: paths.add(c["switch"]["pt"])
for p in sorted(paths):
    ck = torch.load(p, map_location="cpu", weights_only=False)
    print(p.split("v5b1_runs/")[1], "act_env=", ck.get("act_env"), "n_act=", ck.get("n_act"), "n_local=", ck.get("n_local"))
