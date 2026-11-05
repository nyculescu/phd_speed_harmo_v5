"""The collapse check of the protocol, and the settings each learner really ran with. usage: collapse.py train_dir env.json. Exit 1 if settings differ or more than one learner fails."""
import json
import sys
from pathlib import Path

import numpy as np

from common import ENVS, FIRST_WORKER, LEARNERS, LEVELS, NET_SEED, UPDATES
from v5b.fleet import c_train as ct


def stat(rows: list) -> tuple:
    """Rows of one attempt, one per update, in order."""
    r = np.array([x["r"] for x in rows])
    return abs(r[400:500].mean() - r[300:400].mean()), r[400:500].mean() - r[:50].mean()


def collapsed(rows: list) -> bool:
    a, b = stat(rows)
    return not (a <= 0.03 and b >= 0.0)


def settings_differ(cfg: dict, i: int, env: dict) -> list:
    want = {"learner": i, "updates": UPDATES, "n_envs": ENVS, "gamma": 0.933, "lam": 0.967, "levels": list(LEVELS), "seed": NET_SEED + i, "workers": [FIRST_WORKER + i * ENVS + k for k in range(ENVS)], "env": {**ct.ENV, **env}}
    return [k for k, v in want.items() if cfg.get(k) != v]


if __name__ == "__main__":
    d, env = Path(sys.argv[1]), json.load(open(sys.argv[2]))
    failed, wrong = [], []
    for i in range(LEARNERS):
        rows = [json.loads(x) for x in open(d / f"C{i}_updates.jsonl")]
        assert [x["u"] for x in rows] == list(range(UPDATES)), f"C{i}: updates are not 0-{UPDATES - 1} once each"
        a, b = stat(rows)
        ok = not collapsed(rows)
        bad = settings_differ(json.load(open(d / f"C{i}_config.json")), i, env)
        print(f"C{i}: last two blocks differ {a:.4f}, gain on the start {b:+.4f}, {'ok' if ok else 'FAILS'}; settings {'as pinned' if not bad else bad}", flush=True)
        eps = [json.loads(x) for x in open(d / f"C{i}_episodes.jsonl")]
        for lab, part in (("first 150 episodes", eps[:150]), ("last 150", eps[-150:])):
            lv = np.sum([e["lv"] for e in part], axis=0).reshape(-1, 4).sum(axis=0)
            print(f"  level shares, {lab}: {np.round(lv / lv.sum(), 3).tolist()}", flush=True)
        failed += [] if ok else [i]
        wrong += [i] if bad else []
    sys.exit(1 if wrong or len(failed) > 1 else 0)
