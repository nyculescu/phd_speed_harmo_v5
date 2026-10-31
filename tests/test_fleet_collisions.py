"""V211 collision rule: one row per event with its smallest bumper distance; contacts versus minGap intrusions."""
from v5b.fleet.day import _first_steps, contact_counts


def _c(t, bumper, pair=("a", "b")):
    return {"t": t, "collider": pair[0], "victim": pair[1], "bumper": bumper}


def test_event_keeps_smallest_bumper():
    ev = _first_steps([_c(10.0, 2.4), _c(10.1, 2.36), _c(10.2, 2.5), _c(20.0, 1.0)])
    assert [e["t"] for e in ev] == [10.0, 20.0]
    assert [e["bumper"] for e in ev] == [2.36, 1.0]


def test_missing_bumper_makes_the_event_unknown():
    ev = _first_steps([_c(10.0, 2.4), _c(10.1, None)])
    assert ev[0]["bumper"] is None


def test_first_row_is_not_mutated():
    rows = [_c(10.0, 2.4), _c(10.1, 2.0)]
    _first_steps(rows)
    assert rows[0]["bumper"] == 2.4


def test_contact_counts():
    ev = [{"bumper": 2.36}, {"bumper": 0.0}, {"bumper": -0.2}, {"bumper": None}, {}]
    assert contact_counts(ev) == {"contacts": 4, "mingap_intrusions": 1}
