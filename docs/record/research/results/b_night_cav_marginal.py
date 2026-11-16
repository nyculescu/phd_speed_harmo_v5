"""Per-vehicle values by own level and zone, each ALKS given one random level for its whole trip (V289): what an independent learner sees, free of the link between level and position."""
import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from v5b.fleet import b_env as be


def one(a):
    q, s = a
    env = be.make(cav=True, decision=5.0, alks_asl=0.5, ref_delay=True, share=0.5, levels=(q,), seeds=[s], run_dir=sys.argv[1], report_net=True)
    rng = np.random.default_rng(s)
    agg = np.zeros((3, 4, 8))
    o, _ = env.reset()
    sec = env._second

    def second():
        r = sec()
        for v, x in env.stats.items():
            if v in env.on:
                agg[env._zone(v), env.lvl.get(v, 0)] += [1, *x]
        return r
    env._second = second
    fixed = {}
    while True:
        for v in o[0]:
            if v not in fixed:
                fixed[v] = env.lvl[v] = int(rng.integers(0, 4))
        o, _, _, tr, _ = env.step({})
        if tr:
            break
    env.close()
    return q, agg


if __name__ == "__main__":
    with ProcessPoolExecutor(9, mp_context=mp.get_context("spawn")) as ex:
        res = list(ex.map(one, [(q, s) for q in (4090.0, 4600.0, 5300.0) for s in range(7_419_950, 7_419_960)]))
    A = {}
    for q, a in res:
        A[q] = A.get(q, 0) + a
    for q in sorted(A):
        for z, name in enumerate(("up", "merge", "down")):
            for lev in range(4):
                m = A[q][z, lev, 1:] / max(A[q][z, lev, 0], 1)
                sp = 0.5 * (m[0] + m[1]) / be.fl.LIMIT
                safe = be.W_CAV_TTC * (m[3] + 0.5 * m[4] + m[6] + 0.5 * m[5])
                print(f"{q:g} {name} L{lev} speed {sp:.3f} flow {m[2] / be.Q_REF:.3f} safety {safe:.3f} net {sp + be.W_CAV_FLOW * m[2] / be.Q_REF - safe:.3f}")
