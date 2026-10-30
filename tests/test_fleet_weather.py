"""V204 weather states: same vehicles in every state, humans scaled, CAVs untouched; the monotone fit."""
import pytest

from v5b.fleet import fleet as fl
from v5b.fleet.weather import pava_decreasing


@pytest.fixture
def knobs(monkeypatch):
    for k in ("WEATHER", "WEATHER_G", "WEATHER_CAV"):
        monkeypatch.setattr(fl, k, getattr(fl, k))


def _fleet(state, g=None, cav=False):
    fl.WEATHER, fl.WEATHER_G, fl.WEATHER_CAV = state, g, cav
    return fl.sample(4000, 7400000, 3, [float(i) for i in range(4000)])


def test_states_share_draws_and_scale_humans_only(knobs):
    dry, wet = _fleet("dry"), _fleet("medium", 1.2)
    saf = fl.WEATHER_STATES["medium"][1]
    for d, w in zip(dry, wet):
        assert (d.cls, d.depart, d.lane, d.length, d.width, d.sf, d.sigma, d.asl) == \
               (w.cls, w.depart, w.lane, w.length, w.width, w.sf, w.sigma, w.asl)
        if d.cls == "hdv_car":
            assert abs(w.tau - 1.2 * d.tau) <= 5e-4 + 1e-9 and w.tau >= w.asl
        elif d.cls == "truck":
            assert d.tau is None and w.tau == 1.2
        else:
            assert w.tau == d.tau and w.max_speed is None
        if d.cls in ("hdv_car", "truck"):
            assert d.max_speed is None and abs(w.max_speed - saf * d.desired) <= 5e-4 + 1e-9


def test_vtype_xml(knobs):
    dry, wet = _fleet("dry"), _fleet("heavy", 1.3)
    tr = next(i for i, v in enumerate(dry) if v.cls == "truck")
    car = next(i for i, v in enumerate(dry) if v.cls == "hdv_car")
    assert 'maxSpeed="25"' in dry[tr].vtype_xml() and "tau" not in dry[tr].vtype_xml()
    assert "maxSpeed" not in dry[car].vtype_xml()
    assert 'tau="1.300"' in wet[tr].vtype_xml() and f'maxSpeed="{wet[tr].max_speed:g}"' in wet[tr].vtype_xml()
    assert f'maxSpeed="{wet[car].max_speed:.3f}"' in wet[car].vtype_xml()


def test_cav_bound(knobs):
    wet = _fleet("medium", 1.2, cav=True)
    dry = _fleet("dry")
    for d, w in zip(dry, wet):
        if d.cls in ("acc", "cacc", "alks"):
            assert abs(w.tau - round(1.2 * d.tau, 3)) < 1e-9 and w.max_speed is not None


def test_pava():
    assert pava_decreasing([1.0, 0.9, 0.95, 0.8]) == pytest.approx([1.0, 0.925, 0.925, 0.8])
    assert pava_decreasing([0.9, 0.95, 1.0]) == pytest.approx([0.95, 0.95, 0.95])
