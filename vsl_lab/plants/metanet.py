"""U.S.169 SB METANET plant (docs/plans/day_pattern_metanet_protocol_v3.md, binding; §1 network, §2 model).

Units inside the model: km, h, veh, km/h. T = 5 s. Replay mode (mode R, §2.3) only; mode C is a later protocol.

Vectorised over a batch axis B = (parameter sets) x (days): every state array has shape (B, N) or (B, n_origins);
every parameter is a scalar or a length-B array, so a whole CMA-ES population can be simulated in one pass.

Main entry points:
  build_network(variant="model")      -> Net (element table, cells, stations), verified against the configuration
  simulate(net, params, inputs, ...)  -> SimOut (5-min station flows/speeds, cell densities, clipping, queues)
"""
from __future__ import annotations

import gzip
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import numpy as np

T_S = 5.0                      # time step (s), §2.5
STEPS_PER_BIN = 60             # 5-min bins
RHO_MAX = 180.0                # veh/km/lane, fixed (§2.3)
V_MIN = 7.4                    # km/h, fixed (§2.5)
Q_O = 2200.0                   # veh/h per ramp lane, fixed (§2.3)
L_MIN_KM = 0.250               # cell rule (§1.4)
CELL_TARGET_KM = 0.500
V_CAP_FACTOR = 1.05            # speed cap 1.05 v_f (§2.5)
VF_MAX, TAU_MIN_S = 150.0, 10.0
START_H, END_H, SCORE_H = 4.0, 23.0, 5.0   # model runs 04:00-23:00; scoring 05:00-23:00 (§2.6)
N_BINS = int((END_H - START_H) * 12)       # 228 input bins
SCORE_FROM_BIN = int((SCORE_H - START_H) * 12)  # 12

# ---------------------------------------------------------------- §1.2 element table (protocol constants; verified)
# entrances: id, km, label, kind, merging (delta_m), replay detector(s)
ENTRANCES = [
    ("E1", -8.382, "Minnetonka Blvd", "metered", True, ["1979"]),
    ("E2", -7.233, "T.H.7 WB", "metered", True, ["1987"]),
    ("E3", -6.835, "T.H.7 EB", "metered", True, ["1990"]),
    ("E4", -5.896, "Excelsior Blvd", "metered", True, ["1994"]),
    ("E5", -4.576, "Lincoln Dr", "metered", True, ["1998"]),
    ("E6", -2.901, "Bren Rd", "metered", True, ["1368"]),
    ("E7", -2.300, "T.H.62 WB", "freeway", True, ["1369"]),
    ("E8", -1.866, "T.H.62 EB", "freeway", True, ["1372"]),
    ("E9", 0.000, "Valley View Rd", "controlled", False, ["1378"]),
    ("E10", 1.730, "I-494 WB", "freeway", False, ["7108"]),
    ("E11", 1.810, "I-494 EB", "freeway", False, ["7086"]),
    ("E12", 1.833, "Marth Rd", "controlled", True, ["7087"]),
    ("E13", 4.055, "Anderson Lakes Pkwy", "controlled", True, ["5425"]),
    ("E14", 6.118, "Pioneer Tr", "controlled", True, ["5430"]),
    ("E15", 7.518, "Old Shakopee Rd", "nodet", True, []),
]
# exits: id, km, label, detector or None (class B). X6+X7 lumped at -2.549.
EXITS = [
    ("X1", -8.074, "36th St", "1983"), ("X2", -7.670, "T.H.7", "1984"), ("X3", -6.221, "Excelsior Blvd", "1991"),
    ("X4", -5.003, "Lincoln Dr", "1995"), ("X5", -3.492, "Bren Rd", "1348"), ("X67", -2.549, "T.H.62 WB+EB", None),
    ("X8", -0.574, "Valley View Rd", "1375"), ("X9", 0.466, "W 78th St", None), ("X10", 1.355, "I-494 EB", None),
    ("X11", 3.751, "Anderson Lakes Pkwy", "5422"), ("X12", 5.818, "Pioneer Tr", "5427"),
    ("X13", 7.017, "Old Shakopee Rd", "5432"), ("X14", 8.999, "T.H.101 NB", "6764"), ("X15", 9.217, "T.H.101 SB", "6765"),
]
# stations: id, km, label, lane detectors
STATIONS = [
    ("S453", -8.413, "Minnetonka Blvd", ["1977", "1978"]), ("S455", -7.298, "T.H.7", ["1985", "1986"]),
    ("S456", -6.946, "Van Buren Way", ["1988", "1989"]), ("S457", -5.974, "Excelsior Blvd", ["1992", "1993"]),
    ("S458", -4.600, "Lincoln Dr", ["1996", "1997"]), ("S459", -3.370, "Bren Rd", ["1366", "1367"]),
    ("S460", -2.099, "T.H.62", ["1370", "1371"]), ("S461", -0.860, "69th St", ["1373", "1374"]),
    ("S462", -0.364, "Valley View Rd", ["1376", "1377"]), ("S1770", 0.370, "S of Valley View Rd", ["1379", "1380", "7094"]),
    ("S1771", 1.137, "I-494", ["7097", "7098", "7099"]), ("S1772", 1.667, "Highwood Ave", ["7084", "7085"]),
    ("S1773", 2.893, "S of Highwood Ave", ["7077", "7078", "7079"]), ("S1147", 3.922, "Anderson Lakes Pkwy", ["5423", "5424"]),
    ("S1140", 6.038, "Pioneer Tr", ["5428", "5429"]), ("S1141", 7.199, "Old Shakopee Rd", ["5433", "5434"]),
    ("S1610", 9.390, "T.H.101", ["6766", "6767"]),
]
# model geometry (§1.3): (from_km, to_km, lambda); variants override parts
LANES_MODEL = [(-8.413, 0.000, 2), (0.000, 1.355, 3), (1.355, 1.730, 2), (1.730, 1.810, 3), (1.810, 2.390, 4),
               (2.390, 3.751, 3), (3.751, 9.390, 2)]
LANES_WEAVE = [(-8.413, 0.000, 2), (0.000, 1.355, 3), (1.355, 1.730, 2), (1.730, 1.810, 3), (1.810, 2.390, 4),
               (2.390, 3.751, 3), (3.751, 6.118, 2), (6.118, 7.017, 3), (7.017, 9.390, 2)]
LANES_STEP_A = [(-8.413, 0.000, 2), (0.000, 1.355, 3), (1.355, 1.730, 2), (1.730, 1.810, 3), (1.810, 2.390, 4),
                (2.390, 3.751, 3), (3.751, 7.518, 2), (7.518, 9.217, 3), (9.217, 9.390, 2)]
