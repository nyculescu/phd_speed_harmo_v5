from lib import *
T = load(FILES["s01test"]); REF = 100/3.6
ST = RUNS + "measure_s01_remote/st/"
for n in ("X1|p333", "X1|w0u250", "X2|nc"):
    r = T[(n, 5300.0)][7440841]
    z = np.load(ST + r["m_st_file"]); v, c = z["v"], z["n"]
    D = c - v / REF
    mm = r["m_minute"]
    print(n, "keys", list(z.keys()), v.shape, "minute keys", sorted(mm.keys()))
    print("  all_delay", round(r["all_delay"]), "N", r["N"], "st n sum", c.sum(), "st delay", round(D.sum()), "dist_step/REF", round(r["dist_step"]/REF), "st dist/REF", round(v.sum()/REF),
          "ramp pend", sum(mm["ramp1_pending"]), sum(mm["ramp2_pending"]), "ramp queue", sum(mm["ramp1_queue"]), sum(mm["ramp2_queue"]), "offsets", r["m_offsets"])
    print("  keys m_:", [k for k in r if k.startswith("m_") and ("pend" in k or "stuck" in k or "road" in k)])
