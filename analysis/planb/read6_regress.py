"""read6 v2's regression gate (read6_v2_spec.md §2): every field of v1's output is unchanged in v2's, bit for bit, except
cells.*.t2_counting_filter, which must equal v2's `v1_value`; a cell's v1 `pr28` of None that v2 fills; and a resilience R (and its %
of no control's loss) that v2 hides because that opponent's own null failed (planb.md:462), shown exactly as "statistic failed its
null" (and None). A key v2 adds must be one the spec lists (NEW_KEYS). v2's report-only map repeats v1's map on v1's measures, and a
block that is not read (by v1's record) carries a report-only status and no verdict (amendments 3 and 5).

usage: read6_regress.py V1.json V2.json    exit 0 if no difference, 1 otherwise (each difference printed)"""
import json
import re
import sys

ALLOWED = ("t2_counting_filter",)
FAILED = "statistic failed its null"
HIDDEN = {"R": FAILED, "pct_of_nc_loss": None}
V1_MEASURES = ("delay", "cf", "flow", "robust_braking", "alks_past_limit", "b45_step", "b3_step", "ttt")
NEW_KEYS = (r"report_version", r"provenance", r"defaults_hit", r"counters_absent_read_as_zero", r"absent_read_as_none", r"space_time",
            r"S\.map_report_only", r"cells\.[^.]+\.(closest|d4|braking_clause|resilience|cf_resilience|map_report_only)",
            r"cells\.[^.]+\.resilience\.status")


def norm(x):
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if hasattr(x, "item"):     # numpy scalars
        return x.item()
    return x


def same(a, b) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, float):
        return repr(a) == repr(b)     # NaN equals NaN; 0.0 differs from -0.0
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def hidden(b: dict) -> bool:
    """That opponent's own null failed; read6.main writes the numpy bool as 0.0."""
    return b.get("null_ok") is not None and not b["null_ok"]


def walk(a, b, path: str, out: list) -> None:
    join = lambda k: f"{path}.{k}" if path else k
    at_cell = path.startswith("cells.") and path.count(".") == 1
    if isinstance(a, dict):
        if not isinstance(b, dict):
            out.append(f"{path}: dict in v1, {type(b).__name__} in v2")
            return
        for k, v in a.items():
            if at_cell and k in ALLOWED:
                if isinstance(b.get(k), dict) and "v1_value" in b[k]:
                    walk(v, b[k]["v1_value"], f"{join(k)}.v1_value", out)
                else:
                    out.append(f"{join(k)}.v1_value: missing in v2")
                continue
            if at_cell and k == "pr28" and v is None and k in b:
                continue
            if (".resilience.per_opponent." in f"{path}." and k in HIDDEN and hidden(b) and k in b and same(b[k], HIDDEN[k])):
                continue
            if k not in b:
                out.append(f"{join(k)}: missing in v2")
            else:
                walk(v, b[k], join(k), out)
        for k in sorted(set(b) - set(a)):
            if not any(re.fullmatch(p, join(k)) for p in NEW_KEYS):
                out.append(f"{join(k)}: new in v2")
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            out.append(f"{path}: list differs in type or length")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif not same(a, b):
        out.append(f"{path}: v1 {a!r}, v2 {b!r}")


def map_repeats(b: dict, out: list) -> None:
    """v2's map_report_only equals its own map on v1's measures, against every opponent of the map, by same()."""
    blocks = [(f"cells.{c}", r) for c, r in b.get("cells", {}).items()] + [("S", b.get("S", {}))]
    for path, r in blocks:
        mro = r.get("map_report_only")
        if mro is None:
            out.append(f"{path}.map_report_only: missing in v2")
            continue
        for o, row in r.get("map", {}).items():
            for m in V1_MEASURES:
                if m not in mro.get(o, {}):
                    out.append(f"{path}.map_report_only.{o}.{m}: missing in map_report_only")
                    continue
                x, y = row[m], mro[o][m]
                for k in ("effect", "ci95", "ci_m"):
                    if not same(x.get(k), y.get(k)):
                        out.append(f"{path}.map_report_only.{o}.{m}.{k}: {y.get(k)!r} against map {x.get(k)!r}")


VERDICT_KEYS = ("passes", "reading", "pass", "verdict")


def no_verdict(a: dict, b: dict, out: list) -> None:
    """Amendments 3 and 5: a resilience block that v1 does not have (v1 writes one only where W's R is read), and close-following
    resilience always, must carry a status starting "report-only" and no verdict key. Whether a block is read is taken from v1, not
    from the output under test."""
    for c, r in b.get("cells", {}).items():
        v1_reads = "resilience" in a.get("cells", {}).get(c, {})
        for k in ("cf_resilience",) + (() if v1_reads else ("resilience",)):
            blk = r.get(k)
            if not isinstance(blk, dict):
                continue
            if not str(blk.get("status", "")).startswith("report-only"):
                out.append(f"cells.{c}.{k}.status: {blk.get('status')!r} in a block that is not read")
            for v in VERDICT_KEYS:
                if v in blk:
                    out.append(f"cells.{c}.{k}.{v}: a verdict in a block that is not read")


def diff(v1: dict, v2: dict) -> list:
    a, b = norm(v1), norm(v2)
    out = []
    walk(a, b, "", out)
    map_repeats(b, out)
    no_verdict(a, b, out)
    return out


def main(argv: list) -> int:
    a, b = (json.load(open(p)) for p in argv[:2])
    d = diff(a, b)
    for x in d:
        print(x)
    print("regression:", "PASS, v1's fields unchanged" if not d else f"FAIL, {len(d)} differences")
    return 0 if not d else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
