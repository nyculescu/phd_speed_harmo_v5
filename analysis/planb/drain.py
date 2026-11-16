"""Plan B §7.3 G4(ii)(a,b), V486: the mean per-seed excess over S, in vehicles, at most 2 on each of six queues. It replaces the registered
median ratios, which had no working null; those stay as report-only rows. Results are keyed "arm|queue" so they can be stored as JSON."""
import numpy as np

LIMIT_VEH = 2.0
ARMS = ("nc", "p333")
KEYS = ("ramp1_queue", "ramp2_queue", "backlog")
GATE_SEEDS = tuple(range(7_480_010, 7_480_050))
WINDOW_MIN = range(20, 25)
LAST_MINUTE = range(24, 25)
EXCESS_LEVELS = (5.0, 10.0, 15.0)
BOOT_B = 20_000


def series_from_row(r: dict, minutes=WINDOW_MIN) -> dict:
    """One S2 row to its three queue means in vehicles over the given minutes."""
    m = r["m_minute"]
    ramp = lambda k: float(np.mean([m[k][i] / 60.0 for i in minutes]))
    pending = [(m["ramp1_pending"][i] + m["ramp2_pending"][i] + r["m_main_pending_min"][i]) / 60.0 for i in minutes]
    return {"ramp1_queue": ramp("ramp1_queue"), "ramp2_queue": ramp("ramp2_queue"), "backlog": float(np.mean(pending))}


def series_from_rows(rows_by_arm: dict, minutes=WINDOW_MIN) -> tuple:
    """{arm: rows in seed order} to ({arm: {key: array}}, seeds); every arm must hold the same seeds."""
    seeds = None
    out = {}
    for a in ARMS:
        rows = rows_by_arm[a]
        s = [r["seed"] for r in rows]
        if seeds is not None and s != seeds:
            raise ValueError("arms hold different seeds")
        seeds = s
        vals = [series_from_row(r, minutes) for r in rows]
        out[a] = {k: np.array([v[k] for v in vals]) for k in KEYS}
    return out, seeds


def _check_seeds(seeds_cell, seeds_steady) -> int:
    for seeds in (seeds_cell, seeds_steady):
        if list(seeds) != list(GATE_SEEDS):
            raise ValueError("rows must hold the 40 gate seeds, in seed order, once each")
    return len(GATE_SEEDS)


def _paired(cell, steady, n: int) -> tuple:
    c = np.asarray(cell, float)
    s = np.asarray(steady, float)
    if c.ndim != 1 or c.shape != s.shape or c.size != n or n == 0:
        raise ValueError("cell and steady must be 1-D series with one value per seed")
    if not (np.isfinite(c).all() and np.isfinite(s).all()):
        raise ValueError("non-finite queue value")
    return c, s


def drain_test(cell: dict, steady: dict, seeds_cell, seeds_steady, limit: float = LIMIT_VEH) -> dict:
    """Binding verdict. cell, steady: {arm: {key: per-seed window mean in vehicles}}, in seed order."""
    n = _check_seeds(seeds_cell, seeds_steady)
    excess = {}
    for a in ARMS:
        for k in KEYS:
            c, s = _paired(cell[a][k], steady[a][k], n)
            # Rounding keeps a value exactly at the limit from failing on float summation.
            excess[f"{a}|{k}"] = round(float(np.mean(c - s)), 9)
    return {"excess": excess, "pass": all(v <= limit for v in excess.values()), "limit": limit, "n": n}


def _boot_ci(d: np.ndarray, b: int, seed: int) -> tuple:
    rng = np.random.default_rng(seed)
    m = d[rng.integers(0, d.size, (b, d.size))].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def drain_report(cell: dict, steady: dict, seeds_cell, seeds_steady, last_cell: dict, last_steady: dict, *, surge: bool, b: int = BOOT_B, seed: int = 0) -> dict:
    """Report-only rows beside drain_test; nothing here may enter the verdict."""
    n = _check_seeds(seeds_cell, seeds_steady)
    out = {}
    for a in ARMS:
        for k in KEYS:
            c, s = _paired(cell[a][k], steady[a][k], n)
            lc, ls = _paired(last_cell[a][k], last_steady[a][k], n)
            d = c - s
            low, up = _boot_ci(d, b, seed)
            med_s = float(np.median(s))
            factor = 1.0 if (surge and k == "backlog") else 1.1
            out[f"{a}|{k}"] = {
                "mean_excess": float(d.mean()),
                "ci95": (low, up),
                "median_paired_excess": float(np.median(d)),
                "n_seeds_over": {x: int(np.sum(d > x)) for x in EXCESS_LEVELS},
                "largest_excess": float(d.max()),
                "last_minute_mean_excess": float((lc - ls).mean()),
                "old_cell_median": float(np.median(c)),
                "steady_median": med_s,
                "old_limit": factor * med_s,
                "old_pass": bool(np.median(c) <= factor * med_s),
            }
    return out


def read_drain(cell_rows: dict, steady_rows: dict, *, surge: bool, b: int = BOOT_B, seed: int = 0) -> dict:
    """{arm: rows in seed order} for the cell and for S, to the binding verdict and its report rows."""
    cell, seeds_cell = series_from_rows(cell_rows)
    steady, seeds_steady = series_from_rows(steady_rows)
    last_cell, _ = series_from_rows(cell_rows, LAST_MINUTE)
    last_steady, _ = series_from_rows(steady_rows, LAST_MINUTE)
    return {"verdict": drain_test(cell, steady, seeds_cell, seeds_steady),
            "report": drain_report(cell, steady, seeds_cell, seeds_steady, last_cell, last_steady, surge=surge, b=b, seed=seed)}
