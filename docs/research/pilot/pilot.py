"""Pre-P0 pilot (author request 2026-10-13). NOT project code, NOT protocol data: non-project seeds 1..N,
no controller, disclosed (V69). Follows protocol v1 §2.2-2.4 where cheap; V68 layout.

usage: pilot.py build <variant>            -> network + detectors in nets/<variant>/
       pilot.py run <variant> <arm> <lam> <seed>   -> one run in runs/
"""
import subprocess, sys, json, math, os
from pathlib import Path
import numpy as np

D = Path(__file__).resolve().parent
BIN = Path(sys.executable).parent
RUNS = Path("/home/catalin/work/phd/v5b1_runs/pilot_20261013")

# ---------------- network (V68), variants for the topology study ----------------
def build(variant="base"):
    nd = D / "nets" / variant; nd.mkdir(parents=True, exist_ok=True)
    gap = 3000 if variant == "gap3k" else 5000   # plain stretch between zones (V68: 5 km)
    x_m1 = 3000; x_m2 = x_m1 + gap + 1000; x_ld = x_m2 + gap + 1000; x_end = x_ld + 3250
    nodes = {"n0": (0, 0), "n2000": (2000, 0), "n3000": (x_m1, 0), "n3250": (x_m1 + 250, 0),
             "nz2": (x_m2 - 1000, 0), "nm2": (x_m2, 0), "nm2e": (x_m2 + 250, 0), "nz3": (x_ld - 1000, 0),
             "nld": (x_ld, 0), "nend": (x_end, 0),
             "or1s": (x_m1 - 600, -90), "x1e": (x_m1 + 850, -90), "or2s": (x_m2 - 600, -90), "x2e": (x_m2 + 850, -90)}
    edges = [("m0", "n0", "n2000", 3), ("m1", "n2000", "n3000", 3), ("merge1", "n3000", "n3250", 4),
             ("m3a", "n3250", "nz2", 3), ("m3", "nz2", "nm2", 3), ("merge2", "nm2", "nm2e", 4),
             ("m5a", "nm2e", "nz3", 3), ("m5", "nz3", "nld", 3), ("m6", "nld", "nend", 2),
             ("OR1", "or1s", "n3000", 1), ("X1", "n3250", "x1e", 1), ("OR2", "or2s", "nm2", 1), ("X2", "nm2e", "x2e", 1)]
    sp = {e[0]: (25.0 if e[0][:1] in "OX" else 27.78) for e in edges}
    cons = [("m0", i, "m1", i) for i in range(3)] + [("m1", i, "merge1", i + 1) for i in range(3)] + [("OR1", 0, "merge1", 0)]
    cons += [("merge1", i + 1, "m3a", i) for i in range(3)] + [("merge1", 0, "X1", 0)] + [("m3a", i, "m3", i) for i in range(3)]
    cons += [("m3", i, "merge2", i + 1) for i in range(3)] + [("OR2", 0, "merge2", 0)]
    cons += [("merge2", i + 1, "m5a", i) for i in range(3)] + [("merge2", 0, "X2", 0)] + [("m5a", i, "m5", i) for i in range(3)]
    if variant == "laneend":                # lane 0 simply ends: drivers must change lanes before the drop
        cons += [("m5", 1, "m6", 0), ("m5", 2, "m6", 1)]
    else:                                   # zipper node: lanes 0,1 -> 0 alternate; lane 2 -> 1
        cons += [("m5", 0, "m6", 0), ("m5", 1, "m6", 0), ("m5", 2, "m6", 1)]
    zipper = variant != "laneend"
    (nd / "n.nod.xml").write_text("<nodes>\n" + "".join(
        f'<node id="{k}" x="{x}" y="{y}"{" type=\"zipper\"" if (k == "nld" and zipper) else ""}/>\n' for k, (x, y) in nodes.items()) + "</nodes>\n")
    (nd / "n.edg.xml").write_text("<edges>\n" + "".join(
        f'<edge id="{e}" from="{f}" to="{t}" numLanes="{n}" speed="{sp[e]}"/>\n' for e, f, t, n in edges) + "</edges>\n")
    (nd / "n.con.xml").write_text("<connections>\n" + "".join(
        f'<connection from="{a}" fromLane="{i}" to="{b}" toLane="{j}"/>\n' for a, i, b, j in cons) + "</connections>\n")
    subprocess.run([str(BIN / "netconvert"), "-n", "n.nod.xml", "-e", "n.edg.xml", "-x", "n.con.xml", "-o", "f3z.net.xml",
                    "--no-turnarounds", "true", "-W"], cwd=nd, check=True)
    # induction loops every 250 m on every mainline lane (evaluation only, never an arm input)
    import xml.etree.ElementTree as ET
    net = ET.parse(nd / "f3z.net.xml").getroot()
    mains = ["m0", "m1", "merge1", "m3a", "m3", "merge2", "m5a", "m5", "m6"]
    lanes = {}
    for e in net.iter("edge"):
        if e.get("id") in mains:
            for l in e.iter("lane"):
                lanes[l.get("id")] = (e.get("id"), float(l.get("length")))
    xs = {}; cum = 0.0
    starts = {}
    for e in mains:
        L = [v[1] for k, v in lanes.items() if v[0] == e][0]; starts[e] = cum; cum += L
    det = []
    for lid, (e, L) in lanes.items():
        pos = 125.0
        while pos < L - 1:
            x = starts[e] + pos
            det.append(f'<inductionLoop id="d_{lid}_{int(x)}" lane="{lid}" pos="{pos:.1f}" period="60" file="LOOPS"/>\n')
            pos += 250.0
    (nd / "det.add.xml").write_text("<additional>\n" + "".join(det) + "</additional>\n")
    meta = {"variant": variant, "x": {"merge1": x_m1, "merge2": x_m2, "drop": x_ld, "end": x_end,
            "Z1": [2000, 3000], "Z2": [x_m2 - 1000, x_m2], "Z3": [x_ld - 1000, x_ld]}, "edge_start": starts}
    (nd / "meta.json").write_text(json.dumps(meta, indent=1))
    return nd

