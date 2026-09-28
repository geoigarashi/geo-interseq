# -*- coding: utf-8 -*-
"""QGIS glue for planar UTM area measurement in GeoInterseQ.

Provides zone detection from QGIS geometries, cached coordinate transforms and
a base-layer footprint that can be materialised in any UTM zone without
round-tripping through EPSG:4326.
"""

from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsCoordinateTransformContext, QgsGeometry, QgsPointXY, QgsRectangle,
)

from .utm_zone import UtmZone, resolve_utm_zone

WGS84_AUTHID: str = 'EPSG:4326'


def wgs84_crs() -> QgsCoordinateReferenceSystem:
    """Returns a fresh EPSG:4326 CRS instance."""
    return QgsCoordinateReferenceSystem(WGS84_AUTHID)


def union_geometries(geoms: list[QgsGeometry]) -> QgsGeometry:
    """Dissolves geometries sequentially and repairs the result.

    Args:
        geoms: Non-empty list of geometries in the same CRS.

    Returns:
        QgsGeometry: Valid union of all inputs.
    """
    merged: QgsGeometry = geoms[0]
    for g in geoms[1:]:
        merged = merged.combine(g)
    return merged.makeValid()


def zone_for_wgs84_extent(
    center: QgsPointXY, extent: QgsRectangle
) -> UtmZone:
    """Resolves the UTM zone from a reference point and extent in EPSG:4326.

    Args:
        center: Reference point (lon/lat degrees).
        extent: Extent (lon/lat degrees) used to detect zone straddling.

    Returns:
        UtmZone: Selected zone.
    """
    return resolve_utm_zone(center.x(), center.y(), extent.xMinimum(), extent.xMaximum())


def zone_for_geometry(
    geom: QgsGeometry, source_crs: QgsCoordinateReferenceSystem,
    ctx: QgsCoordinateTransformContext,
) -> UtmZone:
    """Resolves the optimal UTM zone for a geometry from its centroid.

    Args:
        geom: Geometry (or collection) in ``source_crs``.
        source_crs: CRS of the geometry.
        ctx: QGIS coordinate transform context.

    Returns:
        UtmZone: Zone of the geometry centroid; ``is_cross_zone`` reflects its extent.

    Raises:
        QgsCsException: If the geometry cannot be transformed to EPSG:4326.
    """
    to_wgs = QgsCoordinateTransform(source_crs, wgs84_crs(), ctx)
    bbox: QgsRectangle = to_wgs.transformBoundingBox(geom.boundingBox())
    centroid: QgsGeometry = geom.centroid()
    if centroid.isNull() or centroid.isEmpty():
        center: QgsPointXY = bbox.center()
    else:
        center = to_wgs.transform(centroid.asPoint())
    return zone_for_wgs84_extent(center, bbox)


