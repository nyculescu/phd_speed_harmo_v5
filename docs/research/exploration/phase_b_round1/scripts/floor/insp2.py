import json, collections, sys
for f in ("rows_band.jsonl", "rows_s1.jsonl", "rows_test.jsonl"):
    cnt = collections.Counter(); has = collections.Counter(); seeds = collections.defaultdict(set)
    for line in open("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/" + f):
        r = json.loads(line)
        k = (r["name"], r["q"])
        cnt[k] += 1; has["m_road_vs" in r] += 1; seeds[k].add(r["seed"])
    print(f, len(cnt), dict(has))
    names = sorted({k[0] for k in cnt}); qs = sorted({k[1] for k in cnt})
    print(" names:", names[:60]); print(" q:", qs)
    k0 = sorted(cnt)[0]; print(" e.g.", k0, cnt[k0], min(seeds[k0]), max(seeds[k0]))