LANES_STEP_C = [(-8.413, 0.000, 2), (0.000, 1.355, 3), (1.355, 1.730, 2), (1.730, 1.810, 3), (1.810, 2.390, 4),
                (2.390, 3.751, 3), (3.751, 7.518, 2)]
PHI_DROP_KM = 2.390            # the merging lane drop (§1.3): phi in the last cell before it
B1_KM, B2_KM = (3.751, 6.038), (6.038, 7.199)
GROUP_EDGES = (0.000, 3.751)   # G1 < 0.000 <= G2 < 3.751 <= G3
CONFIG = "/home/catalin/work/phd/dp_data/mndot/metro_config.xml.gz"


# ---------------------------------------------------------------- configuration reading and verification
def _dist(a, b):
    return 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(b[0] - a[0]) / 2) ** 2 + math.cos(math.radians(a[0]))
                                          * math.cos(math.radians(b[0])) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2))


def load_rnodes(route="U.S.169", direction="SB", ref_meter="M169S51", path=CONFIG) -> list[dict]:
    root = ET.fromstring(gzip.open(path).read())
    for c in root.iter("corridor"):
        if c.get("route") != route or c.get("dir") != direction:
            continue
        nodes = [n for n in c.iter("r_node") if n.get("active", "t") == "t"]
        pos = [(float(n.get("lat")), float(n.get("lon"))) for n in nodes]
        km = [0.0]
        for i in range(1, len(pos)):
            km.append(km[-1] + _dist(pos[i - 1], pos[i]))
        i0 = next(i for i, n in enumerate(nodes) if n.find("meter") is not None and n.find("meter").get("name") == ref_meter)
        out = []
        for i, n in enumerate(nodes):
            out.append({"name": n.get("name"), "km": km[i] - km[i0], "type": n.get("n_type", "Station"),
                        "label": n.get("label", ""), "lanes": int(n.get("lanes", "0")), "shift": int(n.get("shift", "0")),
                        "station_id": n.get("station_id"),
                        "dets": [(d.get("name"), d.get("category", ""), float(d.get("field", "22.0"))) for d in n.iter("detector")],
                        "meter": n.find("meter").get("name") if n.find("meter") is not None else None})
        return out
    raise KeyError((route, direction))


def verify_elements(rn: list[dict], tol_km=0.002) -> list[str]:
    """The §1.2 tables against the configuration. Returns a list of mismatches (the build fails if non-empty)."""
    bad = []

    def find(kind, km, label):
        c = [n for n in rn if n["type"] == kind and abs(n["km"] - km) <= tol_km]
        return c[0] if c else None
    for eid, km, label, kind, _m, dets in ENTRANCES:
        n = find("Entrance", km, label)
        if n is None:
            bad.append(f"{eid} {label}: no Entrance r_node at km {km}")
            continue
        names = {d[0] for d in n["dets"]}
        for d in dets:
            if d not in names:
                bad.append(f"{eid}: detector {d} not on r_node {n['name']}")
    for xid, km, label, det in EXITS:
        kms = [km] if xid != "X67" else [-2.549, -2.164]
        for k in kms:
            n = find("Exit", k, label)
            if n is None:
                bad.append(f"{xid} {label}: no Exit r_node at km {k}")
            elif det is not None and det not in {d[0] for d in n["dets"]}:
                bad.append(f"{xid}: detector {det} not on r_node {n['name']}")
    for sid, km, label, dets in STATIONS:
        n = find("Station", km, label)
        if n is None:
            bad.append(f"{sid} {label}: no Station at km {km}")
            continue
        names = {d[0] for d in n["dets"]}
        for d in dets:
            if d not in names:
                bad.append(f"{sid}: lane detector {d} not on r_node {n['name']}")
    return bad


def field_lengths(rn: list[dict]) -> dict:
    return {d[0]: d[2] for n in rn for d in n["dets"]}


# ---------------------------------------------------------------- §1.4 cell rule
@dataclass
class Net:
    variant: str
    km_from: np.ndarray
    km_to: np.ndarray
    L: np.ndarray                  # km
    lam: np.ndarray                # lanes
    group: np.ndarray              # 0=G1, 1=G2, 2=G3, 3=G4
    merge_log: list
    entrances: list                # dicts: id, km, cell, merging, dets, kind
    exits: list                    # dicts: id, km, cell, det
    stations: list                 # dicts: id, km, cell, dets, corr_entr (ids), corr_exit (ids)
    phi_cell: int                  # 0-based cell index with the lane-drop term (-1 if none)
    b1_cells: list = field(default_factory=list)
    b2_cells: list = field(default_factory=list)
    head1: int = -1                # B1 head cell (theta1)

    @property
    def N(self):
        return len(self.L)


def _lam_at(lanes, a, b):
    mid = 0.5 * (a + b)
    for x0, x1, lam in lanes:
        if x0 - 1e-9 <= mid <= x1 + 1e-9:
            return lam
    raise ValueError(mid)


def cell_table(lanes, end_km, station_kms) -> tuple[list, list]:
    """Break points -> merge short pieces -> split. Returns (cells as (from, to, lam), merge log)."""
    lam_pts = sorted({x for x0, x1, _ in lanes for x in (x0, x1)} - {lanes[0][0], lanes[-1][1]})
    pts = sorted({round(x, 6) for x in [lanes[0][0], end_km] + [s for s in station_kms if lanes[0][0] <= s <= end_km]
                  + [x for x in lam_pts if x < end_km]})
    pieces = [[pts[i], pts[i + 1], _lam_at(lanes, pts[i], pts[i + 1])] for i in range(len(pts) - 1)]
    log = []
    while True:
        short = [i for i, p in enumerate(pieces) if p[1] - p[0] < L_MIN_KM - 1e-9]
        if not short:
            break
        i = short[0]
        p = pieces[i]
        nb = [j for j in (i - 1, i + 1) if 0 <= j < len(pieces)]
        same = [j for j in nb if pieces[j][2] == p[2]]
        if same:
            j = min(same, key=lambda j: pieces[j][1] - pieces[j][0])
            lam = p[2]
        else:
            j = max(nb, key=lambda j: pieces[j][2])
            lam = pieces[j][2]
        a, b = min(p[0], pieces[j][0]), max(p[1], pieces[j][1])
        log.append(f"{p[0]:.3f}-{p[1]:.3f} ({1000 * (p[1] - p[0]):.0f} m, lam {p[2]}) into "
                   f"{pieces[j][0]:.3f}-{pieces[j][1]:.3f} (lam {pieces[j][2]})" + ("" if same else "; lambda point moved"))
        lo, hi = min(i, j), max(i, j)
        pieces[lo:hi + 1] = [[a, b, lam]]
    cells = []
    for a, b, lam in pieces:
        n = max(1, int(round((b - a) / CELL_TARGET_KM)))
        for k in range(n):
            cells.append((a + (b - a) * k / n, a + (b - a) * (k + 1) / n, lam))
    return cells, log