# ---------------- inflow + attribute manifest (protocol §2.3-2.4) ----------------
PEAK = {"main": 4000.0, "or1": 1200.0, "or2": 1000.0}
ROUTES = {"main_thru": ("main", 0.8, "m0 m1 merge1 m3a m3 merge2 m5a m5 m6"),
          "main_x1": ("main", 0.1, "m0 m1 merge1 X1"),
          "main_x2": ("main", 0.1, "m0 m1 merge1 m3a m3 merge2 X2"),
          "or1_thru": ("or1", 0.9, "OR1 merge1 m3a m3 merge2 m5a m5 m6"),
          "or1_x2": ("or1", 0.1, "OR1 merge1 m3a m3 merge2 X2"),
          "or2_thru": ("or2", 1.0, "OR2 merge2 m5a m5 m6")}
def rel(t):        # triangle: 0.5 until 900 s, peak at 5160 s, 0.7 at 9900 s, stop after
    if t < 900: return 0.5
    if t < 5160: return 0.5 + 0.5 * (t - 900) / 4260
    if t < 9900: return 1.0 - 0.3 * (t - 5160) / 4740
    return 0.0
CAR_PT = [("petrol", .2552), ("diesel", .1737), ("hev", .2285), ("phev", .1506), ("bev", .1920)]
EMC = {"petrol": "HBEFA4/PC_petrol_Euro-6d", "diesel": "HBEFA4/PC_diesel_Euro-6d", "phevP": "HBEFA4/PC_PHEV_petrol_Euro-6d_(P)",
       "phevE": "HBEFA4/PC_PHEV_petrol_Euro-6d_(El)", "bev": "HBEFA4/PC_BEV", "truck": "HBEFA4/TT_AT_gt34-40t_Euro-VI_D-E"}
MASS = {"petrol": 1400, "diesel": 1500, "phevP": 1700, "phevE": 1700, "bev": 1800, "truck": 40000}   # pilot ASSUMPTION

