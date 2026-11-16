import re, sys
t = open(sys.argv[1]).read()
toks = [w for w in t.split() if re.search(r"[A-Za-z0-9]", w)]
print("tokens with a letter or digit:", len(toks))
sec = re.split(r"\n## ", t)
for s in sec:
    print(len([w for w in s.split() if re.search(r"[A-Za-z0-9]", w)]), s.split("\n")[0][:60])
