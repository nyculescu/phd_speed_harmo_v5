t = open("part1.md").read()
R = [
("| 5 % | 45-52 % | 1.4-1.8 % |", "| 5 % | 44-52 % | 1.4-1.8 % |"),
("- With the 60-seed pick before it (one arm at the effect, three at 0): PASS 39-46 % at 5 %, 72-95 % at 6 %.",
 "- With the 60-seed pick before it (one arm at the effect, three at 0; two noise cases): PASS 39-46 % at 5 %, 72-95 % at 6 %."),
("p333, the stored pick (none of 22 stored rules has less delay by point), and os0_10_10", "p333, the stored pick (none of 22 stored rules has less delay by point, EXPLORATORY), and os0_10_10"),
("(stored arms: 0-2 stuck rows of 240)", "(stored arms: 0-2 stuck rows of 240, EXPLORATORY)"),
]
for a, b in R:
    assert a in t, a[:50]
    t = t.replace(a, b)
open("part1.md", "w").write(t)
