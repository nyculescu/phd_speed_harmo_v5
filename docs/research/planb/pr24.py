"""Plan B counter traces (PR-24; planb.md §5, §7.2 C5, §7.3 G4(iv)). A traced run records, through libsumo getters only, every
vehicle each second and every braking step after the warm-up. The Plan B counters are then recounted from that record by code that
shares nothing with measure.py's counters; the definitions are planb.md §5's. A trace passes if the recount equals the row and the
traced row equals the untraced row on every key (V386: a trace must not change the run)."""
import json
import multiprocessing as mp
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

GROUPS = {"1": "1", "2": "2", "3a": "3a", "3": "3", "4a": "4a", "4": "4", "5": "5", "r": "ramp1", "rj": "ramp1", "r2": "ramp2", "rj2": "ramp2"}
ROBUST = {"car": -4.0, "alks": -4.0, "truck": -3.5}     # m/s²: a robust braking event peaks at or below this
BRAKE = -3.0
TTC, LC_S = 3.0, 5.0
STUCK_V, STUCK_RUN, STUCK_LEAD = 0.1, 300, 50.0
CONG_KMH, CONG_CELLS, DX, DT = 60.0, 6, 50.0, 10.0     # 6 cells of 50 m = 0.3 km
SKIP = {"cfg", "m_st_file"}
REL = 1e-9
SAMPLE_VEH = 3
_REC = None


def group(road: str) -> str:
    return "junction" if road.startswith(":") else GROUPS.get(road, "other")


def install() -> None:
    """Wrap the pack so that, after each of its reads, the same state is recorded through getters. Called once in a worker."""
    from v5b.fleet import measure
    init0, sec0, step0 = measure.Measure.__init__, measure.Measure.second, measure.Measure.vehicle_step

    def init(self, env, trucks, routes, length, dt):
        init0(self, env, trucks, routes, length, dt)
        global _REC
        pert = getattr(env, "pert", None)
        _REC = {"t0": env.warm, "t_end": env.t_end, "dt": dt, "trucks": set(trucks), "alks": set(env.alks_all),
                "route": {v.vid: r for v, r in zip(env.dem.veh, env.dem.route_of)}, "off": dict(self.off), "spec": pert.s if pert is not None else None,
                "capped": {x[1] for x in pert.log} if pert is not None and pert.kind == "truck_fixed" else set(), "sec": [], "brk": []}

    def second(self, ls, t):
        sec0(self, ls, t)
        vs = []
        for v in ls.vehicle.getIDList():
            lead = ls.vehicle.getLeader(v, 200.0)
            lid, gap = (lead[0], float(lead[1])) if lead and lead[0] else ("", 0.0)
            vs.append((v, ls.vehicle.getRoadID(v), ls.vehicle.getLaneID(v), ls.vehicle.getLanePosition(v), ls.vehicle.getSpeed(v), lid, gap,
                       ls.vehicle.getMinGap(v)))
        _REC["sec"].append((t, vs, list(ls.simulation.getPendingVehicles())))

    def vehicle_step(self, ls, v, a, s, f, t):
        step0(self, ls, v, a, s, f, t)
        x = ls.vehicle.getAcceleration(v)
        if x <= BRAKE:
            _REC["brk"].append((t, v, x, ls.vehicle.getRoadID(v), ls.vehicle.getLanePosition(v)))

    measure.Measure.__init__, measure.Measure.second, measure.Measure.vehicle_step = init, second, vehicle_step


def nest():
    return defaultdict(lambda: defaultdict(float))


