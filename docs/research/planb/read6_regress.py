"""read6 v2's regression gate (read6_v2_spec.md §2): every field of v1's output is unchanged in v2's, bit for bit, except
cells.*.t2_counting_filter; v2's report-only map repeats v1's map on v1's measures.

usage: read6_regress.py V1.json V2.json    exit 0 if no difference, 1 otherwise (each difference printed)"""
import json
import sys

ALLOWED = ("t2_counting_filter",)
V1_MEASURES = ("delay", "cf", "flow", "robust_braking", "alks_past_limit", "b45_step", "b3_step", "ttt")


def norm(x):
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if hasattr(x, "item"):     # numpy scalars
        return x.item()
    return x


def walk(a, b, path: str, out: list) -> None:
    if isinstance(a, dict):
        if not isinstance(b, dict):
            out.append(f"{path}: dict in v1, {type(b).__name__} in v2")
            return
        for k, v in a.items():
            if path.startswith("cells.") and path.count(".") == 1 and k in ALLOWED:
                continue
            if k not in b:
                out.append(f"{path}.{k}: missing in v2")
            else:
                walk(v, b[k], f"{path}.{k}" if path else k, out)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            out.append(f"{path}: list differs in type or length")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif a != b or type(a) is not type(b):
        out.append(f"{path}: v1 {a!r}, v2 {b!r}")


def map_repeats(b: dict, out: list) -> None:
    """v2's map_report_only equals its own map on v1's measures, against every opponent of the map."""
    blocks = [(f"cells.{c}", r) for c, r in b.get("cells", {}).items()] + [("S", b.get("S", {}))]
    for path, r in blocks:
        mro = r.get("map_report_only")
        if mro is None:
            out.append(f"{path}.map_report_only: missing in v2")
            continue
        for o, row in r.get("map", {}).items():
            for m in V1_MEASURES:
                x, y = row[m], mro.get(o, {}).get(m, {})
                for k in ("effect", "ci95", "ci_m"):
                    if x.get(k) != y.get(k):
                        out.append(f"{path}.map_report_only.{o}.{m}.{k}: {y.get(k)!r} against map {x.get(k)!r}")


def diff(v1: dict, v2: dict) -> list:
    a, b = norm(v1), norm(v2)
    out = []
    walk(a, b, "", out)
    map_repeats(b, out)
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
