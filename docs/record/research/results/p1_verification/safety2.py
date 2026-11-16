import json,statistics as st
R='/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
res=json.load(open('/home/catalin/work/phd/v5b1_runs/p1/v99/result.json'))
A=res['tune']['arms']
for q in (1600,2000):
    a=A[str(q)]; N=a['N']
    for typ in ('slow','block','none'):
        arms={'NC':'NC','N':N,'PI':a['PI'],'FB':a['FB']}
        if typ!='none': arms['IP']=f"{N}-{a['IP'][typ]}"
        for nm,k in arms.items():
            es=[];ew=[]
            for s in range(7400500,7400600):
                d=json.load(open(R+f"{k}_{typ}_q{q}_s{s}.json"))
                es.append(d['emergency_stops']); ew.append(d['emergency_warnings'])
            print(q,typ,nm,'estops median',st.median(es),'share>0',sum(1 for x in es if x>0),'ewarn median',st.median(ew))
