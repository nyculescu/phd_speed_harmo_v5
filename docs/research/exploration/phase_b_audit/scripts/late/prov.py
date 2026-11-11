"""Provenance tally: plant flags and metric keys per rows file. Prints counts only."""
import json, sys, glob, gzip, collections
R = '/home/catalin/work/phd/v5b1_runs/'
FILES = {
 'conf3 eval primary': R+'conf3/eval_primary.jsonl',
 'conf3b x2': R+'conf3b/eval_x2.jsonl',
 'sweep V409': R+'sweep/sweep.jsonl',
 'osc V410': R+'osc/osc.jsonl',
 'round1_sweep V419': R+'round1_sweep/out/sweep1.jsonl',
 'round1 test': R+'round1_remote/out/test/test.jsonl',
 'round1 band': R+'round1_remote/out/test/band.jsonl',
 'round2 test': R+'round2/test/rows_6c49e7e.jsonl',
 'round2 val': R+'round2/val/rows_*.jsonl',
 's01 rows_s1': R+'measure_s01_remote/rows_s1.jsonl',
}
PK = ('smooth','ease','smooth_s','ease_max','tau_rise','taper_fast','fix_x','geom')
def find_plant(cfg):
    # plant flags may sit at top level of cfg or under a sub-dict
    out = {}
    def walk(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in PK and not isinstance(v, dict):
                    out.setdefault(k, v)
                walk(v)
    walk(cfg)
    return tuple(sorted((k, str(v)) for k, v in out.items()))
for label, pat in FILES.items():
    fs = sorted(glob.glob(pat))
    if not fs:
        print(label, 'NO FILE', pat); continue
    n = 0; plants = collections.Counter(); hasall = 0; qs = collections.Counter(); seeds = set(); names=set(); perts=collections.Counter()
    for f in fs:
        for line in open(f):
            line=line.strip()
            if not line: continue
            r = json.loads(line); n += 1
            plants[find_plant(r.get('cfg', r))] += 1
            hasall += ('all_delay' in r)
            if 'q' in r: qs[r['q']] += 1
            if 'seed' in r: seeds.add(r['seed'])
            if 'name' in r: names.add(r['name'].split('|')[0] if '|' in str(r['name']) else '-')
    print('==', label, 'files', len(fs), 'rows', n, 'all_delay rows', hasall)
    for p, c in plants.items(): print('   plant', c, dict(p))
    print('   seeds', len(seeds), min(seeds) if seeds else None, max(seeds) if seeds else None, '| levels', len(qs), sorted(qs)[:4], '...', sorted(qs)[-2:], '| cond', sorted(names)[:12])
