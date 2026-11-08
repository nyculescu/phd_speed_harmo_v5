n = 80
learners, nc, existing, picks, new = 5, 1, 15, 8, 3   # new: 3E-c, 3E-Dc, SCH-c
cell_arms = learners + nc + existing + picks + new
s5300_arms = learners + nc + existing + 2 * (picks + new)
s4600_arms = cell_arms
ev = 3 * cell_arms * n + s5300_arms * n + s4600_arms * n
checks = 330
for label, two in (("both searches", 2), ("3E-c only", 1)):
    for G in (40, 100):
        search = 384 * G + 40 + 11 * 40
        tune = 3 * (1400 + two * search + 100)
        tot = tune + ev + checks
        bA = (tot / 3050, tot / 2450)
        wA = (bA[0] / 0.88, bA[1] / 0.88)
        bB = tot / 6400
        print(label, G, "arms", cell_arms, s5300_arms, "eval", ev, "search", search, "tune", tune, "total", tot,
              "A batch %.1f-%.1f wall %.1f-%.1f $%.1f-%.1f" % (*bA, *wA, wA[0] * 0.312, wA[1] * 0.312),
              "B batch %.1f wall %.1f $%.1f" % (bB, bB / 0.88, bB / 0.88 * 0.81))
print("eval only A wall h %.1f-%.1f" % (ev / 3050 / 0.88, ev / 2450 / 0.88))
print("seeds used", 10 + 20 + 40 + 80)