def cell_table_v4(lanes, end_km) -> tuple[list, list]:
    """Protocol v4 §A1 rule: break points = lambda-change points, ramp gores (X6+X7 lumped) and the stretch ends;
    stations are not break points. Pieces < L_merge are merged shortest first (ties: the upstream one) into the
    same-lambda neighbour (the shorter if both), else into the larger-lambda neighbour; n = floor(L/500 m + 0.5)."""
    start = lanes[0][0]
    lam_pts = {x for x0, x1, _ in lanes for x in (x0, x1)}
    gores = {km for _, km, *_ in ENTRANCES} | {km for _, km, *_ in EXITS}
    pts = sorted({round(x, 6) for x in lam_pts | gores | {start, end_km} if start - 1e-9 <= x <= end_km + 1e-9})
    pieces = [[pts[i], pts[i + 1], _lam_at(lanes, pts[i], pts[i + 1])] for i in range(len(pts) - 1)]
    log = []
    while True:
        short = [i for i, p in enumerate(pieces) if p[1] - p[0] < L_MIN_KM - 1e-9]
        if not short:
            break
        i = min(short, key=lambda j: (round(pieces[j][1] - pieces[j][0], 9), j))
        p = pieces[i]
        nb = [j for j in (i - 1, i + 1) if 0 <= j < len(pieces)]
        same = [j for j in nb if pieces[j][2] == p[2]]
        if same:
            j = min(same, key=lambda j: (pieces[j][1] - pieces[j][0], j))
            lam = p[2]
        else:
            j = max(nb, key=lambda j: (pieces[j][2], -(pieces[j][1] - pieces[j][0])))
            lam = pieces[j][2]
        shared = p[0] if j < i else p[1]                    # the break point the merge removes
        inside = [e for e, km, *_ in ENTRANCES + EXITS if abs(km - shared) < 1e-9]
        log.append({"removed_break_km": shared,"piece": [p[0], p[1]], "length_m": round(1000 * (p[1] - p[0])), "lam": p[2],
                    "into": [pieces[j][0], pieces[j][1]], "into_lam": pieces[j][2], "same_lam": bool(same),
                    "ramps_now_inside": inside})
        lo, hi = min(i, j), max(i, j)
        pieces[lo:hi + 1] = [[min(p[0], pieces[j][0]), max(p[1], pieces[j][1]), lam]]
    cells = []
    for a, b, lam in pieces:
        n = max(1, int(np.floor((b - a) / CELL_TARGET_KM + 0.5)))
        for k in range(n):
            cells.append((a + (b - a) * k / n, a + (b - a) * (k + 1) / n, lam))
    return cells, log


def _cell_of(km_from, km_to, x, on_boundary="downstream"):
    """§1.5: an element strictly inside a cell belongs to it; exactly on a boundary: entrances feed the downstream
    cell, exits leave and stations read the upstream cell (the first cell for the stretch start)."""
    n = len(km_from)
    for i in range(n):
        if abs(x - km_from[i]) <= 1e-9:
            return i if (on_boundary == "downstream" or i == 0) else i - 1
        if km_from[i] < x < km_to[i]:
            return i
    if abs(x - km_to[-1]) <= 1e-9:
        return n - 1
    raise ValueError(x)


V4_VARIANTS = {"v4": LANES_MODEL, "v4_weave": LANES_WEAVE, "v4_step_a": LANES_STEP_A, "v4_step_c": LANES_STEP_C}


def build_network_v4(variant: str = "v4", verify: bool = True, rnodes: list | None = None) -> Net:
    """Protocol v4 §A1/§A4. 'v4' = step (b) (G4 from the E15 cell; E15 lane-adding, V9); 'v4_weave', 'v4_step_a',
    'v4_step_c' are the regenerated variants. Build checks (1)-(2) of §A1 raise on failure."""
    lanes = V4_VARIANTS[variant]
    end_km = 7.518 if variant == "v4_step_c" else 9.390
    if verify:
        rn = rnodes if rnodes is not None else load_rnodes()
        bad = verify_elements(rn)
        if bad:
            raise RuntimeError("element table differs from the configuration: " + "; ".join(bad[:10]))
    cells, log = cell_table_v4(lanes, end_km)
    kf = np.array([c[0] for c in cells])
    kt = np.array([c[1] for c in cells])
    lam = np.array([c[2] for c in cells], dtype=float)
    mid = 0.5 * (kf + kt)
    group = np.where(mid < GROUP_EDGES[0], 0, np.where(mid < GROUP_EDGES[1], 1, 2))
    adds = {"v4": {"E9", "E10", "E11", "E15"}, "v4_weave": {"E9", "E10", "E11", "E14", "E15"},
            "v4_step_a": {"E9", "E10", "E11", "E15"}, "v4_step_c": {"E9", "E10", "E11"}}[variant]
    entr = []
    for eid, km, label, kind, merging, dets in ENTRANCES:
        if km >= end_km - 1e-9:
            continue
        entr.append({"id": eid, "km": km, "label": label, "kind": kind, "merging": merging and eid not in adds,
                     "dets": dets, "cell": _cell_of(kf, kt, km, "downstream")})
    if variant in ("v4", "v4_weave"):                        # G4 = the cell fed by E15 to the stretch end
        e15 = next(e["cell"] for e in entr if e["id"] == "E15")
        group = np.where(np.arange(len(kf)) >= e15, 3, group)
    exits = [{"id": x, "km": km, "label": lab, "det": det, "cell": _cell_of(kf, kt, km, "upstream")}
             for x, km, lab, det in EXITS if km <= end_km]
    stations = []
    for sid, km, label, dets in STATIONS:
        if km > end_km + 1e-9:
            continue
        c = _cell_of(kf, kt, km, "upstream") if km > kf[0] + 1e-9 else 0
        stations.append({"id": sid, "km": km, "label": label, "dets": dets, "cell": c,
                         "corr_entr": [e["id"] for e in entr if e["cell"] == c and e["km"] > km + 1e-9],
                         "corr_exit": [x["id"] for x in exits if x["cell"] == c and x["km"] > km + 1e-9]})
    phi_cell = int(np.flatnonzero(np.isclose(kt, PHI_DROP_KM))[0]) if np.any(np.isclose(kt, PHI_DROP_KM)) else -1
    ecell = {e["id"]: e["cell"] for e in entr}
    xcell = {x["id"]: x["cell"] for x in exits}
    b1 = list(range(ecell["E13"], xcell["X12"] + 1))          # §A1: merge cell .. cell of the last exit before the station
    b2 = list(range(ecell["E14"], xcell["X13"] + 1))
    net = Net(variant, kf, kt, kt - kf, lam, group, log, entr, exits, stations, phi_cell, b1, b2, head1=b1[0])
    scell = {s["id"]: s["cell"] for s in stations}
    scaled = set(b1) | set(b2)
    if scaled & set(scell.values()):                          # build check (1)
        raise RuntimeError(f"build check (1): a station reads a scaled cell: "
                           f"{[s for s, c in scell.items() if c in scaled]}")
    if not (scell["S1773"] < b1[0] < scell["S1140"] and scell["S1140"] < b2[0] < scell["S1141"]):   # check (2)
        raise RuntimeError("build check (2): a head is not strictly between its pair's station cells")
    return net


