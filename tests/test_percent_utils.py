# -*- coding: utf-8 -*-
"""Unit tests for percentage normalisation (no QGIS required)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from percent_utils import normalize_class_areas, safe_percent  # noqa: E402


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


def test_normalize_class_areas_parity_infogeo() -> None:
    """Tests accounting closure with actual dataset from tabela_calculada.csv and infogeo."""
    # Raw UTM planar areas in m² (converted from hectares in tabela_calculada.csv)
    raw_areas_m2: dict[int, float] = {
        1: 757.8414 * 10_000.0,
        3: 1397.1694 * 10_000.0,
        4: 1.0646 * 10_000.0,
        6: 0.6877 * 10_000.0,
        8: 570.3832 * 10_000.0,
        10: 5.4550 * 10_000.0,
    }
    base_area_m2_ref: float = 2732.6054 * 10_000.0

    normalized_m2, total_norm_m2 = normalize_class_areas(raw_areas_m2, base_area_m2_ref)

    # 1. Total area must exactly match base area within float epsilon
    assert abs(total_norm_m2 - base_area_m2_ref) < 1e-6

    # 2. Each class rounded to 4 decimals in hectares must match tabela_calculada_infogeo.csv
    expected_ha: dict[int, float] = {
        1: 757.8426,
        3: 1397.1715,
        4: 1.0646,
        6: 0.6877,
        8: 570.3840,
        10: 5.4550,
    }
    for class_id, exp_ha in expected_ha.items():
        calc_ha = round(normalized_m2[class_id] / 10_000.0, 4)
        assert abs(calc_ha - exp_ha) <= 1e-4, f"Class {class_id}: expected {exp_ha}, got {calc_ha}"



def test_normalize_class_areas_preserves_partial_coverage() -> None:
    """Ensure partial raster coverages (> 0.5% deficit) are NOT scaled up."""
    areas_m2 = {1: 300_000.0, 2: 200_000.0}
    base_area_m2_ref = 1_000_000.0  # 50% coverage only

    normalized, total = normalize_class_areas(areas_m2, base_area_m2_ref)

    assert total == 500_000.0
    assert normalized == areas_m2


def test_normalize_class_areas_excess_discretization() -> None:
    """Ensure slight pixel over-discretization (> base_area) is scaled down to 100%."""
    base_area_m2_ref = 1_000_000.0
    areas_m2 = {1: 600_050.0, 2: 400_050.0}  # 1_000_100 m² (100.01%)

    normalized, total = normalize_class_areas(areas_m2, base_area_m2_ref)

    assert abs(total - base_area_m2_ref) < 1e-6
    assert abs(sum(normalized.values()) - base_area_m2_ref) < 1e-6


def test_normalize_class_areas_zero_and_empty() -> None:
    """Ensure defensive handling of zero base area and empty input."""
    assert normalize_class_areas({}, 1000.0) == ({}, 0.0)
    assert normalize_class_areas({1: 100.0}, 0.0) == ({1: 100.0}, 100.0)
    assert normalize_class_areas({1: 0.0}, 1000.0) == ({1: 0.0}, 0.0)

