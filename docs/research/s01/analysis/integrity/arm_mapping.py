"""Task (4): the arm-name mapping from the run code (measure2.groups, decide2.names, test2.plan) and validation.json, checked
against the job files' policy paths. Read only; run with python -I -B so no bytecode is written to the worktree."""
import json
import sys
from pathlib import Path

W = Path("/home/catalin/work/phd/wt/r2-metrics")
R2 = W / "docs/research/round2"
sys.path[:0] = [str(W), str(R2), str(W / "docs/research/round1")]
import measure2  # noqa: E402
import decide2  # noqa: E402
import common2e  # noqa: E402

RUNS = Path("/home/catalin/work/phd/v5b1_runs")
v = json.load(open(RUNS / "round2/val/validation.json"))
G = measure2.groups(RUNS / "round2")
print("measure2.groups:", G)
print("validation finalists:", v["finalists"], " chosen v3w:", v["chosen"]["v3w"], " chosen sw:", v["chosen"]["sw"])
print("PREFIX:", common2e.PREFIX, " R1 (v3w policies):", common2e.R1)
jt = json.load(open(RUNS / "measure_s01_remote/job_test.json"))
jb = json.load(open(RUNS / "measure_s01_remote/job_band.json"))


def src(c):
    x = c.get("ctrl", {})
    if "pt" in x:
        return "pt:" + "/".join(Path(x["pt"]).parts[-3:])
    if "pts" in x:
        return "pts:" + ",".join("/".join(Path(p).parts[-2:]) for p in x["pts"])
    if "switch" in x:
        return "switch:" + "/".join(Path(x["switch"]["pt"]).parts[-3:]) + f" x_from={x['switch']['x_from']} own_state={x['switch']['own_state']}"
    return "rule:" + ",".join(k for k in x if k != "env") if x else "no control"


out = {"groups": G, "finalists": v["finalists"], "chosen": v["chosen"], "paths": {}}
for g, names in G.items():
    for n in names:
        for cell in ("X1", "X2"):
            out["paths"][f"{cell}|{n}"] = src(jt["arms"][f"{cell}|{n}"])
        out["paths"][f"B|{n}"] = src(jb["arms"][f"B|{n}"])
    print(f"\n{g}:")
    for n in names:
        print(f"  {n}: X1 {out['paths'][f'X1|{n}']}\n      X2 same source: {out['paths'][f'X2|{n}'] == out['paths'][f'X1|{n}']}; B same source: {out['paths'][f'B|{n}'] == out['paths'][f'X1|{n}']}")
rules = sorted({k.split('|')[1] for k in jt["arms"]} - {n for x in G.values() for n in x})
print("\nrule arms in test:", rules)
print("rule arms in band:", sorted({k.split('|')[1] for k in jb["arms"]} - {n for x in G.values() for n in x}))
print("rule sources:", {r: src(jt["arms"].get(f"X1|{r}") or jt["arms"][f"X2|{r}"]) for r in rules})
print("3ex1 in X2:", "X2|3ex1" in jt["arms"], " 3ex2 in X1:", "X1|3ex2" in jt["arms"])
(Path(__file__).parent / "arm_mapping.json").write_text(json.dumps(out, indent=1))