def recount(rec: dict) -> dict:
    """The Plan B counters from a record, by planb.md §5's definitions."""
    from v5b.fleet.perturb import event_period
    t0, t_end = rec["t0"], rec["t_end"]
    nt, nm = int(np.ceil((t_end - t0) / DT)), int(np.ceil((t_end - t0) / 60.0))
    nx = int(np.ceil(rec["off"]["_end"] / DX))
    field, field_nc = np.zeros((2, nt, nx)), np.zeros((2, nt, nx))
    road_vs, road_dist, road_ttc = nest(), nest(), nest()
    pend_min = {k: np.zeros(nm) for k in ("ramp1", "ramp2", "main")}
    lane_idx, lc_t, run = {}, {}, defaultdict(int)
    stuck, ttc_all, ttc_lc, pending_end, vmax = set(), 0, 0, 0, 0.0
    for t, vs, pend in rec["sec"]:
        k = int((t - t0 - 1e-9) // DT)
        if not 0 <= k < nt:
            continue
        m = int((t - t0 - 1e-9) // 60.0)
        per = event_period(rec["spec"], t)
        speed = {v: s for v, _, _, _, s, *_ in vs}
        for v, road, lane, x, s, *_ in vs:
            g = group(road)
            road_vs[g][per] += 1
            road_dist[g][per] += s
            if v in rec["capped"]:
                vmax = max(vmax, s)
            if road.startswith(":"):
                continue
            o = rec["off"].get(road)
            if o is not None:
                j = min(int((o + x) // DX), nx - 1)
                for f, keep in ((field, True), (field_nc, v not in rec["capped"])):
                    if keep:
                        f[0, k, j] += s
                        f[1, k, j] += 1
            edge, li = lane.rsplit("_", 1)
            idx = int(li) - 1 if edge in ("3a", "4a") else int(li)
            if v in lane_idx and lane_idx[v] != idx:
                lc_t[v] = t
            lane_idx[v] = idx
        for v in pend:
            r = rec["route"].get(v)
            pend_min["ramp1" if r == "ramp" else "ramp2" if r == "ramp2" else "main"][m] += 1
            road_vs[f"pending_{r}"][per] += 1
        pending_end = len(pend)
        for v, road, lane, x, s, lid, gap, mingap in vs:
            ls_ = speed.get(lid) if lid else None
            if ls_ is not None and s > ls_ and (gap + mingap) / (s - ls_) < TTC:
                road_ttc[group(road)][per] += 1
                ttc_all += 1
                ttc_lc += t - lc_t.get(v, -1e9) <= LC_S or t - lc_t.get(lid, -1e9) <= LC_S
            behind_stopped = ls_ is not None and gap <= STUCK_LEAD and ls_ < STUCK_V
            if s < STUCK_V and not behind_stopped:
                run[v] += 1
                if run[v] >= STUCK_RUN:
                    stuck.add(v)
            else:
                run[v] = 0
    robust = nest()

    def shut(v, ev):
        c = "truck" if v in rec["trucks"] else "alks" if v in rec["alks"] else "car"
        if ev["peak"] <= ROBUST[c]:
            robust[group(ev["road"])][event_period(rec["spec"], ev["t"])] += 1

    cur = None     # (vehicle, event): samples are sorted by vehicle, then time, so one event is open at a time
    for t, v, a, road, x in sorted(rec["brk"], key=lambda r: (r[1], r[0])):
        if cur and cur[0] == v and t - cur[1]["last"] <= 1.5 * rec["dt"]:
            ev = cur[1]
            if a < ev["peak"]:
                ev.update(peak=a, t=t, road=road)
            ev["last"] = t
            continue
        if cur:
            shut(*cur)
        cur = (v, {"peak": a, "t": t, "road": road, "last": t})
    if cur:
        shut(*cur)
    out = {"m_road_vs": road_vs, "m_road_dist": road_dist, "m_road_ttc3": road_ttc, "m_robust_road": robust, "m_ttc3_all": ttc_all,
           "m_ttc3_lc": ttc_lc, "m_stuck_n": len(stuck), "m_pending_end": pending_end, "m_main_pending_min": pend_min["main"].tolist(),
           "m_minute.ramp1_pending": pend_min["ramp1"].tolist(), "m_minute.ramp2_pending": pend_min["ramp2"].tolist(), "m_capped_vmax": vmax}
    for tag, f in (("", field), ("_nc", field_nc)):
        out[f"m_cong_vs{tag}"], out[f"m_cong_run_s{tag}"] = congestion(f)
    return {k: {g: dict(x) for g, x in v.items()} if isinstance(v, dict) else v for k, v in out.items()}     # plain dicts cross the process boundary


def congestion(f: np.ndarray) -> tuple:
    """Vehicle-seconds in cells below 60 km/h, and the longest run of 10-s bins with at least 0.3 km congested."""
    occ = f[1] > 0
    v = np.full(f[0].shape, np.inf)
    v[occ] = 3.6 * f[0][occ] / f[1][occ]
    cong = v < CONG_KMH
    best = cur = 0
    for row in cong:
        cur = cur + 1 if row.sum() >= CONG_CELLS else 0
        best = max(best, cur)
    return float(f[1][cong].sum()), float(best * DT)


def flat(x, pre: str = "") -> dict:
    if isinstance(x, dict):
        return {k2: v2 for k, v in x.items() for k2, v2 in flat(v, f"{pre}{k}.").items()}
    return {pre[:-1]: x}


def close(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= REL * max(1.0, abs(float(a)), abs(float(b)))
    return a == b


def recount_differs(row: dict, rc: dict) -> list:
    """Keys whose recount differs from the row; nested counters compare leaf by leaf, a missing leaf reads as 0."""
    bad = []
    for k, v in rc.items():
        got = row["m_minute"][k.split(".", 1)[1]] if k.startswith("m_minute.") else row.get(k)
        if isinstance(v, dict):
            a, b = flat(json.loads(json.dumps(v))), flat(got or {})
            bad += [f"{k}.{x}" for x in sorted(set(a) | set(b)) if not close(a.get(x, 0), b.get(x, 0))]
        elif not close(v, got):
            bad.append(k)
    return bad


def row_differs(a: dict, b: dict) -> list:
    a, b = json.loads(json.dumps(a)), json.loads(json.dumps(b))
    return sorted(k for k in (set(a) | set(b)) - SKIP if a.get(k) != b.get(k))


def sample(rec: dict) -> dict:
    """The first few vehicles' per-second records, for reading what a count measures."""
    ids = []
    for _, vs, _ in rec["sec"]:
        ids += [v[0] for v in vs if v[0] not in ids]
        if len(ids) >= SAMPLE_VEH:
            break
    ids = set(ids[:SAMPLE_VEH])
    return {"vehicles": sorted(ids), "fields": ["t", "veh", "road", "lane", "pos", "speed", "leader", "gap", "min_gap"],
            "rows": [[t, *v] for t, vs, _ in rec["sec"] for v in vs if v[0] in ids]}


def traced_one(a: tuple) -> tuple:
    install()
    from v5b.fleet import plant_sweep as ps
    row = ps.run_one(a)
    return row, recount(_REC), sample(_REC), {"seconds": len(_REC["sec"]), "braking_steps": len(_REC["brk"])}


def run(jobs: list, workers: int, out: Path) -> dict:
    """jobs: [name, cfg, q, seed] with the pack on; cfg's measure folder must differ from the untraced run's. Returns
    {(name, seed): (row, recount, differing keys)} and writes each recount and sample to out."""
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        futs = {ex.submit(traced_one, (n, c, q, s, str(out / "rd"))): (n, s) for n, c, q, s in jobs}
        for f in as_completed(futs):
            n, s = futs[f]
            row, rc, smp, size = f.result()
            bad = recount_differs(row, rc)
            (out / f"{n.replace('|', '__')}__{s}.json").write_text(json.dumps({"name": n, "seed": s, "size": size, "recount_differs": bad,
                                                                                "recount": json.loads(json.dumps(rc)), "sample": smp}))
            res[(n, s)] = (row, rc, bad)
    return res
