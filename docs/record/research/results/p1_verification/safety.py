import json,os,re
from multiprocessing import Pool
from collections import Counter
R='/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
fs=[f for f in os.listdir(R) if re.search(r'_s74005\d\d\.json$',f)]
def one(f):
    d=json.load(open(R+f))
    return (d.get('collisions',0) or 0, d.get('emergency_stops',0) or 0, d.get('health'), tuple(d.get('health_codes') or ()), d.get('drained'))
if __name__=='__main__':
    with Pool(8) as p: out=p.map(one,fs,chunksize=500)
    print('files',len(fs))
    print('runs with collisions',sum(1 for o in out if o[0]>0),'total collisions',sum(o[0] for o in out))
    print('runs with estops',sum(1 for o in out if o[1]>0))
    print('health',Counter(o[2] for o in out))
    print('codes',Counter(c for o in out for c in o[3]).most_common(10))
    print('not drained',sum(1 for o in out if o[4] is False))
