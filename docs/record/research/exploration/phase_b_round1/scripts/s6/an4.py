import numpy as np
exec(open("an1.py").read().split("FIELDS = [")[0])
ARMS = sorted({k.split("|")[1] for k in Z if "|" in k})
for cell in ("TRUCK", "S"):
    for f in ("collisions", "m_stuck_n", "gap25"):
        print(cell, f, {a: int(val(cell, a, f).sum()) for a in ARMS if val(cell, a, f).sum() > 0})
    for a in ("v3w", "p333", "3E-C_TRUCK", "nc"):
        g = (lambda f: pooled(cell, f)) if a == "v3w" else (lambda f: val(cell, a, f))
        print(" ", cell, a, "ttc15 share below 10 m/s %.1f %%, below 5 m/s %.1f %%; sev3 share at >= 10 m/s %.1f %%; sev3 on 4a %.1f %%; ttc15 on 4a %.1f %%; b45 1 Hz/step %.1f/%.1f; b7 %.2f/%.2f" % (
            100 * (g("ttc15_s_lo").mean() + g("ttc15_s_mid").mean()) / g("ttc15").mean(), 100 * g("ttc15_s_lo").mean() / g("ttc15").mean(), 100 * g("sev3_s_hi").mean() / g("sev3").mean(),
            100 * g("sev3_r_4a").mean() / g("sev3").mean(), 100 * g("ttc15_r_4a").mean() / g("ttc15").mean(), g("b45_net").mean(), g("b45_step").mean(), g("b7_net").mean(), g("b7_step").mean()))
    # ttc3 == ttc_net == m_ttc3_all on every row?
    print(" ", cell, "rows where ttc3 != ttc_net:", sum(int((val(cell, a, "ttc3") != val(cell, a, "ttc_net")).sum()) for a in ARMS), "; ttc3 != m_ttc3_all:", sum(int((val(cell, a, "ttc3") != val(cell, a, "m_ttc3_all")).sum()) for a in ARMS), "of", len(ARMS) * n)
    # sum of best-rule comparisons at >= 5 m/s outside 4a not available; print ev45 seconds vs events for v3w and 3E-C
    for a in ("v3w", "3E-C_TRUCK", "p333"):
        g = (lambda f: pooled(cell, f)) if a == "v3w" else (lambda f: val(cell, a, f))
        print(" ", cell, a, "events>=4.5: all %.0f (alks %.0f, car %.0f, truck %.0f); seconds at <= -4.5 (step) %.0f" % (g("ev45_all").mean(), g("ev45_alks").mean(), g("ev45_car").mean(), g("ev45_all").mean() - g("ev45_alks").mean() - g("ev45_car").mean(), g("b45_step").mean()))