def manifest(lam, seed):
    vehs = []
    for k, (rid, (src, sh, _)) in enumerate(ROUTES.items()):
        rng = np.random.default_rng([seed, 1000 + k])
        qmax = PEAK[src] * sh * lam / 3600.0
        t = 0.0
        while True:                                 # thinning of a Poisson process
            t += rng.exponential(1.0 / qmax)
            if t >= 9900: break
            if rng.random() < rel(t): vehs.append([t, rid])
    vehs.sort()
    ra = np.random.default_rng([seed, 1])          # attribute stream
    out = []
    for i, (t, rid) in enumerate(vehs):
        if ra.random() < 0.075:
            out.append(dict(id=f"v{i}", t=t, r=rid, cat="truck", pt="truck", cav=False, sf=1.0)); continue
        u = ra.random(); acc = 0
        for pt, p in CAR_PT:
            acc += p
            if u < acc: break
        if pt in ("hev", "phev"): pt = "phevE" if ra.random() < 0.5 else "phevP"
        cav = pt in ("phevE", "phevP", "bev") and ra.random() < 0.5
        v = ra.random()
        sf = 1.0 if v < 0.55 else (1.0 + 0.2 * ra.random() if v < 0.997 else 1.2 + 0.3 * ra.random())
        out.append(dict(id=f"v{i}", t=t, r=rid, cat="car", pt=pt, cav=cav, sf=sf))
    return out

def routes_xml(lam, seed, arm):
    m = manifest(lam, seed)
    s = ["<routes>\n"]
    for pt in ["petrol", "diesel", "phevP", "phevE", "bev"]:
        s.append(f'<vType id="hdv_{pt}" vClass="passenger" carFollowModel="EIDM" laneChangeModel="LC2013" speedDev="0" '
                 f'mass="{MASS[pt]}" emissionClass="{EMC[pt]}" color="240,200,0"/>\n')
        s.append(f'<vType id="cav_{pt}" vClass="passenger" carFollowModel="ACC" laneChangeModel="LC2013" speedDev="0" '
                 f'mass="{MASS[pt]}" emissionClass="{EMC[pt]}" color="0,90,255"/>\n')
    s.append(f'<vType id="truck" vClass="truck" length="16.5" maxSpeed="25" carFollowModel="EIDM" laneChangeModel="LC2013" '
             f'speedDev="0" mass="40000" emissionClass="{EMC["truck"]}" color="200,30,30"/>\n')
    for rid, (_, _, edges) in ROUTES.items():
        s.append(f'<route id="{rid}" edges="{edges}"/>\n')
    for v in m:
        if v["cat"] == "truck": ty = "truck"
        elif v["cav"] and arm in ("B1", "B1s"): ty = f"cav_{v['pt']}"
        else: ty = f"hdv_{v['pt']}"
        sf = 1.0 if (v["cav"] and arm == "B1") else v["sf"]      # B1s (V72): CAV keeps its driver's desired speed
        dl = "0" if v["r"].startswith("or") else "random"
        s.append(f'<vehicle id="{v["id"]}" type="{ty}" route="{v["r"]}" depart="{v["t"]:.2f}" departLane="{dl}" '
                 f'departSpeed="avg" speedFactor="{sf:.4f}"/>\n')
    s.append("</routes>\n")
    return "".join(s), m

def run(variant, arm, lam, seed):
    nd = D / "nets" / variant
    tag = f"{variant}_{arm}_l{lam:.2f}_s{seed}"
    od = RUNS / tag; od.mkdir(parents=True, exist_ok=True)
    rx, m = routes_xml(lam, seed, arm)
    (od / "r.rou.xml").write_text(rx)
    json.dump({k: [v[k] for v in m] for k in ("id", "pt", "cav", "sf", "cat", "r")}, open(od / "manifest.json", "w"))
    (od / "det.add.xml").write_text((nd / "det.add.xml").read_text().replace("LOOPS", str(od / "loops.xml")))
    cmd = [str(BIN / "sumo"), "-n", str(nd / "f3z.net.xml"), "-r", str(od / "r.rou.xml"), "-a", str(od / "det.add.xml"),
           "--begin", "0", "--end", "11700", "--step-length", "0.2", "--time-to-teleport", "300",
           "--collision.action", "warn", "--collision.check-junctions", "true", "--collision.mingap-factor", "0",
           "--seed", str(seed), "--device.emissions.probability", "1",
           "--tripinfo-output", str(od / "trip.xml"), "--tripinfo-output.write-unfinished", "true",
           "--statistic-output", str(od / "stat.xml"), "--log", str(od / "log.txt"), "--no-step-log", "true",
           "--duration-log.statistics", "true"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    (od / "rc.txt").write_text(str(r.returncode))
    return tag, r.returncode

if __name__ == "__main__":
    if sys.argv[1] == "build": print(build(sys.argv[2]))
    else: print(run(sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5])))
