import json, sys, collections
c = collections.Counter()
for f in sys.argv[1:]:
    for line in open(f):
        i = line.find('"name": "'); j = line.find('"', i + 9)
        k = line.find('"q": '); 
        name = line[i+9:j]
        q = line[k+5:line.find(',', k)]
        c[(f.split('/')[-1], name.split('|')[0], q)] += 1
for k, v in sorted(c.items()):
    print(k, v)
