"""Round 2 evaluation (protocol docs/local/research/protocols/round_2.md, revision 2, approved V454): seeds, arms, snapshots and the
multi-snapshot runner, in one place. The plant, conditions, statistic and the confirmatory-3 opponents are round 1's (common1)."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "analysis/round1")]
from common1 import (BAND_EVAL, H10, LEARNERS, OPPONENTS, PLANT, PRIMARY, Q, RULE, TRAINING_SLOWDOWNS, check_rows, incumbent, load,  # noqa: E402,F401
                     pt_cfg, rule_cfg)

PY = "/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python"
GIT = "/srv/shared/Workspace/phd/phd_speed_harmo_v5"     # the repository; frozen copies hold no .git
RUNS = Path("/home/catalin/work/phd/v5b1_runs")
OUT = RUNS / "round2"
R1 = RUNS / "baseline_v4/policies"     # v3w, round 1's control arm and this round's incumbent, stored read-only as baseline-v4 (D1)
R1_SUMS = ROOT / "docs/local/research/baseline_v4/SHA256SUMS"
R2 = RUNS / "round2_remote"

SEEDS_SMOKE = 7_419_899
SEEDS_3EX = range(7_440_740, 7_440_780)
SEEDS_VAL = range(7_440_800, 7_440_840)
SEEDS_TEST = range(7_440_840, 7_440_880)
SEEDS_BAND = range(7_440_880, 7_440_900)
KILL_SEEDS = (7_440_800, 7_440_801)     # ahead's importance KILL: traced re-runs of these validation seeds

# Trained candidates: prefix, branch commit (the code that trained them), policy folder.
TRAINED = {"2b": ("b", "5f9f5d3", R2 / "train_2b"), "1b": ("g", "5c10e6f", R2 / "train_1b"), "1d": ("k", "e8107fc", R2 / "train_1d"),
           "ahead": ("h", "66fa146", R2 / "train_ahead"), "rep": ("p", "08786f1", R2 / "train_rep")}
ORDER = ("2b", "1b", "1d", "ahead", "rep", "tail", "sw")     # the Arms table's order, the ranking's last tie-break
PREFIX = {**{k: v[0] for k, v in TRAINED.items()}, "tail": "t", "sw": "s", "v3w": "w", "inc": "d"}
CKS = (250, 500)
TAIL_CKS = (250, 300, 350, 400, 450, 500)
SW_X_FROM = 594.72
AHEAD_INPUTS = (16, 17)

E3T = json.load(open(HERE / "3e/final.json"))["pick"]["params"]     # g032i20 (V448)


def e3x(cell: str):
    """3E-X1 or 3E-X2's picked parameters, or None if its search found no configuration within the cap (or did not run)."""
    f = OUT / f"cma3e_{cell.lower()}" / "final.json"
    if not f.exists():
        return None
    p = json.load(open(f))["pick"]
    return p["params"] if p else None


def e3_rules(cell: str) -> dict:
    """The 3E rules of a cell: 3E-T in both cells, 3E-X only in its own."""
    out = {"3e": E3T}
    x = e3x(cell)
    if x is not None:
        out[f"3ex{cell[1]}"] = x
    return out


def opponents2(cells=PRIMARY) -> dict:
    """opponents.json with the 3E rules added to each cell's forms, so confirmatory 3's reading counts them."""
    o = copy.deepcopy(OPPONENTS)
    for c in cells:
        for n in e3_rules(c):
            o["cells"][c]["forms"][n] = n
    return o


def zone_cfg(params: list, cond: str, perturb: dict | None = None) -> dict:
    return rule_cfg({"zone_own_state": {"zones": params}}, cond, perturb)


def cond_env(cond: str, perturb: dict | None = None) -> dict:
    from common1 import COND
    x = perturb if perturb is not None else COND[cond]
    return {**H10, **({"perturb": x} if x else {})}


def tail_cfg(i: int, cond: str, perturb: dict | None = None) -> dict:
    return {**PLANT, "ctrl": {"pts": [str(R1 / f"C{i}_u{c}.pt") for c in TAIL_CKS], "env": cond_env(cond, perturb)}}


def sw_cfg(i: int, ck: int, cond: str, perturb: dict | None = None, x_from: float = SW_X_FROM) -> dict:
    sw = {"own_state": dict(OPPONENTS["ctrl"][RULE]["own_state"]), "pt": str(R1 / f"C{i}_u{ck}.pt"), "x_from": x_from}
    return {**PLANT, "ctrl": {"switch": sw, "env": cond_env(cond, perturb)}}