def build_network(variant: str = "model", verify: bool = True, rnodes: list | None = None) -> Net:
    """variant: 'model' (merge reading), 'weave' (configuration reading, sensitivity), 'step_a', 'step_c', and
    'step_b' (= model geometry with G4 on cells 33-36); protocol v3. 'v4*' variants follow protocol v4 §A1."""
    if variant.startswith("v4"):
        return build_network_v4(variant, verify, rnodes)
    lanes = {"model": LANES_MODEL, "step_b": LANES_MODEL, "weave": LANES_WEAVE, "step_a": LANES_STEP_A,
             "step_c": LANES_STEP_C}[variant]
    end_km = 7.518 if variant == "step_c" else 9.390
    if verify:
        rn = rnodes if rnodes is not None else load_rnodes()
        bad = verify_elements(rn)
        if bad:
            raise RuntimeError("element table differs from the configuration: " + "; ".join(bad[:10]))
    cells, log = cell_table(lanes, end_km, [s[1] for s in STATIONS])
    kf = np.array([c[0] for c in cells])
    kt = np.array([c[1] for c in cells])
    lam = np.array([c[2] for c in cells], dtype=float)
    mid = 0.5 * (kf + kt)
    group = np.where(mid < GROUP_EDGES[0], 0, np.where(mid < GROUP_EDGES[1], 1, 2))
    if variant == "step_b":
        group = np.where(mid >= 7.199, 3, group)
    adds = {"model": {"E9", "E10", "E11"}, "step_b": {"E9", "E10", "E11"}, "weave": {"E9", "E10", "E11", "E14"},
            "step_a": {"E9", "E10", "E11", "E15"}, "step_c": {"E9", "E10", "E11"}}[variant]
    entr = []
    for eid, km, label, kind, merging, dets in ENTRANCES:
        if km >= end_km - 1e-9:      # E15 sits at the step-(c) stretch end: not modelled
            continue
        entr.append({"id": eid, "km": km, "label": label, "kind": kind, "merging": merging and eid not in adds,
                     "dets": dets, "cell": _cell_of(kf, kt, km, "downstream")})
    exits = [{"id": x, "km": km, "label": lab, "det": det, "cell": _cell_of(kf, kt, km, "upstream")}
             for x, km, lab, det in EXITS if km <= end_km]
    stations = []
    for sid, km, label, dets in STATIONS:
        if km > end_km + 1e-9:
            continue
        c = _cell_of(kf, kt, km, "upstream") if km > kf[0] + 1e-9 else 0
        stations.append({"id": sid, "km": km, "label": label, "dets": dets, "cell": c,
                         "corr_entr": [e["id"] for e in entr if e["cell"] == c and e["km"] > km + 1e-9],
                         "corr_exit": [x["id"] for x in exits if x["cell"] == c and x["km"] > km + 1e-9]})
    phi_cell = int(np.flatnonzero(np.isclose(kt, PHI_DROP_KM))[0]) if np.any(np.isclose(kt, PHI_DROP_KM)) else -1
    b1 = [i for i in range(len(kf)) if kf[i] >= B1_KM[0] - 1e-9 and kt[i] <= B1_KM[1] + 1e-9]
    b2 = [i for i in range(len(kf)) if kf[i] >= B2_KM[0] - 1e-9 and kt[i] <= B2_KM[1] + 1e-9]
    if variant == "weave":
        b1 = [i for i in range(len(kf)) if kf[i] >= 3.751 - 1e-9 and kt[i] <= 6.118 + 1e-9]
        b2 = [i for i in range(len(kf)) if 6.118 - 1e-9 <= kf[i] < 7.199]   # v1 cells 31-33 (to the cell read by OSR)
    return Net(variant, kf, kt, kt - kf, lam, group, log, entr, exits, stations, phi_cell, b1, b2,
               head1=b1[0] if b1 else -1)


# ---------------------------------------------------------------- parameters
PARAM_NAMES = ["vf1", "vf2", "vf3", "rc1", "rc2", "rc3", "a1", "a2", "a3", "tau", "nu", "kappa", "delta_m", "phi",
               "theta1"]
BOUNDS = {"vf": (80.0, 150.0), "rc": (15.0, 45.0), "a": (1.0, 3.5), "tau": (10.0, 60.0), "nu": (5.0, 90.0),
          "kappa": (5.0, 60.0), "delta_m": (0.0, 4.0), "phi": (0.0, 4.0), "theta1": (0.75, 1.05),
          "Delta": (0.0, 0.15), "eta": (0.6, 1.0), "Cx": (900.0, 2200.0)}


def param_bounds(names):
    out = []
    for n in names:
        key = n.rstrip("1234") if n not in BOUNDS else n
        key = {"vf": "vf", "rc": "rc", "a": "a"}.get(key, key)
        out.append(BOUNDS[key])
    return out


def midpoint_params(g4: bool = False) -> dict:
    p = {n: 0.5 * sum(param_bounds([n])[0]) for n in PARAM_NAMES}
    if g4:
        p["rc4"], p["a4"] = 0.5 * sum(BOUNDS["rc"]), 0.5 * sum(BOUNDS["a"])
    return p


# ---------------------------------------------------------------- inputs and outputs
@dataclass
class Inputs:
    """Replay inputs on the 228 bins 04:00-23:00 (5-min means, veh/h; split ratios dimensionless).
    d0: (D, 228) boundary flow; d_o: (D, n_entr, 228) entrance demands in net.entrances order;
    beta: (D, n_exit, 228) split ratios in net.exits order."""
    d0: np.ndarray
    d_o: np.ndarray
    beta: np.ndarray


