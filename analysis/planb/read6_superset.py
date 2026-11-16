"""A newer read6 v2.x output keeps every field of an older one (read6_v2_spec.md amendment 5: v2.3 equals v2.2 on every v2.2 field):
each leaf of OLD is in NEW with the same type and value (floats by repr, so NaN equals NaN and 0.0 differs from -0.0); NEW may add keys;
report_version may differ.

usage: read6_superset.py OLD.json NEW.json    exit 0 if NEW holds OLD, 1 otherwise (each difference printed)"""
import json
import sys


def walk(a, b, path: str, out: list) -> None:
    if isinstance(a, dict):
        if not isinstance(b, dict):
            out.append(f"{path}: dict in old, {type(b).__name__} in new")
            return
        for k, v in a.items():
            p = f"{path}.{k}" if path else k
            if p == "report_version":
                continue
            if k not in b:
                out.append(f"{p}: missing in new")
            else:
                walk(v, b[k], p, out)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            out.append(f"{path}: list differs in type or length")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif type(a) is not type(b) or repr(a) != repr(b):
        out.append(f"{path}: old {a!r}, new {b!r}")


def main(argv: list) -> int:
    a, b = (json.load(open(p)) for p in argv[:2])
    out = []
    walk(a, b, "", out)
    for x in out:
        print(x)
    print("superset:", "PASS, every older field unchanged" if not out else f"FAIL, {len(out)} differences")
    return 0 if not out else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
