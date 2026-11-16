"""Task (3) and the pack's own consistency on every run: st/*.npz present and well formed; the pack's sums against the plant's
counters (measure2.checks, reimplemented) on all 5,560 rows; summary_rows_*.json recomputed from rows + fields with the run code's
summary() and compared; None/NaN per summary metric and arm; seeds kept per report panel. Read only (imports the r2-metrics
worktree with -B, so no bytecode is written there)."""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

W = Path("/home/catalin/work/phd/wt/r2-metrics")
sys.path[:0] = [str(W)]
from v5b.fleet import measure as me  # noqa: E402

M = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(__file__).resolve().parent
C = me.CLASSES


def group(arm):
    if arm[0] == "w" and "u" in arm:
        return "v3w"
    if arm[0] == "t" and arm[1:].isdigit():
        return "tail"
    if arm[0] == "s" and "u" in arm:
        return "sw"
    if arm[0] == "d" and "u" in arm:
        return "baseline-v3(d)"
    return arm


def checks(row, field):
    n = sum(row[f"m_n_{c}"] for c in C)
    out = {
        "speed_bins_sum_eq_steps": all(sum(row[f"m_vh_{c}"]) == row[f"m_n_{c}"] == sum(row[f"m_ah_{c}"]) for c in C),
        "dist_eq_dist_step": bool(np.isclose(sum(row[f"m_dist_m_{c}"] for c in C), row["dist_step"], rtol=1e-9)),
        "fuel_eq_fuel_step": bool(np.isclose(sum(row[f"m_fuel_mg_{c}"] for c in C), row["fuel_step"], rtol=1e-9)),
        "event_s_eq_b3_step": bool(np.isclose(sum(row[f"m_event_s_{c}"] for c in C), row.get("b3_step", 0.0), rtol=1e-9, atol=1e-6)),
        "events_ge45_le_b45_steps": bool(sum(np.asarray(row[f"m_peak_{c}"])[3:].sum() for c in C) <= round(row.get("b45_step", 0.0) / 0.1) + 1),
        "st_seconds_le_vs": float(field["n"].sum()) <= row["vs"],
        "st_covers_mainline": float(field["n"].sum()) > 0.5 * row["vs"],
        "m2_out_near_passed": abs(sum(row["m_minute"]["m2_out"]) - row["passed"]) <= max(10, 0.01 * row["passed"]),
    }
    if "m_dec_level_s" in row and len(row.get("lv", [])) == 12:
        out["level_s_eq_env_lv"] = row["m_dec_level_s"] == np.asarray(row["lv"]).reshape(3, 4).sum(0).tolist()
        out["decisions_present"] = row["m_dec_totals"].get("asked", 0) > 0
    a9 = sum(np.asarray(row["m_peak_alks"])[7:])
    out["alks_ge9_event_if_full"] = bool(a9 > 0 or row.get("alks_full_events", 0.0) == 0)
    return out


def bad_value(x):
    return x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))


def flat(d, p=""):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from flat(v, f"{p}.{k}" if p else str(k))
    elif isinstance(d, list):
        if not d:
            yield p + "[]", "EMPTY"
        for i, v in enumerate(d):
            yield from flat(v, f"{p}[{i}]")
    else:
        yield p, d


def same(a, b):
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a == b or abs(a - b) <= 1e-12 * max(abs(a), abs(b))
    return a == b


