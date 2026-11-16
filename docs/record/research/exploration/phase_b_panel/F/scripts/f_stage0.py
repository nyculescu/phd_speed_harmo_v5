"""EXPLORATORY: stage-0 statements for screen F from the stored S6 rows. Convention of planb.md §8.1: effect = -median(P - O) / median(O) * 100."""
import numpy as np
Z = np.load("f_scalars.npz"); KEYS = list(Z["keys"]); n = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda cell, arm, key: Z[f"{cell}|{arm}"][:, KEYS.index(key)]
def val(cell, arm, f):
    if arm == "v3w":
        return np.mean([f(cell, l) for l in LEARN], axis=0)
    return f(cell, arm)
rng = np.random.default_rng(20261112)
IDX = rng.integers(0, n, (20_000, n))
def eff(P, O, lev=97.5):
    d = -(P - O)
    den = np.median(O)
    b = np.median(d[IDX], axis=1) / den * 100
    a = (100 - lev) / 2
    return float(np.median(d) / den * 100), float(np.percentile(b, a)), float(np.percentile(b, 100 - a))
fm = lambda t: "%+.2f [%+.2f, %+.2f]" % t
M = {
 "cf all (ttc_net)": lambda c, a: col(c, a, "ttc_net"),
 "cf off merge 2 (roads 1,2,3a,3,5,ramp1)": lambda c, a: sum(col(c, a, f"rt_{r}") for r in ("1", "2", "3a", "3", "5", "ramp1")),
 "cf merge-2 area (4a,4,ramp2)": lambda c, a: sum(col(c, a, f"rt_{r}") for r in ("4a", "4", "ramp2")),
 "cf junction lanes": lambda c, a: col(c, a, "rt_junction"),
 "cf without lane-change samples": lambda c, a: col(c, a, "m_ttc3_all") - col(c, a, "m_ttc3_lc"),
 "cf lane-change samples": lambda c, a: col(c, a, "m_ttc3_lc"),
 "cf at >= 10 m/s": lambda c, a: col(c, a, "ttc3_s_hi"),
 "cf below 5 m/s": lambda c, a: col(c, a, "ttc3_s_lo"),
 "delay": lambda c, a: col(c, a, "all_delay"),
}
for cell in ("TRUCK", "S"):
    print("==", cell)
    for name, f in M.items():
        P = val(cell, "v3w", f)
        line = []
        for o in ("3E-C_TRUCK", "os0_10_10", "p333", "nc"):
            O = val(cell, o, f)
            line.append("%s %s (med %.0f)" % (o, fm(eff(P, O)), np.median(O)))
        print("  %-42s v3w med %.0f | " % (name, np.median(P)) + " | ".join(line))
    f = M["cf off merge 2 (roads 1,2,3a,3,5,ramp1)"]
    O = val(cell, "3E-C_TRUCK", f)
    per = [eff(f(cell, l), O) for l in LEARN]
    print("  per learner, off merge 2 vs 3E-C:", " | ".join(fm(p) for p in per))
# check sum identity
c = "TRUCK"
tot = sum(col(c, "p333", f"rt_{r}") for r in ("1", "2", "3a", "3", "4a", "4", "5", "ramp1", "ramp2", "junction"))
print("road sum equals ttc_net on p333 TRUCK:", bool(np.allclose(tot, col(c, "p333", "ttc_net"))), "| m_ttc3_all equals ttc_net:", bool(np.allclose(col(c, "p333", "m_ttc3_all"), col(c, "p333", "ttc_net"))))
# T0 record from the stored rows
names = [k for k in Z.files if "|" in k]
mm = sum(Z[k][:, KEYS.index("tau_mismatch")].sum() for k in names)
on = sum(Z[k][:, KEYS.index("tau_on_n")].sum() for k in names)
ma = sum(Z[k][:, KEYS.index("tau_on_match")].sum() for k in names)
print("T0: rows %d, tau_mismatch total %.0f, tau_on_n %.0f, tau_on_match %.0f (%.2f %%)" % (len(names) * n, mm, on, ma, 100 * ma / on))
for a in ("p333", "3E-C_TRUCK", "nc", "w0u250"):
    k = f"TRUCK|{a}"
    print("   ", a, "tau_on_n median %.0f, match share %.3f, mismatch sum %.0f" % (np.median(Z[k][:, KEYS.index("tau_on_n")]), Z[k][:, KEYS.index("tau_on_match")].sum() / max(Z[k][:, KEYS.index("tau_on_n")].sum(), 1), Z[k][:, KEYS.index("tau_mismatch")].sum()))
