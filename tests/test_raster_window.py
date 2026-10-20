# -*- coding: utf-8 -*-
"""Unit tests for raster window grid alignment."""

import math
import sys
from pathlib import Path

import affine
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raster_window import align_raster_window  # noqa: E402


@pytest.fixture
def sample_transform() -> affine.Affine:
    """Standard north-up 10m resolution affine transform."""
    return affine.Affine(10.0, 0.0, 300000.0, 0.0, -10.0, 7000000.0)


def test_align_raster_window_types_are_integer(sample_transform: affine.Affine) -> None:
    """Ensure offsets and dimensions are strictly integer types."""
    # Floating bounds (e.g. from polygon coordinates)
    bounds = (300123.45, 6998765.43, 301234.56, 6999876.54)
    win = align_raster_window(bounds, sample_transform, 1000, 1000)

    assert isinstance(win.col_off, int)
    assert isinstance(win.row_off, int)
    assert isinstance(win.width, int)
    assert isinstance(win.height, int)
    assert win.width > 0
    assert win.height > 0


def test_align_raster_window_affine_origin_invariance(sample_transform: affine.Affine) -> None:
    """Ensure window affine origin perfectly aligns with the native raster grid."""
    import rasterio.windows

    bounds = (300123.45, 6998765.43, 301234.56, 6999876.54)
    win = align_raster_window(bounds, sample_transform, 1000, 1000)

    win_affine = rasterio.windows.transform(win, sample_transform)
    # The origin (0, 0) of the window affine must exactly equal transform * (col_off, row_off)
    expected_origin = sample_transform * (win.col_off, win.row_off)
    actual_origin = win_affine * (0, 0)

    assert math.isclose(actual_origin[0], expected_origin[0], abs_tol=1e-9)
    assert math.isclose(actual_origin[1], expected_origin[1], abs_tol=1e-9)


def test_align_raster_window_spatial_coverage_includes_buffer(sample_transform: affine.Affine) -> None:
    """Ensure spatial extent of window covers the original bounds plus the 1-pixel buffer."""
    import rasterio.windows

    bounds = (300500.25, 6995000.75, 300600.80, 6995100.10)
    win = align_raster_window(bounds, sample_transform, 2000, 2000)

    win_bounds = rasterio.windows.bounds(win, sample_transform)
    # win_bounds: (left, bottom, right, top)
    assert win_bounds[0] <= bounds[0] - 10.0
    assert win_bounds[1] <= bounds[1] - 10.0
    assert win_bounds[2] >= bounds[2] + 10.0
    assert win_bounds[3] >= bounds[3] + 10.0


def test_align_raster_window_crop_within_raster_limits(sample_transform: affine.Affine) -> None:
    """Ensure crop clamps cleanly when bounds extend beyond upper-left raster boundary."""
    # Bounds that start left/above the raster origin
    bounds = (299900.0, 6999900.0, 300100.0, 7000100.0)
    win = align_raster_window(bounds, sample_transform, 100, 100)

    assert isinstance(win.col_off, int)
    assert isinstance(win.row_off, int)
    assert win.col_off == 0
    assert win.row_off == 0
    assert win.width > 0
    assert win.height > 0
    assert win.col_off + win.width <= 100
    assert win.row_off + win.height <= 100


def test_align_raster_window_completely_outside(sample_transform: affine.Affine) -> None:
    """Ensure window returns zero dimensions when bounds do not intersect the raster."""
    # Completely to the left
    bounds = (100000.0, 6000000.0, 100100.0, 6000100.0)
    win = align_raster_window(bounds, sample_transform, 500, 500)

    assert win.width <= 0 or win.height <= 0
