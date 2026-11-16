import sys
s=sorted({int(l.split()[1]) for l in open(sys.argv[1]) if l.strip()})
lo,hi=int(sys.argv[2]),int(sys.argv[3])
s=[x for x in s if lo<=x<=hi]
out=[];a=b=None
for x in s:
    if a is None: a=b=x
    elif x==b+1: b=x
    else: out.append((a,b)); a=b=x
if a is not None: out.append((a,b))
print(len(s),'seeds in',lo,hi)
print(' '.join(f'{a}-{b}' if a!=b else f'{a}' for a,b in out))
