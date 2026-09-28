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
