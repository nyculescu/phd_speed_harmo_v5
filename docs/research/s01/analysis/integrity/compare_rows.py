"""Task (1) and part of (5): every measured S0 row against the round-2 stored row with the same (name, q, seed).
Read only. Output: compare_rows.json and a printed aggregate."""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

D = Path("/home/catalin/work/phd/v5b1_runs")
M = D / "measure_s01_remote"
OUT = Path(__file__).resolve().parent
PAIRS = {"test": (M / "rows_test.jsonl", D / "round2/test/rows_6c49e7e.jsonl"),
         "band": (M / "rows_band.jsonl", D / "round2/band/rows_6c49e7e.jsonl")}
REL = 1e-9


def load(f):
    rows, dup = {}, Counter()
    for line in open(f):
        r = json.loads(line)
        k = (r["name"], r["q"], r["seed"])
        dup[k] += 1
        rows[k] = r
    return rows, {k: n for k, n in dup.items() if n > 1}


def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def nan_eq(a, b):
    return isnum(a) and isnum(b) and math.isnan(a) and math.isnan(b)


def reldiff(a, b):
    """Largest relative difference over a scalar or same-shaped nested numeric structure; None if shapes or types differ."""
    if isnum(a) and isnum(b):
        if a == b or nan_eq(a, b):
            return 0.0
        return abs(a - b) / max(abs(a), abs(b), 1e-300)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return None
        ds = [reldiff(x, y) for x, y in zip(a, b)]
        return None if any(d is None for d in ds) else max(ds, default=0.0)
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return None
        ds = [reldiff(a[k], b[k]) for k in a]
        return None if any(d is None for d in ds) else max(ds, default=0.0)
    return 0.0 if a == b else None


def deep_eq(a, b):
    if isnum(a) and isnum(b):
        return a == b or nan_eq(a, b)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(deep_eq(a[k], b[k]) for k in a)
    return a == b


def main():
    res = {}
    for ph, (fm, fs) in PAIRS.items():
        new, dn = load(fm)
        old, do = load(fs)
        only_new, only_old = sorted(set(new) - set(old)), sorted(set(old) - set(new))
        both = sorted(set(new) & set(old))
        field_exact, field_close, field_bad = Counter(), Counter(), Counter()
        type_kinds = defaultdict(set)
        mism = []
        presence = Counter()
        rows_exact = 0
        cfg_bad = []
        nan_fields = Counter()
        pack_keys = Counter()
        for k in both:
            a, b = new[k], old[k]
            ca = {x: y for x, y in a["cfg"].items() if x != "measure"}
            if not deep_eq(ca, b["cfg"]):
                cfg_bad.append(k)
            if "measure" not in a["cfg"] or "measure" in b["cfg"]:
                cfg_bad.append(("measure key", k))
            row_ok = True
            for f in sorted((set(a) | set(b)) - {"cfg"}):
                if f.startswith("m_") and f not in b:
                    pack_keys[f] += 1
                    continue
                if f in a and f in b:
                    va, vb = a[f], b[f]
                    type_kinds[f].add(type(vb).__name__)
                    for v in (va, vb):
                        if isnum(v) and math.isnan(v):
                            nan_fields[f] += 1
                    if deep_eq(va, vb):
                        field_exact[f] += 1
                        continue
                    row_ok = False
                    d = reldiff(va, vb)
                    if d is not None and d <= REL:
                        field_close[f] += 1
                    else:
                        field_bad[f] += 1
                    mism.append({"name": k[0], "q": k[1], "seed": k[2], "field": f, "rel": d,
                                 "new": va if isnum(va) else type(va).__name__, "old": vb if isnum(vb) else type(vb).__name__})
                else:
                    # A counter that never fired is absent; absence is equal to 0 only if the other side is 0.
                    present, other = (a, "new") if f in a else (b, "old")
                    v = present[f]
                    presence[(f, other)] += 1
                    if isnum(v) and v == 0:
                        field_exact[f + " (absent=0)"] += 1
                        continue
                    row_ok = False
                    field_bad[f + " (one side only)"] += 1
                    mism.append({"name": k[0], "q": k[1], "seed": k[2], "field": f, "rel": None, "only_in": other,
                                 "value": v if isnum(v) else type(v).__name__})
            rows_exact += row_ok
        arms_bad = Counter(m["name"].split("|")[1] for m in mism)
        res[ph] = {"rows_new": len(new), "rows_old": len(old), "dup_new": len(dn), "dup_old": len(do), "matched": len(both),
                   "only_new": [list(x) for x in only_new][:20], "n_only_new": len(only_new), "only_old": [list(x) for x in only_old][:20],
                   "n_only_old": len(only_old), "rows_all_shared_fields_exact": rows_exact,
                   "field_comparisons_exact": sum(field_exact.values()), "field_comparisons_close_1e-9": sum(field_close.values()),
                   "field_comparisons_bad": sum(field_bad.values()), "n_fields_compared": len(set(field_exact) | set(field_close) | set(field_bad)),
                   "fields_compared": sorted(set(field_exact) | set(field_close) | set(field_bad)),
                   "fields_bad": dict(field_bad), "fields_close": dict(field_close), "mismatches": mism[:500], "n_mismatches": len(mism),
                   "mismatch_arms": dict(arms_bad), "cfg_mismatch": [str(x) for x in cfg_bad], "nan_fields": dict(nan_fields),
                   "pack_keys": dict(pack_keys), "one_side_presence_zero": {f"{f}|{s}": n for (f, s), n in presence.items()}}
        r = res[ph]
        print(ph, "rows new/old", r["rows_new"], r["rows_old"], "dups", r["dup_new"], r["dup_old"], "matched", r["matched"],
              "only new/old", r["n_only_new"], r["n_only_old"])
        print("  rows with every shared field exact:", rows_exact, "of", len(both))
        print("  field comparisons exact / within 1e-9 / beyond:", r["field_comparisons_exact"], r["field_comparisons_close_1e-9"], r["field_comparisons_bad"])
        print("  distinct fields compared:", r["n_fields_compared"], " cfg mismatches:", len(cfg_bad), " NaN fields:", dict(nan_fields))
        print("  bad fields:", dict(field_bad))
        print("  close fields:", dict(field_close))
        print("  mismatch arms:", dict(arms_bad))
        print("  pack-only keys:", len(pack_keys), "min rows having one:", min(pack_keys.values()) if pack_keys else None)
    (OUT / "compare_rows.json").write_text(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
