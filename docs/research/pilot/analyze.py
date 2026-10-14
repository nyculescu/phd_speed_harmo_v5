"""Pilot analysis (pre-P0, non-project seeds, NOT protocol data)."""
import json, re, sys, os
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
import numpy as np

RUNS = Path("/home/catalin/work/phd/v5b1_runs/pilot_20261013")
D = Path(__file__).resolve().parent
OUT = D / "out"; OUT.mkdir(exist_ok=True)
DENS = {"petrol": 0.748, "diesel": 0.836, "phevP": 0.748}          # kg/L (JEC E10 / B7)

def loops(run, meta):
    """-> positions (m), minutes, speed[x,t] (km/h, flow-weighted over lanes), flow[x,t] (veh/h total), lanes[x]"""
    starts = meta["edge_start"]
    cnt = defaultdict(float); spd = defaultdict(float); nl = defaultdict(set)
    for _, el in ET.iterparse(run / "loops.xml"):
        if el.tag != "interval": continue
        did = el.get("id"); m = re.match(r"d_(.+)_(\d+)_(\d+)$", did)
        lane, x = m.group(1) + "_" + m.group(2), int(m.group(3))
        t = int(float(el.get("begin")) // 60); n = float(el.get("nVehContrib")); s = float(el.get("speed"))
        cnt[(x, t)] += n
        if n > 0 and s >= 0: spd[(x, t)] += n * s
        nl[x].add(lane); el.clear()
    xs = sorted(nl); T = max(t for _, t in cnt) + 1
    V = np.full((len(xs), T), np.nan); Q = np.zeros((len(xs), T))
    for i, x in enumerate(xs):
        for t in range(T):
            n = cnt.get((x, t), 0.0); Q[i, t] = n * 60
            if n > 0: V[i, t] = spd[(x, t)] / n * 3.6
    return np.array(xs), np.arange(T), V, Q, np.array([len(nl[x]) for x in xs])

def summarize(tag):
    run = RUNS / tag
    v, arm, l, s = re.match(r"(\w+?)_(B\d\w*)_l([\d.]+)_s(\d+)", tag).groups()
    meta = json.load(open(D / "nets" / v / "meta.json")); X = meta["x"]
    st = ET.parse(run / "stat.xml").getroot()
    tel = st.find("teleports").attrib; saf = st.find("safety").attrib; veh = st.find("vehicles").attrib
    man = json.load(open(run / "manifest.json")); info = {i: k for k, i in enumerate(man["id"])}
    rr = json.load(open(run / "manifest.json"))
    # desired departures from the route file order (manifest is sorted by t)
    tdes = {}
    for line in open(run / "r.rou.xml"):
        if line.startswith("<vehicle"):
            tdes[re.search(r'id="([^"]+)"', line).group(1)] = float(re.search(r'depart="([\d.]+)"', line).group(1))
    rows = []
    for _, el in ET.iterparse(run / "trip.xml"):
        if el.tag != "tripinfo": continue
        e = el.find("emissions")
        vid = el.get("id"); k = info[vid]
        rows.append(dict(id=vid, pt=man["pt"][k], cav=man["cav"][k], cat=man["cat"][k], r=man["r"][k],
                         tdes=tdes[vid], dep=float(el.get("depart")), arr=float(el.get("arrival")),
                         dd=float(el.get("departDelay")), dur=float(el.get("duration")), L=float(el.get("routeLength")),
                         tl=float(el.get("timeLoss")), fuel=float(e.get("fuel_abs")) if e is not None else np.nan,
                         el=float(e.get("electricity_abs")) if e is not None else np.nan))
        el.clear()
    coh = [r for r in rows if 900 <= r["tdes"] < 9900]
    unfinished = sum(1 for r in coh if r["arr"] < 0)
    d2d = np.array([(r["arr"] if r["arr"] >= 0 else 11700) - r["tdes"] for r in coh])
    loss = np.array([r["tl"] + r["dd"] for r in coh])        # pilot delay proxy: SUMO timeLoss + insertion delay
    vkm = sum(r["L"] for r in coh) / 1000
    # energy per powertrain (finished, full-length through trips only, to avoid partial trips)
    en = defaultdict(list)
    for r in coh:
        if r["arr"] < 0 or r["L"] < 5000: continue
        km = r["L"] / 1000
        if r["pt"] in DENS: en[r["pt"]].append(r["fuel"] / 1e6 / DENS[r["pt"]] / km * 100)   # L/100 km
        elif r["pt"] in ("bev", "phevE"): en[r["pt"]].append(r["el"] / 1000 / km * 100)       # kWh/100 km
        elif r["pt"] == "truck": en["truck_gkm"].append(r["fuel"] / 1000 / km)                # g/km (HBEFA4, artefact)
    xs, ts, V, Q, nlan = loops(run, meta)
    # congestion: loop-minute speed < 60 km/h during the episode
    cong = (V < 60)
    def any_cong(a, b): m = (xs >= a) & (xs < b); return bool(np.nanmax(cong[m]) if m.any() else False)
    groups = {"entry": (0, 1000), "M1": (X["merge1"] - 750, X["merge1"] + 500), "Z1": tuple(X["Z1"]),
              "Z2": tuple(X["Z2"]), "M2": (X["merge2"] - 750, X["merge2"] + 500), "Z3": tuple(X["Z3"]),
              "LD": (X["drop"] - 750, X["drop"] + 250)}
    where = {g: any_cong(*ab) for g, ab in groups.items()}
    # queue extent upstream of the drop, tolerating the light gaps between waves (gap <= 1,000 m)
    up = np.where(xs < X["drop"])[0][::-1]
    ext_t = np.zeros(len(ts))
    for t in ts:
        ext = 0.0; last = X["drop"]
        for i in up:
            if cong[i, t]: ext = X["drop"] - xs[i]; last = xs[i]
            elif last - xs[i] > 1000: break
        ext_t[t] = ext
    qmax = float(ext_t.max())
    # onset: first minute the queue is >= 500 m long
    on = np.where(ext_t >= 500)[0]; onset = int(on[0]) if len(on) else None
    reach = {g: bool(qmax >= X["drop"] - X[g][0]) for g in ("Z3", "Z2")}
    reach["M2"] = bool(qmax >= X["drop"] - (X["merge2"] + 250))
    # discharge: first loop position downstream of the drop, veh/h/lane
    dn = np.where(xs > X["drop"])[0][0]
    qdown = Q[dn] / nlan[dn]
    end = onset if onset is not None else len(ts)
    pre = float(max(np.mean(qdown[t:t + 15]) for t in range(0, end - 15))) if end > 15 else np.nan
    dis = float(np.mean(qdown[onset + 5:onset + 65])) if onset is not None else np.nan
    # waves: in the queue, 1.5 km upstream of the drop: dips below 40 then back above 60 km/h
    iw = int(np.argmin(np.abs(xs - (X["drop"] - 1500))))
    cyc = 0; low = False; amp = []
    for s_ in V[iw]:
        if np.isnan(s_): continue
        if s_ < 40: low = True
        elif s_ > 60 and low: cyc += 1; low = False
    vq = V[iw][(V[iw] < 60)]
    # wave speed: lag maximising correlation between speed series 1 km apart inside the queue
    iu = int(np.argmin(np.abs(xs - (X["drop"] - 2500))))
    ws = np.nan
    if onset is not None:
        a1 = V[iw, onset:]; a2 = V[iu, onset:]; m = ~(np.isnan(a1) | np.isnan(a2))
        if m.sum() > 30:
            a1 = a1[m] - a1[m].mean(); a2 = a2[m] - a2[m].mean(); best = (-2, 0)
            for lag in range(1, 15):                # upstream position sees the dip later
                c = np.corrcoef(a1[:-lag], a2[lag:])[0, 1]
                if c > best[0]: best = (c, lag)
            if best[0] > 0.3: ws = -(xs[iw] - xs[iu]) / 1000 / (best[1] / 60)   # km/h, negative = upstream
    sg_share = float(np.nanmean(vq < 20)) if len(vq) else 0.0
    # capacity drop per bottleneck: active minutes = >=1 congested loop in [xb-750, xb) AND downstream speed >= 70 km/h
    bns = {"M1": X["merge1"] + 250, "M2": X["merge2"] + 250, "LD": X["drop"]}
    cd = {}
    for name, xb in bns.items():
        idn = np.where(xs > xb + 100)[0][0]; iup = (xs >= xb - 750) & (xs < xb)
        qd = Q[idn] / nlan[idn]; vd = V[idn]
        act = np.array([bool(np.nanmax(cong[iup, t])) and (vd[t] >= 70) for t in ts])
        ia = np.where(act)[0]
        if len(ia) < 10: cd[name] = dict(active_min=int(len(ia))); continue
        t0 = int(ia[0])
        pre_ = float(max(np.mean(qd[t:t + 15]) for t in range(0, t0 - 15))) if t0 > 15 else np.nan
        dis_ = float(np.mean(qd[ia[:60]]))
        cd[name] = dict(active_min=int(len(ia)), onset=t0, pre=pre_, dis=dis_, ratio=(dis_ / pre_ if pre_ == pre_ else np.nan))
    return dict(cd=cd, tag=tag, variant=v, arm=arm, lam=float(l), seed=int(s), inserted=int(veh["inserted"]),
                loaded=int(veh["loaded"]), teleports=int(tel["total"]), collisions=int(saf["collisions"]),
                ebrake=int(saf["emergencyBraking"]), cohort=len(coh), unfinished=unfinished,
                d2d_mean=float(d2d.mean()), loss_mean=float(loss.mean()), dd_mean=float(np.mean([r["dd"] for r in coh])),
                dd_max=float(np.max([r["dd"] for r in coh])), vkm=vkm,
                energy={k: [float(np.median(x)), float(np.percentile(x, 5)), float(np.percentile(x, 95)), len(x)] for k, x in en.items()},
                where=where, reach=reach, queue_max_m=qmax, onset_min=onset, pre_qlane=pre, dis_qlane=dis,
                drop_ratio=(dis / pre if pre and pre == pre and dis == dis else np.nan),
                wave_cycles=cyc, wave_speed_kmh=ws, stop_share_in_queue=sg_share,
                vmin_queue=float(np.nanmin(V[iw])) if onset is not None else np.nan)

def spacetime(tag, fn, title):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    v = tag.split("_")[0]; meta = json.load(open(D / "nets" / v / "meta.json")); X = meta["x"]
    xs, ts, V, Q, _ = loops(RUNS / tag, meta)
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=130)
    im = ax.imshow(V, aspect="auto", origin="lower", cmap="Blues_r", vmin=0, vmax=110,
                   extent=[0, len(ts), xs[0] / 1000, xs[-1] / 1000], interpolation="nearest")
    for z in ("Z1", "Z2", "Z3"):
        for y in X[z]: ax.axhline(y / 1000, color="#52514e", lw=0.6, ls=":")
        ax.text(len(ts) + 1, np.mean(X[z]) / 1000, z, va="center", fontsize=8, color="#0b0b0b")
    ax.axhline(X["drop"] / 1000, color="#0b0b0b", lw=0.8); ax.text(len(ts) + 1, X["drop"] / 1000, "drop", va="center", fontsize=8)
    for t0 in (15, 165): ax.axvline(t0, color="#52514e", lw=0.6, ls="--")
    ax.set_xlabel("time (min)  ·  dashed: scored window 15–165 min"); ax.set_ylabel("position (km)")
    ax.set_title(title, fontsize=10, loc="left")
    cb = fig.colorbar(im, ax=ax, pad=0.06); cb.set_label("speed (km/h); dark = jam")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(OUT / fn); plt.close(fig)

if __name__ == "__main__":
    tags = sorted(p.name for p in RUNS.iterdir() if (p / "rc.txt").exists() and (p / "rc.txt").read_text().strip() == "0")
    res = []
    for t in tags:
        try: res.append(summarize(t))
        except Exception as e: res.append(dict(tag=t, error=repr(e)))
    json.dump(res, open(OUT / "summary.json", "w"), indent=1, default=str)
    print(len(res), "runs summarised;", sum("error" in r for r in res), "errors")