@dataclass
class SimOut:
    q_st: np.ndarray        # (B, n_st, bins) 5-min station flow (veh/h), bins 04:00-23:00
    v_st: np.ndarray        # (B, n_st, bins) 5-min station speed (km/h)
    rho_cell: np.ndarray    # (B, N, bins) 5-min mean cell density
    v_cell: np.ndarray      # (B, N, bins) 5-min mean cell speed
    clipped_share: np.ndarray   # (B,)
    queue_clip_veh: np.ndarray  # (B, n_origins) supply-clipped volume per origin (veh), incl. mainstream at index 0
    queue_end: np.ndarray       # (B, n_origins)
    queue_long: np.ndarray      # (B, n_origins) longest run (min) with w > 0
    nonfinite: np.ndarray       # (B,) bool
    entr_flow: np.ndarray       # (B, n_entr, bins) released origin flows (veh/h)
    exit_flow: np.ndarray       # (B, n_exit, bins)
    out_flow: np.ndarray        # (B, bins) outflow of the last cell
    veh_start: np.ndarray = None    # (B,) vehicles in the cells at 04:00
    veh_end: np.ndarray = None      # (B,) vehicles in the cells at the end
    rho_end: np.ndarray = None      # (B, N)
    v_end: np.ndarray = None        # (B, N)
    floor_nonjam_share: np.ndarray = None   # (B,) v_min floor activations with rho < rho_cr (counted as clipped)
    floor_jam_share: np.ndarray = None      # (B,) v_min floor activations with rho >= rho_cr (reported only)
    rc_cell: np.ndarray = None              # (B, N, bins) bin mean of the per-step effective rho_cr (v4 §A12)
    w0_bin: np.ndarray = None               # (B, bins) bin-mean mainstream-origin queue (veh; v4 §A13 item 2)
    w0_steps: np.ndarray = None             # (B, bins) number of steps in the bin with a mainstream-origin queue
    phi_factor_max: np.ndarray = None       # (B,) max per-step phi factor 2 phi T rho v/(L lam rho_cr) (v4 §A2)


def free_flow_state(net: Net, vf, rc_cell, a_cell, q_cells):
    """Free-flow-branch density for each cell given flows (B, N): solve lam rho V(rho) = q, rho <= rho_cr (bisection)."""
    lo = np.zeros_like(q_cells)
    hi = rc_cell.copy()
    cap = net.lam * rc_cell * vf * np.exp(-1.0 / a_cell)
    over = q_cells > cap
    for _ in range(60):
        m = 0.5 * (lo + hi)
        f = net.lam * m * vf * np.exp(-(1.0 / a_cell) * (m / rc_cell) ** a_cell)
        lo = np.where(f < q_cells, m, lo)
        hi = np.where(f >= q_cells, m, hi)
    rho = np.where(over, rc_cell, 0.5 * (lo + hi))
    return rho, over


