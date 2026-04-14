"""PRD-002 · §7 — sector the church courtyard into 6 interior stub polygons.

Strategy: take block outline, subtract all traced parcel polygons + church
polygon → residual interior polygon(s). For each of the 6 INT-* parcels,
generate a small rectangular stub near the church boundary in the sector
implied by its Excel zone label. Stubs are clearly provisional.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from shapely.geometry import Polygon, Point as ShpPoint, box
from shapely.ops import unary_union

from ..common.prd import prd


@dataclass
class SectorSpec:
    parcel_id: str
    angle_deg_from_church: float   # 0 = east, 90 = north (math convention)
    size_m: tuple[float, float] = (4.0, 5.0)   # (w along tangent, d radial)
    offset_m: float = 2.5          # distance from church boundary outward


DEFAULT_SECTORS: list[SectorSpec] = [
    SectorSpec("INT-N1", angle_deg_from_church=115),
    SectorSpec("INT-N2", angle_deg_from_church=90),
    SectorSpec("INT-N3", angle_deg_from_church=65),
    SectorSpec("INT-E2", angle_deg_from_church=30),
    SectorSpec("INT-S1", angle_deg_from_church=-75),
    SectorSpec("INT-S2", angle_deg_from_church=-50),
]


@prd("002", "§7 InteriorSectoriser")
class InteriorSectoriser:
    def __init__(self, block_outline: Polygon, traced_parcels: list[Polygon], church: Polygon) -> None:
        self._block = block_outline
        self._church = church
        try:
            occupied = unary_union(traced_parcels + [church])
            self._residual = block_outline.difference(occupied)
        except Exception:
            self._residual = block_outline
        self._church_centroid = church.centroid

    def generate(self, specs: list[SectorSpec] = DEFAULT_SECTORS) -> dict[str, Polygon]:
        church_outline = self._church.exterior
        results: dict[str, Polygon] = {}
        for spec in specs:
            theta = math.radians(spec.angle_deg_from_church)
            # Cast a ray from church centroid outward to find a base point on church boundary.
            ray_end = ShpPoint(
                self._church_centroid.x + math.cos(theta) * 100,
                self._church_centroid.y + math.sin(theta) * 100,
            )
            from shapely.geometry import LineString
            ray = LineString([self._church_centroid, ray_end])
            inter = ray.intersection(church_outline)
            if inter.is_empty:
                continue
            base_point = _farthest_from_center(inter, self._church_centroid)
            # push outward by offset
            cx = base_point.x + math.cos(theta) * spec.offset_m
            cy = base_point.y + math.sin(theta) * spec.offset_m
            w, d = spec.size_m
            # axis-aligned rectangle for simplicity; PRD-003 can rotate by tangent if desired
            rect = box(cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2)
            # clip by residual so stubs don't overlap traced parcels / church
            clipped = rect.intersection(self._residual)
            if clipped.is_empty or clipped.area < 1.0:
                # fallback: keep the unclipped rectangle so there is at least a placeholder
                clipped = rect
            if hasattr(clipped, "geoms"):
                # pick the largest piece
                clipped = max(clipped.geoms, key=lambda g: g.area)
            if clipped.geom_type == "Polygon":
                results[spec.parcel_id] = clipped
        return results


def _farthest_from_center(geom, center):
    if geom.geom_type == "Point":
        return geom
    if hasattr(geom, "geoms"):
        pts = [p for g in geom.geoms for p in (g.coords if hasattr(g, "coords") else [])]
    else:
        pts = list(geom.coords)
    if not pts:
        return geom.centroid
    pts = [ShpPoint(*p) for p in pts]
    return max(pts, key=lambda p: p.distance(center))
