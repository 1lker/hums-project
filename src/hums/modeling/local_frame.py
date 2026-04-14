"""PRD-002 · §11 — build a LocalFrame from a UTM footprint.

Origin = centroid. Rotation = aligned so the longest exterior edge becomes the
+X axis of the local frame (cleaner facade geometry + easier photo mapping).
When a block outline is provided, we prefer the longest edge that lies on the
block boundary ("street-facing"); otherwise the longest edge overall wins.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from shapely.geometry import Polygon

from ..common.prd import prd
from .building import LocalFrame, Point


@dataclass
class EdgeChoice:
    start_utm: Point
    end_utm: Point
    length_m: float
    is_street: bool

    @property
    def angle_rad(self) -> float:
        return math.atan2(self.end_utm[1] - self.start_utm[1],
                          self.end_utm[0] - self.start_utm[0])


@prd("002", "§11 LocalFrame")
class LocalFrameBuilder:
    BOUNDARY_TOL_M = 0.5  # edge within 0.5 m of block boundary → street-facing

    def __init__(self, block_outline: Polygon | None = None) -> None:
        self._block = block_outline

    def build(self, footprint_utm: Polygon) -> tuple[LocalFrame, list[Point]]:
        centroid = footprint_utm.centroid
        origin = (centroid.x, centroid.y)

        edge = self._longest_exterior_edge(footprint_utm)
        rotation_rad = edge.angle_rad  # we want this edge along +X → rotate by -angle

        local = []
        cos_r = math.cos(-rotation_rad)
        sin_r = math.sin(-rotation_rad)
        coords = list(footprint_utm.exterior.coords)
        if coords[0] == coords[-1]:
            coords = coords[:-1]
        for (x, y) in coords:
            dx = x - origin[0]
            dy = y - origin[1]
            lx = dx * cos_r - dy * sin_r
            ly = dx * sin_r + dy * cos_r
            local.append((round(lx, 4), round(ly, 4)))

        # Ensure CCW
        if _signed_area(local) < 0:
            local.reverse()

        frame = LocalFrame(origin_utm=origin, street_rotation_deg=round(math.degrees(rotation_rad), 3))
        return frame, local

    def _longest_exterior_edge(self, poly: Polygon) -> EdgeChoice:
        coords = list(poly.exterior.coords)
        best_street: EdgeChoice | None = None
        best_any: EdgeChoice | None = None
        for a, b in zip(coords, coords[1:]):
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            if length < 0.5:
                continue
            is_street = self._edge_on_block_boundary(a, b)
            choice = EdgeChoice(a, b, length, is_street)
            if best_any is None or length > best_any.length_m:
                best_any = choice
            if is_street and (best_street is None or length > best_street.length_m):
                best_street = choice
        chosen = best_street or best_any
        assert chosen is not None, "footprint has no usable edges"
        return chosen

    def _edge_on_block_boundary(self, a: Point, b: Point) -> bool:
        if self._block is None:
            return False
        from shapely.geometry import LineString
        edge = LineString([a, b])
        return edge.distance(self._block.exterior) <= self.BOUNDARY_TOL_M


def _signed_area(ring: list[Point]) -> float:
    s = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return s / 2.0