def policy(kind: str, i: int, ck) -> Path:
    if kind == "v3w":
        return R1 / f"C{i}_u{ck}.pt"
    if kind == "inc":
        return incumbent(i, f"u{ck}" if ck != "final" else "final")
    return TRAINED[kind][2] / f"C{i}_u{ck}.pt"


def snapshot_of(kind: str) -> str:
    """The commit an arm runs from: a trained candidate's own branch, everything else r2/eval's run commit."""
    return TRAINED[kind][1] if kind in TRAINED else "eval"


def freeze(commit: str, run_commit: str) -> Path:
    """A frozen copy of a commit under OUT/code_<sha>, with its sha in COMMIT. "eval" means r2/eval's run commit."""
    sha = run_commit if commit == "eval" else commit
    full = subprocess.run(["git", "-C", GIT, "rev-parse", sha], capture_output=True, text=True, check=True).stdout.strip()
    d = OUT / f"code_{full[:7]}"
    if not (d / "COMMIT").exists():
        d.mkdir(parents=True, exist_ok=True)
        tar = subprocess.run(["git", "-C", GIT, "archive", full], capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", str(d)], input=tar, check=True)
        (d / "COMMIT").write_text(full + "\n")
    return d


RUN_SNIPPET = """import json, sys
from pathlib import Path
from v5b2.fleet import plant_sweep as ps
a = json.load(open(sys.argv[1]))
ps.matrix(a["arms"], tuple(a["levels"]), a["seeds"], Path(a["out"]), a["workers"], a["rd"])
"""


def run_arms(groups: dict, levels, seeds, out: Path, workers: int, run_commit: str, log=print) -> list:
    """groups: snapshot ("eval" or a commit) -> {arm name: cfg}. Each snapshot runs in its own process from its frozen copy and writes
    out/rows_<sha7>.jsonl. Returns the rows files. The chain stops on a failed arm (plant_sweep raises) or a commit mismatch."""
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for snap, arms in groups.items():
        if not arms:
            continue
        code = freeze(snap, run_commit)
        sha = (code / "COMMIT").read_text().strip()[:7]
        f = out / f"rows_{sha}.jsonl"
        if f.exists():     # a hard crash can leave a partial last line, which the runner's resume cannot read
            b = f.read_bytes()
            if b and not b.endswith(b"\n"):
                f.write_bytes(b[:b.rfind(b"\n") + 1])
                log(f"dropped a partial last line of {f.name}")
        job = out / f"job_{sha}.json"
        job.write_text(json.dumps({"arms": arms, "levels": list(levels), "seeds": list(seeds), "out": str(f), "workers": workers, "rd": str(out / "rd")}))
        log(f"snapshot {sha}: {len(arms)} arms")
        with open(out / "snapshots.txt", "a") as h:
            h.write(f"{sha} {len(arms)} arms {f.name}\n")
        env = {**os.environ, "PYTHONPATH": str(code), "OMP_NUM_THREADS": "1"}
        env.pop("SUMO_HOME", None)
        subprocess.run([PY, "-c", RUN_SNIPPET, str(job)], cwd=str(code), env=env, check=True)
        files.append(f)
    return files


def load_union(files, n_seeds: int, expect: set) -> dict:
    """The rows of every snapshot as one table; every expected arm present, complete and unique across files."""
    T, seen = {}, {}
    for f in files:
        part = load(f)
        for k in part:
            if k in seen:
                raise SystemExit(f"arm {k} in both {seen[k]} and {f}")
            seen[k] = f
        T |= part
    names = {k[0] for k in T}
    if expect - names:
        raise SystemExit(f"arms missing from the rows: {sorted(expect - names)[:8]}")
    check_rows(T, n_seeds)
    return T


def cand_cfg(kind: str, i: int, ck, cond: str, perturb: dict | None = None) -> dict:
    """One learner of a candidate, v3w or baseline-v3 (kind "inc") in a cell."""
    if kind == "tail":
        return tail_cfg(i, cond, perturb)
    if kind == "sw":
        return sw_cfg(i, ck, cond, perturb)
    return pt_cfg(policy(kind, i, ck), cond, perturb)


def rule_arms(cell: str, cond: str, perturb: dict | None = None, which=None) -> dict:
    """Confirmatory 3's 12 rule arms, the 3E rules of the cell and no control; `which` limits them to the names given."""
    a = {n: rule_cfg(k, cond, perturb) for n, k in {**OPPONENTS["ctrl"], "nc": {}}.items()}
    a |= {n: zone_cfg(p, cond, perturb) for n, p in e3_rules(cell if cell in PRIMARY else "X1").items() if n == "3e" or cell in PRIMARY}
    return {f"{cell}|{n}": x for n, x in a.items() if which is None or n in which}
