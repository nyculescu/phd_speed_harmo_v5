import gzip, json, statistics, datetime, xml.etree.ElementTree as ET
from pathlib import Path
D = Path("/home/catalin/work/phd/dp_data/mndot")
root = ET.fromstring(gzip.open(D / "metro_config.xml.gz").read())
cached = set(p.stem.split(".")[0] for p in (D / "mayfly/2023").glob("*/*.counts.json"))
best = []
for c in root.iter("corridor"):
    if c.get("route") != "U.S.169" or c.get("dir") != "SB":
        continue
    for r in c.iter("r_node"):
        if r.get("n_type") != "Station":
            continue
        dets = [d.get("name") for d in r.iter("detector") if (d.get("category") or "") == "" and d.get("name") in cached]
        if len(dets) >= 2:
            best.append((r.get("label") or r.get("name"), r.get("station_id"), dets))
days = sorted(p.name for p in (D / "mayfly/2023").iterdir())
wk = [d for d in days if datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday() in (1, 2, 3)]
def profile(dets):
    per = []
    for d in wk:
        try:
            arr = [json.load(open(D / "mayfly/2023" / d / f"{x}.counts.json")) for x in dets]
        except FileNotFoundError:
            continue
        if any(a is None or len(a) != 2880 for a in arr):
            continue
        tot = [sum((a[i] or 0) if a[i] is not None and a[i] >= 0 else 0 for a in arr) for i in range(2880)]
        per.append([sum(tot[k:k + 30]) * 4 for k in range(0, 2880, 30)])      # 15-min bins, veh/h
    return per
st = sorted(best, key=lambda b: -len(b[2]))
label, sid, dets = st[len(st) // 2]
per = profile(dets)
med = [statistics.median(p[k] for p in per) for k in range(96)]
print(json.dumps({"station": sid, "label": label, "lanes": len(dets), "days": len(per), "med": med}))
