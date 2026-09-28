# -*- coding: utf-8 -*-
"""Unit tests for the pure UTM zone selection (no QGIS required)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utm_zone import resolve_utm_zone, zone_number  # noqa: E402


@pytest.mark.parametrize(
    'lon, lat, epsg, label',
    [
        (-51.0, -22.0, 31982, 'SIRGAS 2000 / UTM 22S'),   # zone 22S
        (-57.0, -15.0, 31981, 'SIRGAS 2000 / UTM 21S'),   # zone 21S
        (-45.0, -23.0, 31983, 'SIRGAS 2000 / UTM 23S'),   # zone 23S
        (-61.0, 3.0, 31974, 'SIRGAS 2000 / UTM 20N'),     # zone 20N (Roraima)
        (-52.0, 1.0, 31976, 'SIRGAS 2000 / UTM 22N'),     # zone 22N (Amapá)
        (10.0, 45.0, 32632, 'WGS 84 / UTM 32N'),          # outside SIRGAS coverage
        (150.0, -30.0, 32756, 'WGS 84 / UTM 56S'),
    ],
)
def test_zone_and_epsg(lon: float, lat: float, epsg: int, label: str) -> None:
    z = resolve_utm_zone(lon, lat, lon, lon)
    assert z.epsg == epsg
    assert z.label == label
    assert not z.is_cross_zone


def test_cross_zone_flag_at_minus_54() -> None:
    # Meridian -54 separates zones 21 and 22.
    z = resolve_utm_zone(-53.9, -25.0, -54.1, -53.7)
    assert z.is_cross_zone
    assert (z.zone_min, z.zone_max) == (21, 22)
    assert z.zone == 22
    assert z.label == 'SIRGAS 2000 / UTM 22S (borda)'


def test_zone_number_bounds() -> None:
    assert zone_number(-180.0) == 1
    assert zone_number(180.0) == 60
    assert zone_number(-54.0) == 22
