"""Fleet sampler (v5b/fleet/fleet.py): shares, bounds, moments, CRN and the vType XML."""
import numpy as np
import pytest

from v5b.fleet import fleet as fl

SEED, N = 7_400_000, 20_000


@pytest.fixture(scope="module")
def veh():
    return fl.sample(N, SEED, 4, [0.0] * N)


def by(veh, cls):
    return [v for v in veh if v.cls == cls]


def test_shares(veh):
    for c, p in zip(fl.CLASSES, fl.SHARES):
        k = len(by(veh, c))
        assert abs(k - N * p) < 4 * np.sqrt(N * p * (1 - p)), c


def test_crn_and_streams():
    a = fl.sample(500, SEED, 4, [0.0] * 500)
    b = fl.sample(500, SEED, 4, [0.0] * 500)
    c = fl.sample(500, SEED + 1, 4, [0.0] * 500)
    assert [v.vtype_xml() for v in a] == [v.vtype_xml() for v in b]
    assert [v.vtype_xml() for v in a] != [v.vtype_xml() for v in c]


def test_hdv_car_krauss(veh):
    h = by(veh, "hdv_car")
    tau = np.array([v.tau for v in h])
    asl = np.array([v.asl for v in h])
    sig = np.array([v.sigma for v in h])
    assert (tau >= asl).all() and tau.min() >= 0.2 and tau.max() <= 2.0
    assert set(np.round(asl * 10).astype(int)) <= set(range(1, 11))
    assert 0.1 <= sig.min() and sig.max() <= 1.0
    assert abs(np.median(asl) - 0.30) < 0.051 and abs(np.median(sig) - 0.30) < 0.02


def test_beta_tau_moments():
    a, b = fl.TAU_AB
    lo, hi = fl.TAU_RANGE
    mean = lo + (hi - lo) * a / (a + b)
    sd = (hi - lo) * np.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))
    assert abs(mean - 1.15) < 1e-9 and abs(sd - 0.43) < 1e-9 and a > b   # a > b: left-skewed, as in [1]


def test_speeds(veh):
    cars = [v for v in veh if v.cls in ("hdv_car", "acc", "cacc")]
    sf = np.array([v.sf for v in cars])
    assert abs(sf.mean() - 0.98) < 0.005 and abs(sf.std() - 0.12) < 0.005
    tr = by(veh, "truck")
    assert max(v.desired for v in tr) <= fl.TRUCK_MAX
    assert all(v.sf == 1.0 for v in by(veh, "alks"))


def test_dimensions(veh):
    cars = np.array([v.length for v in veh if v.cls != "truck"])
    assert abs(cars.mean() - 4.34) < 0.01 and abs(cars.std() - 0.36) < 0.02
    w = np.array([v.width for v in veh if v.cls != "truck"])
    assert w.min() >= 1.65 and w.max() <= 1.92
    tr = by(veh, "truck")
    assert all(15.5 <= v.length <= 16.5 and 2.50 <= v.width <= 2.55 for v in tr)


def test_cav_gaps(veh):
    for cls, table in (("acc", fl.ACC_TAU), ("cacc", fl.CACC_TAU)):
        t = np.array([v.tau for v in by(veh, cls)])
        for val, p in table:
            assert abs((t == val).mean() - p) < 0.03, (cls, val)
    assert all(v.tau == fl.ALKS_TAU for v in by(veh, "alks"))


def test_vtype_xml(veh):
    x = {c: by(veh, c)[0].vtype_xml() for c in fl.CLASSES}
    assert 'carFollowModel="Krauss"' in x["hdv_car"] and "actionStepLength" in x["hdv_car"]
    assert 'vClass="trailer"' in x["truck"] and 'maxSpeed="25"' in x["truck"]
    assert 'carFollowModel="ACC"' in x["acc"] and "collisionAvoidance" not in x["acc"]   # V164 default gains
    assert 'carFollowModel="CACC"' in x["cacc"]
    assert 'carFollowModel="ACC"' in x["alks"] and "gapClosingControlGainSpeed" not in x["alks"]


def test_bn4x_geometry():
    from v5b.p1c import plant as pl
    a, b = dict(pl.GEOMS["bn4"]["nodes"]), dict(pl.GEOMS["bn4x"]["nodes"])
    assert b["2"] - b["1"] == a["2"] - a["1"] + fl.UPSTREAM_EXTRA
    assert all(b[n] - b["2"] == a[n] - a["2"] for n in a if n != "1")   # downstream of edge 1 unchanged
    assert pl.GEOMS["bn4x"]["lanes"] == pl.GEOMS["bn4"]["lanes"]
