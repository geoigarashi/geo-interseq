# -*- coding: utf-8 -*-
"""Pure (QGIS-independent) UTM zone selection for GeoInterseQ.

Resolves which UTM projection (SIRGAS 2000 inside its official coverage,
WGS 84 elsewhere) should be used to measure planar areas for a given
location, and flags extents that straddle a zone meridian.
"""

import math
from dataclasses import dataclass

# SIRGAS 2000 / UTM official EPSG ranges (verified against the EPSG registry):
#   South: zones 17S..25S -> EPSG 31977..31985  (31960 + zone)
#   North: zones 11N..22N -> EPSG 31965..31976  (31954 + zone)
_SIRGAS_SOUTH_ZONES: range = range(17, 26)
_SIRGAS_NORTH_ZONES: range = range(11, 23)
_SIRGAS_SOUTH_BASE: int = 31960
_SIRGAS_NORTH_BASE: int = 31954

_WGS84_SOUTH_BASE: int = 32700
_WGS84_NORTH_BASE: int = 32600


@dataclass(frozen=True)
class UtmZone:
    """Resolved UTM zone.

    Attributes:
        epsg: EPSG code of the projected CRS.
        zone: UTM zone number (1..60).
        is_south: True for the southern hemisphere.
        datum: Datum name used in the label (``SIRGAS 2000`` or ``WGS 84``).
        is_cross_zone: True when the extent straddles a zone meridian.
        zone_min: Zone containing the westernmost longitude of the extent.
        zone_max: Zone containing the easternmost longitude of the extent.
    """

    epsg: int
    zone: int
    is_south: bool
    datum: str
    is_cross_zone: bool
    zone_min: int
    zone_max: int

    @property
    def authid(self) -> str:
        """Authority identifier, e.g. ``EPSG:31982``."""
        return f'EPSG:{self.epsg}'

    @property
    def base_label(self) -> str:
        """Label without the border flag, e.g. ``SIRGAS 2000 / UTM 22S``."""
        return f"{self.datum} / UTM {self.zone}{'S' if self.is_south else 'N'}"

    @property
    def label(self) -> str:
        """Traceability label, with ``(borda)`` appended for cross-zone extents."""
        return f'{self.base_label} (borda)' if self.is_cross_zone else self.base_label


def zone_number(lon: float) -> int:
    """Returns the UTM zone number (1..60) that contains a longitude.

    Args:
        lon: Longitude in decimal degrees (WGS 84 / SIRGAS 2000).

    Returns:
        int: Zone number, clamped to the 1..60 range (lon = 180 belongs to zone 60).
    """
    return min(60, max(1, int(math.floor((lon + 180.0) / 6.0)) + 1))


def resolve_utm_zone(lon_c: float, lat_c: float, lon_min: float, lon_max: float) -> UtmZone:
    """Selects the UTM projection for a location and detects zone-straddling extents.

    Args:
        lon_c: Longitude of the reference point (centroid) in degrees.
        lat_c: Latitude of the reference point (centroid) in degrees.
        lon_min: Westernmost longitude of the extent in degrees.
        lon_max: Easternmost longitude of the extent in degrees.

    Returns:
        UtmZone: Zone chosen from the reference point. SIRGAS 2000 is used inside
        its official coverage; WGS 84 / UTM is the global fallback.
    """
    zone: int = zone_number(lon_c)
    is_south: bool = lat_c < 0
    zone_min: int = zone_number(min(lon_min, lon_max))
    zone_max: int = zone_number(max(lon_min, lon_max))

    if is_south and zone in _SIRGAS_SOUTH_ZONES:
        epsg, datum = _SIRGAS_SOUTH_BASE + zone, 'SIRGAS 2000'
    elif not is_south and zone in _SIRGAS_NORTH_ZONES:
        epsg, datum = _SIRGAS_NORTH_BASE + zone, 'SIRGAS 2000'
    else:
        base: int = _WGS84_SOUTH_BASE if is_south else _WGS84_NORTH_BASE
        epsg, datum = base + zone, 'WGS 84'

    return UtmZone(
        epsg=epsg, zone=zone, is_south=is_south, datum=datum,
        is_cross_zone=zone_min != zone_max, zone_min=zone_min, zone_max=zone_max,
    )