def simulate(net: Net, params: dict, inp: Inputs, n_param_sets: int = 1, c1=1.0, c2=1.0, f1: dict | None = None,
             vsl: np.ndarray | None = None, alpha: float = 0.1, T_s: float | None = None, record_cells: bool = True,
             cap_exit: dict | None = None) -> SimOut:
    """Replay simulation. Batch B = n_param_sets * D: parameter set p and day d sit at index p * D + d.
    params: dict of scalars or arrays of length n_param_sets. f1: {"Delta":..., "eta":...} enables F1 (cells B1 u B2).
    vsl: optional (B or 1, N, bins) displayed speed limit (km/h, NaN = none); None = no speed-limit term (§2.8)."""
    if T_s is None:                                           # protocol default: v3 5 s, v4 0.75 s (§A2)
        T_s = T_S_V4 if net.variant.startswith("v4") else T_S
    assert_numerics(net, params, T_s)
    if cap_exit:
        raise NotImplementedError("EXIT-branch exit cap (§1.6) with FIFO blocking: implement only if §1.6 gives EXIT")
    D = inp.d0.shape[0]
    P = n_param_sets
    B = P * D
    N = net.N
    T = T_s / 3600.0
    spb = int(round(300.0 / T_s))
    nb = inp.d0.shape[1]

    def per_b(name):
        x = np.asarray(params[name], dtype=float)
        x = np.broadcast_to(x, (P,))
        return np.repeat(x, D)[:, None]                       # (B, 1)
    g = net.group
    vf_g = np.concatenate([per_b("vf1"), per_b("vf2"), per_b("vf3"),
                           per_b("vf3")], axis=1)            # G4 ties v_f to G3
    rc_g = np.concatenate([per_b("rc1"), per_b("rc2"), per_b("rc3"),
                           per_b("rc4") if "rc4" in params else per_b("rc3")], axis=1)
    a_g = np.concatenate([per_b("a1"), per_b("a2"), per_b("a3"), per_b("a4") if "a4" in params else per_b("a3")], axis=1)
    vf = vf_g[:, g]                                           # (B, N)
    rc0 = rc_g[:, g].copy()
    acell = a_g[:, g]
    c1b = np.repeat(np.broadcast_to(np.asarray(c1, float), (P,)), D)[:, None] if np.ndim(c1) <= 1 else np.asarray(c1)[:, None]
    c2b = np.repeat(np.broadcast_to(np.asarray(c2, float), (P,)), D)[:, None] if np.ndim(c2) <= 1 else np.asarray(c2)[:, None]
    if net.b1_cells:
        rc0[:, net.b1_cells] *= c1b
        rc0[:, net.head1] *= per_b("theta1")[:, 0]
    if net.b2_cells:
        rc0[:, net.b2_cells] *= c2b
    tau = per_b("tau") / 3600.0
    nu, kappa, dm, phi = per_b("nu"), per_b("kappa"), per_b("delta_m"), per_b("phi")
    L, lam = net.L[None, :], net.lam[None, :]
    L_, lam_ = L, lam
    vcap = V_CAP_FACTOR * vf
    f1_cells = np.array(sorted(set(net.b1_cells) | set(net.b2_cells)), dtype=int)
    if f1 is not None:
        Dlt = np.repeat(np.broadcast_to(np.asarray(f1["Delta"], float), (P,)), D)[:, None]
        eta = np.repeat(np.broadcast_to(np.asarray(f1["eta"], float), (P,)), D)[:, None]
        mem = np.zeros((B, len(f1_cells)), dtype=bool)
    # origins: 0 = mainstream, 1.. = entrances
    ne, nx = len(net.entrances), len(net.exits)
    e_cell = np.array([e["cell"] for e in net.entrances], dtype=int)
    e_merge = np.array([e["merging"] for e in net.entrances], dtype=bool)
    x_cell = np.array([x["cell"] for x in net.exits], dtype=int)
    d0 = np.tile(inp.d0, (P, 1))
    d_o = np.tile(inp.d_o, (P, 1, 1))
    beta = np.tile(inp.beta, (P, 1, 1))
    # per-cell element order for exits: entrances and exits in km order within the cell
    order = []   # list of (cell, kind, index) sorted by cell then km
    for i, e in enumerate(net.entrances):
        order.append((e["cell"], e["km"], 0, i))
    for j, x in enumerate(net.exits):
        order.append((x["cell"], x["km"], 1, j))
    order.sort()
    # initial state (§2.6): propagate the first-bin flows
    rho = np.zeros((B, N))
    v = np.zeros((B, N))
    qprop = np.zeros((B, N))
    run = d0[:, 0].copy()
    ptr = 0
    for i in range(N):
        while ptr < len(order) and order[ptr][0] == i:
            _, _, kind, idx = order[ptr]
            if kind == 0:
                run = run + d_o[:, idx, 0]
            else:
                run = run - beta[:, idx, 0] * run
            ptr += 1
        qprop[:, i] = run
    rho, _over = free_flow_state(net, vf, rc0, acell, qprop)
    v = vf * np.exp(-(1.0 / acell) * (rho / rc0) ** acell)
    w = np.zeros((B, 1 + ne))
    veh0 = (rho * L_ * lam_).sum(axis=1)
    clip_n = np.zeros(B)
    fl_nj, fl_j = np.zeros(B), np.zeros(B)
    nonfin = np.zeros(B, dtype=bool)
    st_cells = np.array([s["cell"] for s in net.stations], dtype=int)
    eid = {e["id"]: i for i, e in enumerate(net.entrances)}
    xid = {x["id"]: j for j, x in enumerate(net.exits)}
    corr = [([eid[e] for e in s["corr_entr"]], [xid[x] for x in s["corr_exit"]]) for s in net.stations]
    ns = len(net.stations)
    q_st = np.zeros((B, ns, nb))
    vden = np.zeros((B, ns, nb))
    rho_rec = np.zeros((B, N, nb)) if record_cells else np.zeros((B, 1, 1))
    v_rec = np.zeros((B, N, nb)) if record_cells else np.zeros((B, 1, 1))
    rc_rec = np.zeros((B, N, nb)) if record_cells else None
    w0_rec = np.zeros((B, nb))
    w0_cnt = np.zeros((B, nb))
    phimax = np.zeros(B)
    eflow = np.zeros((B, ne, nb))
    xflow = np.zeros((B, nx, nb))
    oflow = np.zeros((B, nb))
    qclip = np.zeros((B, 1 + ne))
    wrun = np.zeros((B, 1 + ne))
    wlong = np.zeros((B, 1 + ne))
    for b in range(nb):
        db0 = d0[:, b]
        dbo = d_o[:, :, b]
        bb = beta[:, :, b]
        vsl_b = None if vsl is None else vsl[..., b]
        for _ in range(spb):
            if f1 is not None:
                rc = rc0.copy()
                rc[:, f1_cells] = np.where(mem, (1.0 - Dlt) * rc0[:, f1_cells], rc0[:, f1_cells])
            else:
                rc = rc0
            q = rho * v * lam
            # mainstream origin
            Vc1 = vf[:, 0] * np.exp(-1.0 / acell[:, 0])
            with np.errstate(invalid="ignore", divide="ignore"):
                rho_at_v = rc[:, 0] * (-acell[:, 0] * np.log(np.clip(v[:, 0] / vf[:, 0], 1e-12, 1.0))) ** (1.0 / acell[:, 0])
            qcap1 = lam[0, 0] * rc[:, 0] * Vc1
            qlim = np.where(v[:, 0] < Vc1, lam[0, 0] * v[:, 0] * rho_at_v, qcap1)
            q0 = np.minimum(db0 + w[:, 0] / T, qlim)
            # on-ramps
            sup = Q_O * (RHO_MAX - rho[:, e_cell]) / (RHO_MAX - rc[:, e_cell])
            qo = np.minimum(np.minimum(dbo + w[:, 1:] / T, Q_O), np.maximum(sup, 0.0))
            # exits: arriving flow at the diverge, in km order within the cell
            qin = np.concatenate([q0[:, None], q[:, :-1]], axis=1)     # q_{i-1}
            run = {}
            sx = np.zeros((B, nx))
            for (ci, _km, kind, idx) in order:
                r = run.get(ci, qin[:, ci])
                if kind == 0:
                    r = r + qo[:, idx]
                else:
                    s_e = bb[:, idx] * r
                    sx[:, idx] = s_e
                    r = r - s_e
                run[ci] = r
            r_cell = np.zeros((B, N))
            for i_e in range(ne):
                r_cell[:, e_cell[i_e]] += qo[:, i_e]
            rm_cell = np.zeros((B, N))
            for i_e in np.flatnonzero(e_merge):
                rm_cell[:, e_cell[i_e]] += qo[:, i_e]
            s_cell = np.zeros((B, N))
            for j in range(nx):
                s_cell[:, x_cell[j]] += sx[:, j]
            # density
            rho_n = rho + T / (L * lam) * (qin - q + r_cell - s_cell)
            # speed
            Vr = vf * np.exp(-(1.0 / acell) * (rho / rc) ** acell)
            if vsl_b is not None:
                lim = (1.0 + alpha) * vsl_b
                Vr = np.where(np.isnan(lim), Vr, np.minimum(Vr, np.nan_to_num(lim, nan=np.inf)))
            v_up = np.concatenate([v[:, :1], v[:, :-1]], axis=1)
            rho_dn = np.concatenate([rho[:, 1:], np.minimum(rho[:, -1:], rc[:, -1:])], axis=1)
            v_n = (v + (T / tau) * (Vr - v) + (T / L) * v * (v_up - v)
                   - (nu * T) / (tau * L) * (rho_dn - rho) / (rho + kappa)
                   - dm * T * rm_cell * v / (L * lam * (rho + kappa)))
            if net.phi_cell >= 0:
                i = net.phi_cell
                v_n[:, i] -= phi[:, 0] * T * 1.0 * rho[:, i] * v[:, i] ** 2 / (L[0, i] * lam[0, i] * rc[:, i])
                phimax = np.maximum(phimax, 2.0 * phi[:, 0] * T * rho[:, i] * v[:, i] / (L[0, i] * lam[0, i] * rc[:, i]))
            # limits and clipping count (§2.5)
            rho_c = np.clip(rho_n, 0.0, RHO_MAX)
            vclip_hi = v_n > vcap
            vfloor = v_n < V_MIN
            v_c = np.clip(v_n, V_MIN, vcap)
            clipped = (rho_c != rho_n) | vclip_hi | (vfloor & (rho_c < rc))
            clip_n += clipped.sum(axis=1)
            fl_nj += (vfloor & (rho_c < rc)).sum(axis=1)
            fl_j += (vfloor & (rho_c >= rc)).sum(axis=1)
            fin = np.isfinite(rho_c).all(axis=1) & np.isfinite(v_c).all(axis=1)
            nonfin |= ~fin
            rho_next, v_next = np.nan_to_num(rho_c), np.nan_to_num(v_c, nan=V_MIN)
            # queues
            dall = np.concatenate([db0[:, None], dbo], axis=1)
            qall = np.concatenate([q0[:, None], qo], axis=1)
            qclip += T * np.maximum(dall - qall, 0.0)
            w = np.maximum(w + T * (dall - qall), 0.0)
            pos = w > 1e-9
            wrun = np.where(pos, wrun + T_s / 60.0, 0.0)
            wlong = np.maximum(wlong, wrun)
            # 5-min aggregates (§1.5) at step k: station flow corrected for downstream ramps in the same cell
            for si in range(ns):
                c = st_cells[si]
                qs = q[:, c] - sum(qo[:, k] for k in corr[si][0]) + sum(sx[:, k] for k in corr[si][1]) \
                    if (corr[si][0] or corr[si][1]) else q[:, c]
                q_st[:, si, b] += qs
                vden[:, si, b] += qs / v[:, c]
            if record_cells:
                rho_rec[:, :, b] += rho
                v_rec[:, :, b] += v
                rc_rec[:, :, b] += rc
            eflow[:, :, b] += qo
            w0_rec[:, b] += w[:, 0]
            w0_cnt[:, b] += w[:, 0] > 1e-9
            xflow[:, :, b] += sx
            oflow[:, b] += q[:, -1]
            # state update
            rho, v = rho_next, v_next
            # F1 memory update after the density update
            if f1 is not None:
                rcf = rc0[:, f1_cells]
                mem = (rho[:, f1_cells] > rcf) | (mem & (rho[:, f1_cells] > eta * rcf))
    q_st /= spb
    with np.errstate(invalid="ignore", divide="ignore"):
        v_st = np.where(vden > 0, q_st * spb / vden, np.nan)
    if record_cells:
        rho_rec /= spb
        v_rec /= spb
        rc_rec /= spb
    eflow /= spb
    xflow /= spb
    w0_rec /= spb
    oflow /= spb
    return SimOut(q_st, v_st, rho_rec, v_rec, clip_n / (N * nb * spb), qclip, w, wlong, nonfin, eflow, xflow, oflow,
                  veh0, (rho * L_ * lam_).sum(axis=1), rho, v, fl_nj / (N * nb * spb), fl_j / (N * nb * spb), rc_rec, w0_rec, w0_cnt, phimax)


