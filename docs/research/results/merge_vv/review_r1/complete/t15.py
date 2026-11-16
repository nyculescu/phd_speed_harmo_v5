import pickle, sys, collections
R = pickle.load(open(sys.argv[1], "rb"))
c = collections.Counter(); t = collections.Counter()
for (n, s), d in R.items():
    t[n] += 1; c[n] += "ttc15" in d
print({n: c[n] for n in sorted(t) if c[n] != t[n]} or "all have ttc15")
print("arms with ttc15:", sorted(n for n in t if c[n]))
