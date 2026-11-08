import sys,re
txt=open(sys.argv[1],encoding='utf-8').read().split('\n')
for pat in sys.argv[2:]:
    print('==',pat)
    n=0
    for i,l in enumerate(txt,1):
        for m in re.finditer(re.escape(pat),l):
            v=l.split('|')[1].strip() if l.startswith('|') else ''
            print(f'  L{i} {v}: ...{l[max(0,m.start()-220):m.end()+180]}...')
            n+=1
            if n>=4: break
        if n>=4: break
