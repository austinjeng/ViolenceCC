"""TRN-02: EarlyStopping semantics and NaN tolerance."""
import math

from src.utils.early_stopping import EarlyStopping


def test_patience_trigger():
    es = EarlyStopping(patience=10)
    # 10 non-improving epochs trip the stop
    es.step(0, 1.0)  # best
    dec = None
    for e in range(1, 11):
        dec = es.step(e, 2.0)  # never better than 1.0
        if e < 10:
            assert not dec["should_stop"]
    assert dec["should_stop"] is True


def test_best_resets_counter():
    es = EarlyStopping(patience=5)
    es.step(0, 1.0)
    es.step(1, 1.5)  # counter=1
    es.step(2, 1.2)  # counter=2
    dec = es.step(3, 0.5)  # improvement -> counter resets, best_epoch=3
    assert dec["is_best"] is True
    assert es.counter == 0
    assert es.best_epoch == 3
    assert es.best_loss == 0.5


def test_nan_handling():
    es = EarlyStopping(patience=5)
    es.step(0, 1.0)
    dec = es.step(1, math.nan)
    assert dec["is_best"] is False
    assert es.counter == 0  # NaN does not increment
    assert es.best_loss == 1.0  # best unchanged


def test_nan_streak_halts():
    es = EarlyStopping(patience=100)
    es.step(0, 1.0)
    es.step(1, math.nan)
    es.step(2, math.nan)
    dec = es.step(3, math.nan)  # 3rd consecutive NaN
    assert dec["should_stop"] is True