class UtmTransformCache:
    """Caches CRS objects and transforms between a source CRS, UTM zones and the output CRS."""

    def __init__(
        self, source_crs: QgsCoordinateReferenceSystem,
        out_crs: QgsCoordinateReferenceSystem, ctx: QgsCoordinateTransformContext,
    ) -> None:
        """Initialises the cache.

        Args:
            source_crs: CRS of the geometries to be measured.
            out_crs: CRS of the generated output layers (project CRS).
            ctx: QGIS coordinate transform context.
        """
        self._source_crs = source_crs
        self._out_crs = out_crs
        self._ctx = ctx
        self._crs: dict[int, QgsCoordinateReferenceSystem] = {}
        self._to_utm: dict[int, QgsCoordinateTransform] = {}
        self._from_utm: dict[int, QgsCoordinateTransform] = {}

    def crs(self, zone: UtmZone) -> QgsCoordinateReferenceSystem:
        """Returns the projected CRS of a zone."""
        if zone.epsg not in self._crs:
            self._crs[zone.epsg] = QgsCoordinateReferenceSystem(zone.authid)
        return self._crs[zone.epsg]

    def to_utm(self, zone: UtmZone) -> QgsCoordinateTransform:
        """Returns the source CRS -> UTM transform for a zone."""
        if zone.epsg not in self._to_utm:
            self._to_utm[zone.epsg] = QgsCoordinateTransform(
                self._source_crs, self.crs(zone), self._ctx
            )
        return self._to_utm[zone.epsg]

    def from_utm(self, zone: UtmZone) -> QgsCoordinateTransform:
        """Returns the UTM -> output CRS transform for a zone."""
        if zone.epsg not in self._from_utm:
            self._from_utm[zone.epsg] = QgsCoordinateTransform(
                self.crs(zone), self._out_crs, self._ctx
            )
        return self._from_utm[zone.epsg]

    def project_to_utm(self, geom: QgsGeometry, zone: UtmZone) -> QgsGeometry:
        """Returns a repaired copy of ``geom`` projected to the zone's UTM CRS.

        Raises:
            QgsCsException: If the transformation fails.
        """
        out: QgsGeometry = QgsGeometry(geom)
        out.transform(self.to_utm(zone))
        return out.makeValid()

    def utm_to_output(self, geom: QgsGeometry, zone: UtmZone) -> QgsGeometry:
        """Returns a copy of a UTM geometry reprojected to the output CRS.

        Raises:
            QgsCsException: If the transformation fails.
        """
        out: QgsGeometry = QgsGeometry(geom)
        out.transform(self.from_utm(zone))
        return out


class BaseFootprint:
    """Base-layer geometries kept in their native CRS and materialised per UTM zone."""

    def __init__(
        self, native_geoms: list[QgsGeometry], source_crs: QgsCoordinateReferenceSystem,
        ctx: QgsCoordinateTransformContext,
    ) -> None:
        """Builds the footprint and its EPSG:4326 union (used for zone detection and filters).

        Args:
            native_geoms: Non-empty list of base geometries in ``source_crs``.
            source_crs: Native CRS of the base layer.
            ctx: QGIS coordinate transform context.

        Raises:
            QgsCsException: If a geometry cannot be transformed to EPSG:4326.
        """
        self.native_geoms: list[QgsGeometry] = native_geoms
        self.source_crs: QgsCoordinateReferenceSystem = source_crs
        self._ctx = ctx
        self._wgs84 = wgs84_crs()
        self._cache = UtmTransformCache(source_crs, self._wgs84, ctx)
        self._zone_geoms: dict[int, QgsGeometry] = {}

        to_wgs = QgsCoordinateTransform(source_crs, self._wgs84, ctx)
        wgs_geoms: list[QgsGeometry] = []
        for g in native_geoms:
            g2 = QgsGeometry(g)
            g2.transform(to_wgs)
            wgs_geoms.append(g2)
        self.wgs84_union: QgsGeometry = union_geometries(wgs_geoms)

    def zone(self) -> UtmZone:
        """Returns the UTM zone of the whole base footprint (centroid based)."""
        return zone_for_geometry(self.wgs84_union, self._wgs84, self._ctx)

    def in_zone(self, zone: UtmZone) -> QgsGeometry:
        """Returns the dissolved base geometry projected to a UTM zone (cached).

        Args:
            zone: Target UTM zone.

        Returns:
            QgsGeometry: Valid union of the base geometries in metres.

        Raises:
            QgsCsException: If the transformation fails.
        """
        if zone.epsg not in self._zone_geoms:
            projected: list[QgsGeometry] = [
                self._cache.project_to_utm(g, zone) for g in self.native_geoms
            ]
            self._zone_geoms[zone.epsg] = union_geometries(projected)
        return self._zone_geoms[zone.epsg]

    def area_in_zone(self, zone: UtmZone) -> float:
        """Returns the planar base area (m²) in a UTM zone."""
        return self.in_zone(zone).area()
