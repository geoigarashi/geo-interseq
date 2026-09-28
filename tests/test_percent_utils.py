# -*- coding: utf-8 -*-
"""Unit tests for percentage normalisation (no QGIS required)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from percent_utils import safe_percent  # noqa: E402


def test_snaps_overlay_noise_to_100() -> None:
    whole = 1_234_567.891
    assert safe_percent(whole * (1 - 1.8e-13), whole) == 100.0
    assert safe_percent(whole * (1 + 1.8e-13), whole) == 100.0


def test_regular_and_edge_values() -> None:
    assert safe_percent(25.0, 100.0) == 25.0
    assert safe_percent(0.0, 100.0) == 0.0
    assert safe_percent(10.0, 0.0) == 0.0
    assert safe_percent(150.0, 100.0) == 100.0


def test_small_real_difference_is_kept() -> None:
    assert 99.98 < safe_percent(99.99, 100.0) < 100.0
