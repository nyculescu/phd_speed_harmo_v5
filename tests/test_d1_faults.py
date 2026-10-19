"""Screen D1 Rule 2 fault layer, onset window, RF fill-in math and determinism hooks (no SUMO)."""
import numpy as np
import pytest

from v5b.d1.faults import ANY, FAULTS, DetectorFault, onset_time, ratio_fit, rf_fill, saturated_count

LANES = {"3_0": 140.0, "3_1": 140.0, "3_2": 140.0, "3_3": 140.0, "4_0": 280.0, "4_1": 280.0, "5_0": 155.0}


def test_saturated_count_is_jam_count_of_edge_4():
    assert saturated_count(LANES) == pytest.approx(80.0)


@pytest.mark.parametrize("kind", FAULTS)
def test_fault_inactive_before_onset_true_reading(kind):
    f = DetectorFault(kind, onset=100.0, saturated=80.0, seed=7_400_000)
    assert not f.active(99.0) and f.read(99.0, 12) == 12.0


def test_fault_types_after_onset():
    t = 100.0
    assert DetectorFault("stuck_off", t, 80.0, 1).read(t, 12) == 0.0
    assert DetectorFault("stuck_on", t, 80.0, 1).read(t + 500, 3) == 80.0
    assert DetectorFault("dropout", t, 80.0, 1).read(t, 12) is None
    assert not DetectorFault("none", t, 80.0, 1).active(1e9)


def test_noisy_multiplicative_sigma_50pct_seeded_nonnegative():
    f = DetectorFault("noisy", 0.0, 80.0, 7_400_001)
    x = np.array([f.read(1.0, 10.0) for _ in range(20000)]) / 10.0
    assert x.min() >= 0.0
    assert abs(x.mean() - 1.0) < 0.02 and abs(x.std() - 0.5) < 0.03
    g = DetectorFault("noisy", 0.0, 80.0, 7_400_001)
    assert [g.read(1.0, 10.0) for _ in range(5)] == list(10.0 * x[:5])        # same seed, same stream
    h = DetectorFault("noisy", 0.0, 80.0, 7_400_002)
    assert [h.read(1.0, 10.0) for _ in range(5)] != list(10.0 * x[:5])


def test_any_fault_refuses_reading_after_onset():
    f = DetectorFault(ANY, 50.0, 80.0, 1)
    assert f.read(10.0, 5) == 5.0 and f.active(50.0)
    with pytest.raises(RuntimeError):
        f.read(50.0, 5)
    with pytest.raises(ValueError):
        DetectorFault("smoke", 0.0, 80.0, 1)


def test_onset_uniform_in_first_third_of_control_and_seeded():
    on = np.array([onset_time(s, 40.0, 900.0) for s in range(7_400_000, 7_402_000)])
    assert on.min() >= 40.0 and on.max() < 340.0
    assert on.min() < 45.0 and on.max() > 335.0 and abs(on.mean() - 190.0) < 6.0
    assert onset_time(7_400_123, 40.0, 900.0) == onset_time(7_400_123, 40.0, 900.0)


def test_rf_ratio_of_sums_and_fill_in():
    assert ratio_fit([2, 4, 0], [3, 5, 1]) == pytest.approx(9 / 6)
    assert rf_fill(1.5, 4) == pytest.approx(6.0)
    assert rf_fill(ratio_fit([10, 20], [5, 10]), 30) == pytest.approx(15.0)
    with pytest.raises(ValueError):
        ratio_fit([0, 0], [1, 2])
