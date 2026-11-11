from lib import *
import pickle
T = load(FILES["s01test"]); REF = 100/3.6; Q = 5300.0
ST = RUNS + "measure_s01_remote/st/"
W = ["w0u250","w1u500","w2u250","w3u500","w4u500"]
SEG = [("up 1-2", 0, 3498.3), ("m1 3a", 3498.3, 3793.02), ("between 3", 3793.02, 4987.32), ("m2 4a", 4987.32, 5282.04), ("down 4-5", 5282.04, 6800)]
PER = {"X1": [("before 300-600", 300, 600), ("slow1 600-720", 600, 720), ("after1 720-840", 720, 840), ("mid 840-1200", 840, 1200), ("slow2 1200-1320", 1200, 1320), ("after2 1320-1440", 1320, 1440), ("end 1440-1800", 1440, 1800)],
       "X2": [("before 300-700", 300, 700), ("slow 700-880", 700, 880), ("after 880-1000", 880, 1000), ("1000-1400", 1000, 1400), ("1400-1800", 1400, 1800)]}
xs = np.arange(136) * 50.0
ts = 300 + np.arange(150) * 10.0     # bin start
tm = 300 + np.arange(25) * 60.0
def comp(r, cell):
    z = np.load(ST + r["m_st_file"]); D = z["n"].astype(float) - z["v"].astype(float) / REF
    out = {}
    for pn, a, b in PER[cell]:
        tk = (ts >= a) & (ts < b)
        for sn, x0, x1 in SEG:
            out[("main", pn, sn)] = D[tk][:, (xs >= x0) & (xs < x1)].sum()
        mk = (tm >= a - 30) & (tm < b - 30)     # minute bins assigned by their centre
        mm = r["m_minute"]
        out[("pend_r1", pn, "")] = float(np.array(mm["ramp1_pending"])[mk[:len(mm["ramp1_pending"])]].sum())
        out[("pend_r2", pn, "")] = float(np.array(mm["ramp2_pending"])[mk[:len(mm["ramp2_pending"])]].sum())
        out[("queue_r2", pn, "")] = float(np.array(mm["ramp2_queue"])[mk[:len(mm["ramp2_queue"])]].sum())
        out[("queue_r1", pn, "")] = float(np.array(mm["ramp1_queue"])[mk[:len(mm["ramp1_queue"])]].sum())
    out[("total", "", "")] = r["all_delay"]
    out[("main_all", "", "")] = D.sum()
    out[("pend_all", "", "")] = float(sum(mm["ramp1_pending"]) + sum(mm["ramp2_pending"]))
    out[("resid", "", "")] = r["all_delay"] - D.sum() - out[("pend_all", "", "")]
    out[("N_off_main", "", "")] = r["N"] - float(z["n"].sum()) - out[("pend_all", "", "")]
    out[("dist", "", "")] = r["dist_step"] / REF
    out[("N", "", "")] = r["N"]
    for k in ("end_stop2", "end_stop", "passed", "arrived", "delay_ramp2", "delay_ramp", "delay", "halt_3a_0"):
        out[(k, "", "")] = val(r, k)
    out[("cumflow", "", "")] = np.cumsum(r["flow_min"][:25]).astype(float)
    return out
res = {}
for cell, arms in (("X1", ["p333", "lr1000_10_1", "os0_10_10", "3ex1", "nc"]), ("X2", ["p333", "os0_10_10", "3ex2", "lr1000_10_1", "nc"])):
    C = {}
    for a in W + arms:
        C[a] = {s: comp(r, cell) for s, r in T[(f"{cell}|{a}", Q)].items()}
        print(cell, a, len(C[a]), flush=True)
    res[cell] = C
pickle.dump(res, open("b1.pkl", "wb"))