T_S_V4 = 0.75                                  # protocol v4 §A2 (rule applied to the step-(b) table)
T_LADDER_V4 = (1.25, 1.0, 0.75, 0.625, 0.5)
NU_MAX, DM_MAX, KAPPA_MIN = 90.0, 4.0, 5.0     # bound maxima/minima used by §A2 (a)-(f)
VN_EPS = 1e-4                                  # §A10 test 2 (iii) gate, 1/s
_VN_CACHE: dict = {}


def v4_conditions(net: Net, T_s: float) -> dict:
    """§A2 (a)-(d), (f) against the bound maxima (units: h, km, km/h, veh/h, veh/km/lane)."""
    T, tau_min = T_s / 3600.0, TAU_MIN_S / 3600.0
    vcap = V_CAP_FACTOR * VF_MAX
    Ltab = float(net.L.min())
    sq = np.zeros(net.N)
    for e in net.entrances:
        if e["merging"]:
            sq[e["cell"]] += Q_O
    stiff = DM_MAX * T * sq / (net.L * net.lam * KAPPA_MIN)
    comb = T / tau_min + stiff + vcap * T / net.L
    return {"a": NU_MAX * T / Ltab ** 2, "b": (vcap + np.sqrt(NU_MAX / tau_min)) * T / Ltab, "c": T / tau_min,
            "d": float(stiff.max()), "d_cell": int(stiff.argmax()) + 1, "f": float(comb.max()),
            "f_cell": int(comb.argmax()) + 1, "L_tab_m": 1000 * Ltab}


def vn_scan(T_s: float, lengths_km, n_theta: int = 181) -> dict:
    """§A10 test 2 (iii): frozen-coefficient von Neumann scan of the simulate() cell update, linearised about
    uniform states (no ramps, delta_m, phi or boundaries). Returns the worst Euler growth (1/s) over stable states."""
    taus = np.array([10.0, 15.0, 30.0, 60.0])                  # s
    nus = np.array([5.0, 30.0, 60.0, 90.0]) * 1e6 / 3600.0     # m^2/s
    kaps = np.array([5.0, 20.0, 40.0, 60.0])                    # veh/km/lane
    th = np.arange(n_theta + 1) * np.pi / n_theta
    Ls = np.unique(np.round(np.asarray(lengths_km, float) * 1000.0, 3))     # m
    TAU, NU, KAP, TH, LL = np.meshgrid(taus, nus, kaps, th, Ls, indexing="ij")
    em = 1.0 - np.exp(-1j * TH)
    ep = np.exp(1j * TH) - 1.0
    worst, n_stable, n_bad, worst_state = 0.0, 0, 0, None
    worst_unstable, n_tol_band = -np.inf, 0
    for vf in (80.0, 120.0, 150.0):
        for rc in (15.0, 30.0, 45.0):
            for a in (1.0, 2.0, 3.5):
                states = []
                for r in (0.1, 0.3, 0.6, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0):
                    rho = r * rc
                    if rho > RHO_MAX:
                        continue
                    V = vf * np.exp(-(1.0 / a) * r ** a)
                    Vp = -V * r ** (a - 1.0) / rc
                    if V >= V_MIN:
                        states.append((rho, V, Vp, "eq"))
                    else:
                        states += [(rho, V_MIN, 0.0, "floor0"), (rho, V_MIN, Vp, "floorVp")]
                for r in (0.1, 0.3):
                    V = vf * np.exp(-(1.0 / a) * r ** a)
                    states.append((r * rc, V_CAP_FACTOR * vf, -V * r ** (a - 1.0) / rc, "cap"))
                for rho0, v0k, Vpk, kind in states:
                    v0, Vp = v0k / 3.6, Vpk / 3.6                 # m/s, (m/s)/(veh/km)
                    a11 = -(v0 / LL) * em
                    a12 = -(rho0 / LL) * em
                    a21 = Vp / TAU - NU * ep / (TAU * LL * (rho0 + KAP))
                    a22 = -1.0 / TAU - (v0 / LL) * em
                    tr, det = a11 + a22, a11 * a22 - a12 * a21
                    s = np.sqrt(tr * tr / 4.0 - det)
                    lam = np.stack([tr / 2.0 + s, tr / 2.0 - s])          # (2, tau, nu, kap, th, L)
                    re_max = lam.real.max(axis=(0, 4))
                    mag = np.abs(lam).max(axis=(0, 4))
                    stable = re_max <= 1e-9 * mag
                    gr = (np.log(np.abs(1.0 + T_s * lam)) / T_s).max(axis=(0, 4))
                    n_stable += int(stable.sum())
                    worst_unstable = max(worst_unstable, float(np.where(~stable, gr - re_max, -np.inf).max()))
                    n_tol_band += int(((re_max > 0) & stable).sum())
                    g = np.where(stable, gr, -np.inf)
                    if g.max() > worst:
                        worst = float(g.max())
                        k = np.unravel_index(int(g.argmax()), g.shape)
                        worst_state = {"tau": float(taus[k[0]]), "nu": float(nus[k[1]] * 3600 / 1e6),
                                       "kappa": float(kaps[k[2]]), "L_m": float(Ls[k[3]]), "vf": vf, "rc": rc,
                                       "a": a, "rho": float(rho0), "kind": kind}
                    n_bad += int((g > VN_EPS).sum())
    return {"T_s": T_s, "worst_stable_growth": worst, "n_stable": n_stable, "n_stable_above_eps": n_bad,
            "report_only": {"worst_excess_growth_unstable_states": worst_unstable, "n_tolerance_band": n_tol_band},
            "worst_state": worst_state, "PASS": bool(worst <= VN_EPS)}


