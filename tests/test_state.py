"""Tests for hyprop.core.state (TimeHistory)."""

import numpy as np
import pytest

from hyprop.core.state import TimeHistory


def test_record_and_read_back():
    history = TimeHistory()
    for i in range(5):
        history.record(t=0.01 * i, thrust=1000.0 - i, pc=3.5e6)
    assert len(history) == 5
    assert history["t"][2] == pytest.approx(0.02)
    assert isinstance(history["thrust"], np.ndarray)


def test_unknown_channel_rejected():
    history = TimeHistory()
    with pytest.raises(KeyError):
        history.record(t=0.0, flux_capacitor=1.21)


def test_dataframe_export():
    history = TimeHistory()
    history.record(t=0.0, thrust=1.0)
    history.record(t=0.1, thrust=2.0)
    df = history.to_dataframe()
    assert list(df.columns) == ["t", "thrust"]
    assert len(df) == 2
