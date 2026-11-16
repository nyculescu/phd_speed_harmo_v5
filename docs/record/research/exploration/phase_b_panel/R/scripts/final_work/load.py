# EXPLORATORY: own loader of the stored X1 rows (already read for verdicts); keeps three keys only.
import json, numpy as np
RUNS = "/home/catalin/work/phd/v5b1_runs/"
SETS = {"r1": (RUNS + "round1_remote/out/test/test.jsonl", ["w0", "w1", "w2", "w3", "w4"]),
        "r2v": (RUNS + "round2/val/rows_6c49e7e.jsonl", ["w0u250", "w1u250", "w2u500", "w3u500", "w4u500"]),
        "r2t": (RUNS + "round2/test/rows_6c49e7e.jsonl", ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"])}
RULES = ["p333", "lr1000_10_1", "os0_10_10", "lr1000_16_2", "os1_15_10", "lr400_13_2", "z33133", "os1_10_0", "r4a1", "a4400_10_1", "lr400_16_1", "copy"]
KEYS = ("all_delay", "ttc_net", "end_stop2")


def rows(f):
    T = {}
    with open(f) as h:
        for line in h:
            r = json.loads(line)
            if r["q"] != 5300.0 or not r["name"].startswith("X1|"):
                continue
            T.setdefault(r["name"][3:], {})[r["seed"]] = {k: float(r.get(k) or 0.0) for k in KEYS}
    return T


def arrays(key="all_delay"):
    L, O, NC, names_seen = [], [], [], set()
    for s, (f, lrn) in SETS.items():
        T = rows(f)
        names_seen |= set(T)
        seeds = sorted(T["p333"])
        assert len(seeds) == 40, (s, len(seeds))
        L.append(np.array([[T[n][k][key] for n in lrn] for k in seeds]))
        O.append(np.array([[T[r][k][key] for r in RULES] for k in seeds]))
        NC.append(np.array([T["nc"][k][key] for k in seeds]))
    return np.vstack(L), np.vstack(O), np.concatenate(NC), sorted(names_seen)


if __name__ == "__main__":
    L, O, NC, names = arrays()
    np.savez(__file__.replace("load.py", "x1.npz"), L=L, O=O, NC=NC)
    print("arms present:", len(names), names)
    print("shapes", L.shape, O.shape, NC.shape)
