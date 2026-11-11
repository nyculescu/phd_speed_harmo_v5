"""Provenance tally, second set. Counts only."""
import json, glob, collections
R = '/home/catalin/work/phd/v5b1_runs/'
FILES = {
 'V382 T0': R+'conf3/t0/prerun.jsonl',
 'conf3 map': R+'conf3/eval_map*.jsonl',
 'round1 val': R+'round1_remote/out/val/validation.jsonl',
 'round1 stage0b': R+'round1_remote/out/stage0/stage0b.jsonl',
 'planb S3a': R+'planb_s34_remote/s3a/repick_runs.jsonl',
 'planb ASCH tune': R+'planb_s34_remote/asch/tune_runs.jsonl',
 'planb MPC-F gate': R+'planb_s34_remote/mpcf/gate_runs.jsonl',
 'planb 3E-D check': R+'planb_s34_remote/cmab/TRUCK_delay/check_runs.jsonl',
 'planb S2': R+'planb_remote/s2/*.jsonl',
}
PK = ('smooth','ease','smooth_s','ease_max','tau_rise','taper_fast','fix_x','geom')
def find_plant(cfg):
    out = {}
    def walk(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in PK and not isinstance(v, dict): out.setdefault(k, v)
                walk(v)
    walk(cfg)
    return tuple(sorted((k, str(v)) for k, v in out.items()))
for label, pat in FILES.items():
    fs = sorted(glob.glob(pat))
    if not fs: print(label, 'NO FILE'); continue
    n = 0; plants = collections.Counter(); hasall = 0; seeds = set(); qs = set(); conds = set()
    for f in fs:
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception: continue
            if not isinstance(r, dict): continue
            n += 1; plants[find_plant(r.get('cfg', {}))] += 1; hasall += ('all_delay' in r)
            if 'seed' in r: seeds.add(r['seed'])
            if 'q' in r: qs.add(r['q'])
            if 'name' in r and '|' in str(r['name']): conds.add(str(r['name']).split('|')[0])
    print('==', label, 'files', len(fs), 'rows', n, 'all_delay', hasall, '| seeds', len(seeds), (min(seeds), max(seeds)) if seeds else None, '| q', sorted(qs)[:8], '| cond', sorted(conds)[:10])
    for p, c in plants.items(): print('   plant', c, dict(p))
