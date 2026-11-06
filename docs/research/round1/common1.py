"""Round 1 (protocol docs/research/protocols/round_1.md): candidates, seeds, arms and the statistic, in one place.
The plant, conditions, opponents and statistic are confirmatory 3's, imported from docs/research/conf3/common.py."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT / "docs/research/conf3"))
from common import COND, LEVELS, PLANT, PRIMARY, Q, H10, check_rows, load, med, paired_median, raw, val, collisions, effect  # noqa: E402,F401

BASE = ROOT / "docs/research/baseline_v3"
OPPONENTS = json.load(open(BASE / "opponents.json"))
ENV_V3 = json.load(open(BASE / "env.json"))
INCUMBENT = Path("/home/catalin/work/phd/v5b1_runs/baseline_v3/conf3/train")     # read-only copy, checkpoints u50-u500 and final
RULE = "os1_15_10"

SEEDS_SMOKE = 7_419_899
SEEDS_STAGE0A = range(7_440_300, 7_440_320)
SEEDS_STAGE0B = range(7_440_340, 7_440_370)
SEEDS_VAL = range(7_440_400, 7_440_440)
SEEDS_TEST = range(7_440_500, 7_440_540)
PER_WORKER, FIRST_WORKER, LEARNERS, ENVS, UPDATES, NET_SEED = 520, 9, 5, 3, 500, 20261205
SEED0 = 7_464_000 - FIRST_WORKER * PER_WORKER     # worker 9 starts at 7,464,000
TRAIN_FIRST, TRAIN_LAST = 7_464_000, 7_471_799
GAMMA, LAM = 0.933, 0.967
CHECKPOINTS = tuple(range(50, 501, 50))

# What each candidate changes on top of baseline-v3's env.json; 2C also passes --lagr with d_ref from stage 0b.
CANDIDATES = {"res": {"base_rule": dict(OPPONENTS["ctrl"][RULE]["own_state"])},
              "attr": {"reward_mode": "attr", "w_flow": 0.0},
              "lagr": {"reward_mode": "lagr"}}
ORDER = ("res", "attr", "lagr")
PREFIX = {"res": "r", "attr": "a", "lagr": "l", "inc": "d"}


def env_for(kind: str) -> dict:
    """Training environment of a candidate: baseline-v3's, with this round's seeds and the candidate's options."""
    e = {**ENV_V3, "seed0": SEED0, "seeds_per_worker": PER_WORKER, **CANDIDATES[kind]}
    return e


def pt_cfg(path: str, cond: str, perturb: dict | None = None) -> dict:
    """A policy arm. The policy's own environment options travel inside its checkpoint (c_train.act_env)."""
    x = perturb if perturb is not None else COND[cond]
    return {**PLANT, "ctrl": {"pt": str(path), "env": {**H10, **({"perturb": x} if x else {})}}}


TRAINING_SLOWDOWNS = {"kind": "random"}


def rule_cfg(ctrl: dict, cond: str, perturb: dict | None = None) -> dict:
    """A rule or no-control arm; perturb overrides the condition (stage 0b uses training's random slowdowns)."""
    x = perturb if perturb is not None else COND[cond]
    if not ctrl:
        return {**PLANT, **({"ctrl": {"env": {"perturb": x}}} if x else {})}
    return {**PLANT, "ctrl": {**ctrl, "env": {**H10, **({"perturb": x} if x else {})}}}


def incumbent(i: int, ck: str) -> Path:
    return INCUMBENT / f"C{i}_{ck}.pt"


def arm_mean(T: dict, names: list, q: float = Q) -> dict:
    """Per seed, the mean over the learners of every numeric key: one arm of 5 learners."""
    rows = [T[(n, q)] for n in names]
    seeds = sorted(set.intersection(*(set(r) for r in rows)))
    keys = {k for r in rows for s in seeds for k, v in r[s].items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    return {s: {"seed": s, **{k: sum(val(r[s], k) for r in rows) / len(rows) for k in keys}} for s in seeds}
