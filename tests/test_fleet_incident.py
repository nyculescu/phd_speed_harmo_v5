"""V199 passing zone: a short incident run on the straight calibration road."""
import pytest

pytest.importorskip("libsumo")

from v5b.fleet import fleet as fl, incident  # noqa: E402


@pytest.fixture
def short(monkeypatch):
    for k in ("SHARES", "HDV_TAU_SCALE", "HDV_ASL_SCALE", "INCIDENT_TAU_FACTOR"):
        monkeypatch.setattr(fl, k, getattr(fl, k))      # run_one sets plant knobs; restore them afterwards
    monkeypatch.setattr(fl, "CAV_MODELS", dict(fl.CAV_MODELS))
    monkeypatch.setattr(incident, "WARM", 60.0)
    monkeypatch.setattr(incident, "HOLD", 180.0)
    monkeypatch.setattr(incident, "SKIP", 0.0)


def test_zone_slows_humans_only_when_active(short, tmp_path):
    on = incident.run_one(7400000, 2.0, "inc3", 0, 100.0, tmp_path / "on")
    off = incident.run_one(7400000, 1.0, "inc3", 0, 100.0, tmp_path / "off")
    assert on["t_crash"] is not None and on["slowed"] > 0 and off["slowed"] == 0
    assert on["collisions"] == off["collisions"] == 0 and on["sumo_errors"] == 0
    assert on["discharge_vph"] < off["discharge_vph"]
