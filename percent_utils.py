# -*- coding: utf-8 -*-
"""Pure helpers for percentage computation in GeoInterseQ."""

# Relative tolerance under which part/whole is considered exactly 1. Planar overlay
# (GEOS noding) leaves ~1e-13 relative noise between the area of an intersection and
# the area of the geometry that fully contains it.
_SNAP_REL_TOL: float = 1e-9


def safe_percent(part_m2: float, whole_m2: float) -> float:
    """Computes ``part / whole * 100`` free of floating-point overlay noise.

    The ratio is clamped to [0, 100] (an intersection can never exceed the
    geometry it is measured against) and snapped to exactly 100 when the part
    equals the whole within ``1e-9`` relative tolerance.

    Args:
        part_m2: Intersection area in square metres.
        whole_m2: Reference area (denominator) in square metres.

    Returns:
        float: Percentage in [0, 100]; 0.0 when ``whole_m2`` is not positive.
    """
    if whole_m2 <= 0:
        return 0.0
    ratio: float = part_m2 / whole_m2
    if abs(ratio - 1.0) <= _SNAP_REL_TOL:
        return 100.0
    return min(100.0, max(0.0, ratio * 100.0))


def normalize_class_areas(
    areas_by_class: dict[int, float],
    base_area_ref: float,
    max_discretization_ratio: float = 0.005,
) -> tuple[dict[int, float], float]:
    """Normalizes class areas to match base reference area within discretization tolerance.

    Applies bilateral proportional closing (accounting closure) when the raster
    fully covers the base geometry (discretization residual <= 0.5% due to UTM
    projection vertex densification) or when numerical discretization exceeds
    the base area. Prevents scaling when coverage is partial (ratio > 0.5%).

    Args:
        areas_by_class: Mapping of class IDs to measured areas in m² (or ha).
        base_area_ref: Reference planar base area in m² (or ha).
        max_discretization_ratio: Relative threshold (default 0.005 = 0.5%).

    Returns:
        tuple[dict[int, float], float]: Tuple containing:
            - Normalized areas dictionary.
            - Total area of classes after normalization.
    """
    total_area: float = float(sum(areas_by_class.values()))
    if base_area_ref > 0.0 and total_area > 0.0:
        discretization_ratio: float = abs(base_area_ref - total_area) / base_area_ref
        if discretization_ratio <= max_discretization_ratio or total_area > base_area_ref:
            factor: float = base_area_ref / total_area
            normalized: dict[int, float] = {k: v * factor for k, v in areas_by_class.items()}
            return normalized, float(sum(normalized.values()))
    return areas_by_class, total_area

