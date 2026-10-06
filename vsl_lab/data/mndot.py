"""MnDOT (Twin Cities) loop data for the day-pattern track: config parsing, polite Mayfly fetching with a disk cache,
and the corridor screening of docs/plans/day_pattern_corridor_selection_v0.md.

Mayfly: https://data.dot.state.mn.us/mayfly/{counts,occupancy}?district=metro&date=YYYYMMDD&detector=ID
-> JSON array of 2,880 30-s values (documented in github.com/mnit-rtmc/iris mayfly/src/routes.rs).
Raw data stay outside the repo (DATA_ROOT, ext4).

python -m vsl_lab.data.mndot windows            # print the candidate windows / station set size
python -m vsl_lab.data.mndot screen             # fetch occupancy for the screening days (background), then score
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import math
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_ROOT = Path("/home/catalin/work/phd/dp_data/mndot")
CONFIG = DATA_ROOT / "metro_config.xml.gz"
MAYFLY = "https://data.dot.state.mn.us/mayfly"
RATE_PER_S = 5.0
UA = "phd-research (cn.cata academic; polite 5 req/s)"


def _dist(a, b):
    return 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(b[0] - a[0]) / 2) ** 2 + math.cos(math.radians(a[0]))
                                          * math.cos(math.radians(b[0])) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2))


def windows(span=(1.5, 8.0), down_km=2.0) -> list[dict]:
    """Freeway windows of 2-3 consecutive metered entrances whose ramps all have Queue and Passage/Merge detectors;
    each window lists the mainline stations from its first ramp to down_km past its last ramp."""
    root = ET.fromstring(gzip.open(CONFIG).read())
    out = []
    for c in root.iter("corridor"):
        route, dr = c.get("route"), c.get("dir")
        if not any(k in route for k in ("I-", "U.S.", "T.H.")) or "CD" in route:
            continue
        nodes = [n for n in c.iter("r_node") if n.get("active", "t") == "t"]
        pos = [(float(n.get("lat")), float(n.get("lon"))) for n in nodes]
        km = [0.0]
        for i in range(1, len(pos)):
            km.append(km[-1] + _dist(pos[i - 1], pos[i]))
        ent = [(km[i], i, n) for i, n in enumerate(nodes) if n.get("n_type") == "Entrance" and n.find("meter") is not None]

        def full(n):
            cs = {d.get("category", "") for d in n.iter("detector")}
            return "Queue" in cs and ("Passage" in cs or "Merge" in cs)
        st = [i for i, n in enumerate(nodes) if n.get("n_type", "Station") == "Station"]
        for a in range(len(ent)):
            for b in (a + 1, a + 2):
                if b >= len(ent):
                    continue
                sub = ent[a:b + 1]
                s = sub[-1][0] - sub[0][0]
                if not (span[0] <= s <= span[1]) or not all(full(n) for _, _, n in sub):
                    continue
                i0, i1 = sub[0][1], sub[-1][1]
                main = [i for i in st if i0 < i and km[i] - km[i1] <= down_km]
                dets = {i: [d.get("name") for d in nodes[i].iter("detector") if d.get("category", "") == ""] for i in main}
                dets = {i: v for i, v in dets.items() if v}
                if len(dets) < 2:
                    continue
                out.append({"route": route, "dir": dr, "n_ramps": len(sub), "span_km": round(s, 2),
                            "start_km": round(sub[0][0], 2),
                            "ramps": [n.get("label") or n.get("name") for _, _, n in sub],
                            "meters": [n.find("meter").get("name") for _, _, n in sub],
                            "stations": [{"node": nodes[i].get("name"), "km": round(km[i], 2),
                                          "label": nodes[i].get("label", ""), "dets": v} for i, v in dets.items()]})
    return out


TOP3 = {"I35W_SB": ["M35WS29", "M35WS30", "M35WS34"], "I394_WB": ["M394W17", "M394W22", "M394W24"],
        "TH100_SB": ["M100S36", "M100S37", "M100S39"]}      # author choice 2026-10-05 (shortlist #1-#3)
RAMP_CATS = ("Queue", "Passage", "Merge", "Bypass", "Green")
US169_METERS = ["M169S51", "M169S54", "M169S55", "M169S56"]   # decision D3.2 (2026-10-05)
# Corridor analysis Addendum A (2026-10-05): downstream range extended to include the next 3 data-bearing stations
# (data-extent fix); T.H.100 SB has no station downstream in the configuration.
DOWN_KM = {"I35W_SB": 4.2, "I394_WB": 4.6, "TH100_SB": 2.0}


def corridor_detectors(meters: list[str], up_km=4.0, down_km=2.0, exit_down_km: float | None = None,
                       all_entrances: bool = False) -> dict:
    """All detectors of the corridor containing `meters`: mainline lanes of every station from up_km upstream of the
    first metered ramp to down_km downstream of the last; ramp detectors (RAMP_CATS) of the metered entrances; Exit
    detectors of exits in between."""
    root = ET.fromstring(gzip.open(CONFIG).read())
    for c in root.iter("corridor"):
        nodes = [n for n in c.iter("r_node") if n.get("active", "t") == "t"]
        names = [n.find("meter").get("name") if n.find("meter") is not None else None for n in nodes]
        if not all(m in names for m in meters):
            continue
        pos = [(float(n.get("lat")), float(n.get("lon"))) for n in nodes]
        km = [0.0]
        for i in range(1, len(pos)):
            km.append(km[-1] + _dist(pos[i - 1], pos[i]))
        i0, i1 = names.index(meters[0]), names.index(meters[-1])
        out = {"route": c.get("route"), "dir": c.get("dir"), "meters": meters, "mainline": [], "ramps": [], "exits": []}
        for i, n in enumerate(nodes):
            if not (km[i0] - up_km <= km[i] <= km[i1] + down_km):
                continue
            t = n.get("n_type", "Station")
            dets = list(n.iter("detector"))
            rec = {"node": n.get("name"), "label": n.get("label", ""), "km": round(km[i] - km[i0], 3),
                   "lanes": n.get("lanes"), "s_limit": n.get("s_limit", "55")}
            if t == "Station":
                d = [(x.get("name"), x.get("lane"), x.get("field", "22.0")) for x in dets if x.get("category", "") == ""]
                if d:
                    out["mainline"].append(rec | {"dets": d})
            elif t == "Entrance" and (all_entrances or (n.find("meter") is not None and names[i] in meters)):
                # all_entrances (METANET calibration): every entrance in range, metered or not, with Merge too
                d = [(x.get("name"), x.get("category")) for x in dets if x.get("category", "") in RAMP_CATS]
                mt = n.find("meter")
                out["ramps"].append(rec | {"meter": names[i], "storage": mt.get("storage") if mt is not None else None,
                                           "dets": d})
            elif t == "Exit" and km[i] <= km[i1] + (min(down_km, 2.0) if exit_down_km is None else exit_down_km):
                # review fix #5: exits only inside the original range (the Addendum A extension is mainline only)
                d = [(x.get("name"), x.get("category")) for x in dets if x.get("category", "") == "Exit"]
                if d:
                    out["exits"].append(rec | {"dets": d})
        return out
    raise KeyError(meters)


def year_dates(year=2023) -> list[str]:
    """All days of `year`, weekdays first (weekends second: the / and \\ day shapes need them)."""
    days = [dt.date(year, 1, 1) + dt.timedelta(k) for k in range((dt.date(year + 1, 1, 1) - dt.date(year, 1, 1)).days)]
    return [d.strftime("%Y%m%d") for d in sorted(days, key=lambda d: (d.weekday() >= 5, d))]


def pass1_dates(year=2023) -> list[str]:
    """Corridor-selection pass (104 days, ~32.7k requests for the top 3; the author approved ~25k, overrun disclosed
    2026-10-05): every Wednesday, plus alternate Saturdays and
    alternate Sundays (weekend / and \\ shapes), of `year`."""
    days = [dt.date(year, 1, 1) + dt.timedelta(k) for k in range((dt.date(year + 1, 1, 1) - dt.date(year, 1, 1)).days)]
    wed = [d for d in days if d.weekday() == 2]
    sat = [d for d in days if d.weekday() == 5][::2]
    sun = [d for d in days if d.weekday() == 6][1::2]
    return [d.strftime("%Y%m%d") for d in wed + sat + sun]


def screening_dates() -> list[str]:
    """1st and 3rd Wednesday of Feb-Nov 2023 (20 dates; 2023 = screening/tuning year, 2024 kept for the gate)."""
    out = []
    for m in range(2, 12):
        weds = [d for d in (dt.date(2023, m, k) for k in range(1, 29)) if d.weekday() == 2]
        out += [weds[0].strftime("%Y%m%d"), weds[2].strftime("%Y%m%d")]
    return out


class Fetcher:
    def __init__(self, rate=RATE_PER_S):
        self.dt = 1.0 / rate
        self.t_last = 0.0
        self.n_req = self.n_cached = self.n_404 = self.n_err = 0

    def get(self, kind: str, date: str, det: str) -> list | None:
        f = DATA_ROOT / "mayfly" / date[:4] / date / f"{det}.{kind}.json"
        if f.exists():
            self.n_cached += 1
            txt = f.read_text()
            return None if txt == "null" else json.loads(txt)
        url = f"{MAYFLY}/{kind}?district=metro&date={date}&detector={det}"
        for attempt in range(4):
            wait = self.t_last + self.dt - time.time()
            if wait > 0:
                time.sleep(wait)
            self.t_last = time.time()
            self.n_req += 1
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                    data = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.n_404 += 1
                    data = None
                    break
                self.n_err += 1
                time.sleep(2 ** attempt * 5)
            except (urllib.error.URLError, TimeoutError, ValueError):
                self.n_err += 1
                time.sleep(2 ** attempt * 5)
        else:
            return None   # not cached: retried next time
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data))
        return data


def available(date: str) -> list:
    """Detector ids with archived data on `date` (cached)."""
    f = DATA_ROOT / "mayfly" / date[:4] / date / "_detectors.json"
    if f.exists():
        return json.loads(f.read_text())
    url = f"{MAYFLY}/detectors?district=metro&date={date}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        data = json.loads(r.read())
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data))
    time.sleep(1.0 / RATE_PER_S)
    return data


def available_cached(date: str) -> list:
    """The cached detector list of `date` (no request); empty if it was never fetched."""
    f = DATA_ROOT / "mayfly" / date[:4] / date / "_detectors.json"
    return json.loads(f.read_text()) if f.exists() else []


def day_congested(occ_lanes: list[list], thr=25.0, min_bins=3) -> dict:
    """Lane-mean 5-min occupancy (%); congested if >= thr for >= min_bins consecutive 5-min bins in 06:00-20:00.
    Mayfly occupancy units: per the IRIS docs scaled values; normalised here by the max plausible (see note)."""
    lanes = [o for o in occ_lanes if o is not None and sum(1 for x in o if x is not None) > 2000]
    if not lanes:
        return {"valid": False}
    bins = []
    for b in range(72, 240):                       # 5-min bins 06:00-20:00 (10 x 30 s each)
        vals = [x for o in lanes for x in o[b * 10:(b + 1) * 10] if x is not None and x >= 0]
        bins.append(sum(vals) / len(vals) if vals else None)
    run = best = 0
    first = None
    for k, v in enumerate(bins):
        run = run + 1 if v is not None and v >= thr else 0
        if run >= min_bins and first is None:
            first = k - min_bins + 1
        best = max(best, run)
    return {"valid": True, "congested": best >= min_bins, "max_run_5min": best,
            "onset_hhmm": None if first is None else f"{(72 + first) * 5 // 60:02d}:{(72 + first) * 5 % 60:02d}"}


def _cached_occ(date: str, det: str):
    f = DATA_ROOT / "mayfly" / date[:4] / date / f"{det}.occupancy.json"
    if not f.exists():
        return None
    txt = f.read_text()
    return None if txt == "null" else json.loads(txt)


def score(W: list[dict]) -> dict:
    """Screening score per window from the cached occupancy (no new requests): per day, the station congestion of
    day_congested() on the one fetched lane; the window is congested on a day if any of its stations is; the first
    congested station (earliest onset, ties downstream) locates the bottleneck."""
    dates = screening_dates()
    cache = {}
    rows = []
    for w in W:
        per_day = []
        for date in dates:
            sts = []
            for s in w["stations"]:
                key = (date, s["node"])
                if key not in cache:
                    # review fix #4: the screen's lane choice (available that date, middle lane first), so that
                    # later pulls of more lanes cannot change the screening result
                    have = set(available_cached(date))
                    ds = [d for d in s["dets"] if d in have]
                    order = sorted(ds, key=lambda d: abs(ds.index(d) - (len(ds) - 1) / 2))
                    occ = next((o for o in (_cached_occ(date, d) for d in order) if o is not None), None)
                    cache[key] = day_congested([occ]) if occ is not None else {"valid": False}
                sts.append((s, cache[key]))
            valid = [(s, c) for s, c in sts if c["valid"]]
            if len(valid) < max(2, len(sts) // 2):
                per_day.append(None)
                continue
            cong = [(s, c) for s, c in valid if c["congested"]]
            if not cong:
                per_day.append({"congested": False})
                continue
            first = min(cong, key=lambda sc: (sc[1]["onset_hhmm"], -sc[0]["km"]))
            per_day.append({"congested": True, "station": first[0]["label"] or first[0]["node"], "km": first[0]["km"],
                            "onset": first[1]["onset_hhmm"]})
        days = [d for d in per_day if d is not None]
        cd = [d for d in days if d["congested"]]
        locs = {}
        for d in cd:
            locs[d["station"]] = locs.get(d["station"], 0) + 1
        rows.append({k: w[k] for k in ("route", "dir", "n_ramps", "span_km", "start_km", "ramps", "meters")} | {
            "n_stations": len(w["stations"]), "n_valid_days": len(days),
            "share_congested": round(len(cd) / len(days), 2) if days else None,
            "share_am_onset": round(sum(d["onset"] < "12:00" for d in cd) / len(cd), 2) if cd else None,
            "bottleneck_station_counts": dict(sorted(locs.items(), key=lambda kv: -kv[1])[:3])})
    rows.sort(key=lambda r: (-(r["share_congested"] or 0), -r["n_valid_days"]))
    return {"dates": dates, "threshold": "lane 5-min occupancy >= 25 % for >= 15 min, 06-20h, one lane per station",
            "windows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["windows", "screen", "probe", "score", "corridors", "pull"])
    ap.add_argument("--det", default="1664")
    ap.add_argument("--full-year", action="store_true", help="pull: every day of 2023 (needs author approval: ~115k req)")
    ap.add_argument("--from-bnscreen", action="store_true", help="pull: the bottleneck-anchored top 3 (protocol v1)")
    ap.add_argument("--us169-full", action="store_true", help="pull: the complete U.S.169 SB corridor (decision D3.3)")
    a = ap.parse_args(argv)
    W = windows()
    if a.what == "windows":
        dets = sorted({d for w in W for s in w["stations"] for d in s["dets"]})
        n_st = len({s["node"] for w in W for s in w["stations"]})
        print(json.dumps({"n_windows": len(W), "n_mainline_detectors": len(dets), "n_stations": n_st,
                          "n_dates": len(screening_dates()), "requests_min": n_st * len(screening_dates())}))
        return 0
    if a.what == "probe":
        f = Fetcher()
        o = f.get("occupancy", "20230315", a.det)
        print(json.dumps({"n": None if o is None else len(o), "max": None if o is None else max(x for x in o if x is not None)}))
        return 0
    if a.what == "corridors":
        out = {k: corridor_detectors(v) for k, v in TOP3.items()}
        (DATA_ROOT / "top3_corridors.json").write_text(json.dumps(out, indent=1))
        n = {k: sum(len(x["dets"]) for x in v["mainline"] + v["ramps"] + v["exits"]) for k, v in out.items()}
        print(json.dumps({"detectors": n, "requests_all_days_2023": 2 * 365 * sum(n.values()),
                          "requests_weekdays_2023": 2 * 260 * sum(n.values())}))
        return 0
    if a.what == "pull":
        if a.us169_full:   # decision D3.3: complete U.S.169 SB corridor for METANET calibration
            cors = {"US169_SB_full": corridor_detectors(US169_METERS, up_km=12.0, down_km=5.35, exit_down_km=5.35,
                                                        all_entrances=True)}
        elif a.from_bnscreen:   # selection protocol v1: the bottleneck-anchored top 3 (each <= 12,000 requests)
            bn = json.loads((Path(__file__).resolve().parents[2] / "docs" / "plans" / "day_pattern_bnscreen_v1.json").read_text())
            # unique key per corridor (bn-screen review: route_dir alone could collide); exits over the full range
            cors = {f"{c['route']}_{c['dir']}_{c['u_label']}": corridor_detectors(c["meters"], down_km=c["down_km"],
                                                                                  exit_down_km=c["down_km"])
                    for c in bn["top3"] if c["within_cap_12000"]}
        else:
            cors = {k: corridor_detectors(v, down_km=DOWN_KM.get(k, 2.0)) for k, v in TOP3.items()}
        dets = sorted({d[0] for v in cors.values() for x in v["mainline"] + v["ramps"] + v["exits"] for d in x["dets"]})
        f = Fetcher()
        t0 = time.time()
        log = DATA_ROOT / "pull_top3_progress.log"
        dates = pass1_dates(2023) if not a.full_year else year_dates(2023)
        for i, date in enumerate(dates):
            have = set(available(date))
            for det in dets:
                if det in have:
                    for kind in ("counts", "occupancy"):
                        f.get(kind, date, det)
            if i % 10 == 9 or i == len(dates) - 1:
                with open(log, "a") as fh:
                    fh.write(f"{time.strftime('%H:%M:%S')} day {i + 1}/{len(dates)} {date} req={f.n_req} "
                             f"cached={f.n_cached} 404={f.n_404} err={f.n_err} elapsed={time.time() - t0:.0f}s\n")
        print(json.dumps({"done": True, "req": f.n_req, "cached": f.n_cached, "404": f.n_404, "err": f.n_err}))
        return 0
    if a.what == "score":
        res = score(W)
        out = Path(__file__).resolve().parents[2] / "docs" / "plans" / "day_pattern_screening_v0.json"
        out.write_text(json.dumps(res, indent=1))
        print(json.dumps({"n_windows_scored": len(res["windows"]), "out": str(out)}))
        return 0
    f = Fetcher()
    dates = screening_dates()
    # one lane per station (middle lane; neighbours only if it has no data) keeps the pull at ~1 h at 5 req/s
    stations = {s["node"]: s["dets"] for w in W for s in w["stations"]}
    t0 = time.time()
    log = DATA_ROOT / "screen_progress.log"
    for i, date in enumerate(dates):
        have = set(available(date))
        for node, ds in stations.items():
            ds = [d for d in ds if d in have]        # the config is current; detectors absent that day are skipped
            order = sorted(ds, key=lambda d: abs(ds.index(d) - (len(ds) - 1) / 2))
            for det in order:
                if f.get("occupancy", date, det) is not None:
                    break
        with open(log, "a") as fh:
            fh.write(f"{time.strftime('%H:%M:%S')} date {i + 1}/{len(dates)} {date} req={f.n_req} cached={f.n_cached} "
                     f"404={f.n_404} err={f.n_err} elapsed={time.time() - t0:.0f}s\n")
    print(json.dumps({"done": True, "req": f.n_req, "cached": f.n_cached, "404": f.n_404, "err": f.n_err}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
