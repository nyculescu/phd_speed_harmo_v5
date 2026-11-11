from lib import *
A = load(FILES["r2test"]); B = load(FILES["s01test"])
n=0; diff=0; mx=0
for k in A:
    for s in A[k]:
        a=A[k][s]["all_delay"]; b=B[k][s]["all_delay"]; n+=1
        if a!=b: diff+=1; mx=max(mx,abs(a-b)/a)
print("r2test vs s01test all_delay: rows",n,"differ",diff,"max rel",mx)
for lab,f in {"r1test":RUNS+"round1_remote/out/test/test.jsonl","r1val":RUNS+"round1_remote/out/val/validation.jsonl","r2val":RUNS+"round2/val/rows_6c49e7e.jsonl"}.items():
    T=load(f); by=defaultdict(list)
    for (n_,q),S in T.items():
        c,a=n_.split("|"); by[(c,q)].append((a,len(S),min(S),max(S)))
    print("==",lab)
    for (c,q),L in sorted(by.items()):
        print(" ",c,q,len(L),sorted({(x[1],x[2],x[3]) for x in L})); print("    "," ".join(sorted(x[0] for x in L)))
