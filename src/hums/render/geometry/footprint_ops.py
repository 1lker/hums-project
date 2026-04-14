"""PRD-003 · §6.1 — footprint utilities.

Shapely does the heavy lifting; thin wrappers give us clearer call sites in
the extruder + roof strategies.
"""
from __future__ import annotations
from typing import Sequence

from shapely.geometry import Polygon

from ...common.prd import prd

Point = tuple[float, float]


@prd("003", "§6.1 footprint_ops")
def to_polygon(ring: Sequence[Point]) -> Polygon:
    poly = Polygon(ring)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def inset(ring: Sequence[Point], distance_m: float) -> list[Point]:
    """Inset a CCW ring inward by ``distance_m``. Returns [] if the inset collapses."""
    poly = to_polygon(ring)
    inner = poly.buffer(-distance_m, join_style=2)
    if inner.is_empty or inner.geom_type != "Polygon":
        return []
    coords = list(inner.exterior.coords)
    if coords and coords[0] == coords[-1]:
        coords = coords[:-1]
    return [(round(x, 4), round(y, 4)) for x, y in coords]


def centroid(ring: Sequence[Point]) -> Point:
    p = to_polygon(ring).centroid
    return (p.x, p.y)


def area(ring: Sequence[Point]) -> float:
    return to_polygon(ring).area
