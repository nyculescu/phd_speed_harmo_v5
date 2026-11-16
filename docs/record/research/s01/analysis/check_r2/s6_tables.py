"""Parse the r3 draft's section 6.1-6.3 tables and recompute every cell (positive = v3w better)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib2 import *

T = load()
md = (HERE.parent / "draft_s01_result_r3.md").read_text().splitlines()
ALIAS = {"no control": "nc", "3E-T": "3e", "3E-X1": "3ex1", "3E-X2": "3ex2"}
NUM = r"([+−-]?\d+(?:\.\d+)?)"
TRI = re.compile(NUM + r"\s*\[" + NUM + r",\s*" + NUM + r"\]")


def fl(s):
    return float(s.replace("−", "-").replace("+", ""))


def tri(s):
    m = TRI.search(s)
    return tuple(fl(x) for x in m.groups()) if m else None


def check(cell, q, opp, key, want, sign=-1):
    got = eff(arm(T, cell, "v3w", q, key), arm(T, cell, ALIAS.get(opp, opp), q, key), sign)
    ok = all(abs(round(g, 1) - w) <= 0.051 for g, w in zip(got[:3], want))
    return ok, got


def section(start, stop):
    i = next(n for n, l in enumerate(md) if l.startswith(start))
    j = next(n for n, l in enumerate(md) if n > i and l.startswith(stop))
    return md[i:j]


n = bad = 0
for head, nxt, cell in (("### 6.1", "### 6.2", "X1"), ("### 6.2", "### 6.3", "X2")):
    for l in section(head, nxt):
        if not l.startswith("| ") or l.startswith("| Opponent") or l.startswith("|---"):
            continue
        c = [x.strip() for x in l.strip("|").split("|")]
        for key, txt in (("all_delay", c[1]), ("ttc_net", c[2])):
            w = tri(txt)
            ok, got = check(cell, 5300, c[0], key, w)
            n += 1
            if not ok:
                bad += 1
                print("MISMATCH", cell, c[0], key, w, f1(got, 2))
print("6.1/6.2 cells", n, "mismatch", bad)

n = bad = 0
for l in section("### 6.3", "Source [map_all:F3"):
    if not l.startswith("| ") or l.startswith("| Level") or l.startswith("|---"):
        continue
    c = [x.strip() for x in l.strip("|").split("|")]
    q = int(c[0].replace(",", "").replace("†", ""))
    key = "all_delay" if c[1] == "delay" else "ttc_net"
    for opp, txt in zip(("p333", "os1_15_10", "3E-T", "no control"), c[2:6]):
        w = tri(txt)
        if w is None:
            continue
        ok, got = check("B", q, opp, key, w)
        n += 1
        if not ok:
            bad += 1
            print("MISMATCH B", q, opp, key, w, f1(got, 2))
print("6.3 cells", n, "mismatch", bad)