def main():
    rep = {}
    files = {p.name for p in (M / "st").iterdir()}
    used = Counter()
    for ph in ("test", "band", "s1"):
        S = json.load(open(M / f"summary_rows_{ph}.json"))
        fails, shape_bad, nan_field, neg_field, missing_file = Counter(), [], 0, 0, []
        sum_mismatch, sum_missing, rows_n = [], 0, 0
        none_ct = defaultdict(Counter)     # path -> (group, q) -> count
        tot = Counter()
        p333_levels, p333_tot = [], Counter()
        keys_rows = set()
        for line in open(M / f"rows_{ph}.jsonl"):
            r = json.loads(line)
            rows_n += 1
            nm, q, s = r["name"], r["q"], r["seed"]
            keys_rows.add(f"{nm}|{q:.0f}|{s}")
            f = r["m_st_file"]
            used[f] += 1
            if f not in files:
                missing_file.append(f)
                continue
            z = np.load(M / "st" / f)
            v, n = z["v"], z["n"]
            if list(v.shape) != list(r["m_st_shape"]) or list(n.shape) != list(r["m_st_shape"]):
                shape_bad.append(f)
            nan_field += int(not np.isfinite(v).all() or not np.isfinite(n).all())
            neg_field += int((n < 0).any() or (v < 0).any())
            for k, ok in checks(r, {"v": v, "n": n}).items():
                if not ok:
                    fails[(k, group(nm.split("|")[1]))] += 1
            if nm.endswith("|p333"):
                ls_ = np.asarray(r["m_dec_level_s"], float)
                p333_levels.append(ls_ / ls_.sum())
                for k2, v2 in r["m_dec_totals"].items():
                    p333_tot[k2] += v2
            stored = S.get(f"{nm}|{q:.0f}", {}).get(str(s))
            if stored is None:
                sum_missing += 1
                continue
            new = json.loads(json.dumps(me.summary(r, {"v": v, "n": n}), default=float))
            if not same(new, stored):
                diff = [k for k in set(new) | set(stored) if not same(new.get(k), stored.get(k))]
                sum_mismatch.append((nm, q, s, diff[:5]))
            g = (group(nm.split("|")[1]), nm.split("|")[0], q)
            tot[g] += 1
            for path, x in flat(stored):
                if x == "EMPTY" or bad_value(x):
                    none_ct[path][g] += 1
        n_sum = sum(len(v) for v in S.values())
        res = {"rows": rows_n, "summary_entries": n_sum, "summary_names": len(S), "summary_missing_for_row": sum_missing,
               "summary_mismatch_vs_recomputed": len(sum_mismatch), "mismatch_examples": sum_mismatch[:10],
               "missing_st_files": len(missing_file), "st_shape_bad": len(shape_bad), "st_nonfinite": nan_field, "st_negative": neg_field,
               "check_failures": {f"{k}|{g}": c for (k, g), c in fails.items()},
               "none_nan_by_metric": {p: {f"{g[0]}|{g[1]}|{g[2]:.0f}": f"{c}/{tot[g]}" for g, c in sorted(d.items())} for p, d in sorted(none_ct.items())}}
        if p333_levels:
            res["p333_level_share_mean"] = np.mean(p333_levels, 0).round(4).tolist()
            res["p333_dec_totals"] = dict(p333_tot)
        rep[ph] = res
        print(f"== {ph}: rows {rows_n}, summary entries {n_sum} ({len(S)} name|q), summary missing for a row {sum_missing}, "
              f"summary != recomputed {len(sum_mismatch)}, st missing {len(missing_file)}, shape bad {len(shape_bad)}, non-finite fields {nan_field}, negative {neg_field}")
        print("  pack check failures (check|group: runs):", res["check_failures"] or "none")
        if sum_mismatch:
            print("  summary mismatch examples:", sum_mismatch[:5])
        print("  summary paths with None/NaN/inf/empty:")
        for p, d in res["none_nan_by_metric"].items():
            items = list(d.items())
            print(f"    {p}: {len(items)} arm-levels; " + ", ".join(f"{k} {v}" for k, v in items[:8]) + (" ..." if len(items) > 8 else ""))
        if p333_levels:
            print("  p333 V2V-on level-second shares (levels 0-3), mean over runs:", res["p333_level_share_mean"], " decision totals:", res["p333_dec_totals"])
    dup = {f: c for f, c in used.items() if c > 1}
    rep["st_files"] = {"files_in_st": len(files), "referenced": len(used), "referenced_twice": len(dup), "orphans": len(files - set(used))}
    print("st files:", rep["st_files"])
    (OUT / "pack_checks.json").write_text(json.dumps(rep, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
