import re, sys
t = open(sys.argv[1]).read()
p1 = t.split("# PART 2")[0]
def counts(s):
    toks = s.split()
    alnum = [x for x in toks if re.search(r"[A-Za-z0-9]", x)]
    letters = [x for x in toks if re.search(r"[A-Za-z]", x)]
    return len(toks), len(alnum), len(letters)
print("part 1: wc %d, tokens with a letter or digit %d, tokens with a letter %d" % counts(p1))
for sec in re.split(r"\n(?=## )", p1):
    print("  %-60s %s" % (sec.split("\n")[0][:60], counts(sec)))
