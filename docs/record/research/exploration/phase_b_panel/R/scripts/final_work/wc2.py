import re, sys
t = open(sys.argv[1]).read()
a = t.index(sys.argv[2]) if len(sys.argv) > 2 else 0
b = t.index(sys.argv[3]) if len(sys.argv) > 3 else len(t)
p = t[a:b]
cnt = lambda s: len([w for w in s.split() if re.search(r"[A-Za-z0-9]", w)])
print("words:", cnt(p))
for s in re.split(r"\n(?=## \d+\.)", p)[1:]:
    print(cnt(s), s.split("\n")[0][:50])