def payne_diagnostic(params: dict, net: Net, T_s: float) -> dict:
    """§A2 report-only, per FD group g and rho in {1.0, 1.25, 1.5, 1.75, 2.0} x rho_cr,g at the frozen parameters:
    c = sqrt(nu rho / (tau (rho + kappa))) vs rho |V'(rho)| (km/h), and the maximum semi-discrete growth rate (1/s)
    of the linearised cell update on g's shortest cell."""
    p = {k: float(np.ravel(v)[0]) for k, v in params.items()}
    vf = {0: p["vf1"], 1: p["vf2"], 2: p["vf3"], 3: p["vf3"]}
    rcg = {0: p["rc1"], 1: p["rc2"], 2: p["rc3"], 3: p.get("rc4", p["rc3"])}
    ag = {0: p["a1"], 1: p["a2"], 2: p["a3"], 3: p.get("a4", p["a3"])}
    tau, nu, kap = p["tau"], p["nu"] * 1e6 / 3600.0, p["kappa"]
    th = np.arange(182) * np.pi / 181
    out = {}
    for g in sorted(set(int(x) for x in net.group)):
        Lm = 1000.0 * float(net.L[net.group == g].min())
        rows = []
        for r in (1.0, 1.25, 1.5, 1.75, 2.0):
            rho = r * rcg[g]
            V = vf[g] * np.exp(-(1.0 / ag[g]) * r ** ag[g])
            Vp = -V * r ** (ag[g] - 1.0) / rcg[g]
            c = np.sqrt(p["nu"] * rho / ((tau / 3600.0) * (rho + kap)))          # km/h
            v0, Vps = V / 3.6, Vp / 3.6
            em, ep = 1.0 - np.exp(-1j * th), np.exp(1j * th) - 1.0
            a11, a12 = -(v0 / Lm) * em, -(rho / Lm) * em
            a21 = Vps / tau - nu * ep / (tau * Lm * (rho + kap))
            a22 = -1.0 / tau - (v0 / Lm) * em
            tr, det = a11 + a22, a11 * a22 - a12 * a21
            sq = np.sqrt(tr * tr / 4.0 - det)
            lam = np.concatenate([tr / 2.0 + sq, tr / 2.0 - sq])
            rows.append({"rho_over_rcr": r, "c_kmh": float(c), "rho_absVprime_kmh": float(rho * abs(Vp)),
                         "max_growth_1_per_s": float(lam.real.max())})
        out[f"G{g + 1}"] = rows
    return out


def assert_numerics_v4(net: Net, params: dict, T_s: float) -> None:
    """§A2: (a)-(d), (f) in every call; (e) the von Neumann gate, cached per (T, table)."""
    c = v4_conditions(net, T_s)
    bad = [k for k, lim in (("a", 0.25), ("b", 0.5)) if c[k] > lim + 1e-12]
    bad += ["c"] if c["c"] > 0.1 + 1e-12 else []
    bad += [k for k in ("d", "f") if c[k] >= 1.0]
    if bad:
        raise ValueError(f"protocol v4 §A2: conditions {bad} fail at T = {T_s} s ({c})")
    key = (T_s, tuple(np.round(np.unique(net.L), 6)))
    if key not in _VN_CACHE:
        _VN_CACHE[key] = vn_scan(T_s, net.L)
    if not _VN_CACHE[key]["PASS"]:
        raise ValueError(f"protocol v4 §A2 (e): von Neumann gate fails at T = {T_s} s: {_VN_CACHE[key]}")
    if np.any(np.asarray(params["tau"], dtype=float) < TAU_MIN_S - 1e-9):
        raise ValueError("tau below its lower bound")


def assert_numerics(net: Net, params: dict, T_s: float = T_S) -> None:
    if net.variant.startswith("v4"):
        return assert_numerics_v4(net, params, T_s)
    """§2.5, asserted against the bound maxima (not the current iterate): CFL with v_cap = 1.05 x 150 km/h, and
    tau >= 2T over the whole tau range (tau_min = 10 s)."""
    vcap = V_CAP_FACTOR * VF_MAX / 3.6                       # m/s
    if T_s * vcap > 1000.0 * net.L.min() + 1e-9:
        raise ValueError(f"CFL: T v_cap = {T_s * vcap:.1f} m > min cell {1000 * net.L.min():.1f} m")
    if TAU_MIN_S < 2.0 * T_s - 1e-12:
        raise ValueError("tau_min < 2T")
    if np.any(np.asarray(params["tau"], dtype=float) < TAU_MIN_S - 1e-9):
        raise ValueError("tau below its lower bound")
