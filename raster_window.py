# -*- coding: utf-8 -*-
"""Pure raster window calculation and grid alignment utilities (no QGIS required)."""

from __future__ import annotations

import math
from typing import Any


def align_raster_window(
    bounds: tuple[float, float, float, float],
    transform: Any,
    raster_width: int,
    raster_height: int,
) -> Any:
    """Calculate an integer raster window anchored to the native pixel grid with 1-pixel buffer.

    Anchors the boundaries (col_off, row_off, width, height) strictly to integer
    indices of the GeoTIFF pixel grid, eliminating sub-pixel affine translation
    and implicit GDAL nearest-neighbor resampling.

    Args:
        bounds (tuple[float, float, float, float]): Bounding box (minx, miny, maxx, maxy).
        transform (Any): Raster affine transformation (Affine).
        raster_width (int): Full raster width in pixels.
        raster_height (int): Full raster height in pixels.

    Returns:
        Any: rasterio.windows.Window with integer coordinates cropped to raster dimensions.
    """
    import rasterio.windows

    minx, miny, maxx, maxy = bounds
    res_x: float = abs(transform.a)
    res_y: float = abs(transform.e)
    buf: float = max(res_x, res_y)

    raw_window = rasterio.windows.from_bounds(
        minx - buf,
        miny - buf,
        maxx + buf,
        maxy + buf,
        transform=transform,
    )
    col_off: int = math.floor(raw_window.col_off)
    row_off: int = math.floor(raw_window.row_off)
    width: int = math.ceil(raw_window.col_off + raw_window.width) - col_off
    height: int = math.ceil(raw_window.row_off + raw_window.height) - row_off

    int_window = rasterio.windows.Window(col_off, row_off, width, height)
    return int_window.crop(height=raster_height, width=raster_width)
