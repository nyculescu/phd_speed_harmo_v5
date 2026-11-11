import re, sys
t = open(sys.argv[1]).read()
body = t[t.index('### 1.'):]
if '## PART 2' in body:
    body = body[:body.index('## PART 2')]
words = body.split()
print('tokens (wc -w)', len(words), '| with a letter or digit', len([w for w in words if re.search(r'[A-Za-z0-9]', w)]), '| with a letter', len([w for w in words if re.search(r'[A-Za-z]', w)]))
for s in re.split(r'\n### ', body):
    print(len(s.split()), len([w for w in s.split() if re.search(r'[A-Za-z]', w)]), s[:40].replace('\n', ' '))
for w in ('first', 'novel', 'safe', 'safer', 'proven', 'realistic', 'converged', 'safety'):
    n = len(re.findall(r'\b' + w + r'\b', t, flags=re.I))
    if n: print('BARRED', w, n)
