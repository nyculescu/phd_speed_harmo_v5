import json,os,statistics as st
R='/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
def load(k):
    p=R+k+'.json'
    return json.load(open(p)) if os.path.exists(p) else None
rows=[]
for s in range(7400500,7400600):
    n=load(f'c1800_slow_q2000_s{s}')
    ip=load(f'c1800-c800+back_slow_q2000_s{s}')
    ds={}
    for d in (30,60,120,240):
        x=load(f'c1800-c800+back_d{d}_slow_q2000_s{s}')
        ds[d]=x
    rows.append((s,n['delay_s'],ip['delay_s'],{d:(x['delay_s'] if x else None) for d,x in ds.items()}, ip['t_on'],ip['t_off'], {d:((x['t_switch'],x['t_back'],x['q_at_back']) if x else None) for d,x in ds.items()}))
for r in rows[:8]: print(r)
for d in (30,60,120,240):
    diffs=[r[1]-(r[3][d] if r[3][d] is not None else r[1]) for r in rows]
    eq=sum(1 for r in rows if r[3][d] is not None and abs(r[3][d]-r[1])<1e-9)
    miss=sum(1 for r in rows if r[3][d] is None)
    print(d,'median N-IPd',round(st.median(diffs),2),'exact equal to N',eq,'missing',miss)
