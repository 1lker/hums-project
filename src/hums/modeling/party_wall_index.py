"""PRD-004 · Party-wall detector.

Two adjacent parcel polygons typically share a segment of their outline
(the common wall between neighbour buildings). No windows or doors can
exist on such a shared edge. This index pre-computes a set of
``(midpoint, direction)`` fingerprints from every traced polygon's edges
and exposes a cheap lookup: *is this edge shared with any other parcel?*

Adjacency tolerance: 0.8 m midpoint distance, or a 1.2 m gap between
parallel/overlapping edges, within 15° of the same edge direction. This
handles imperfect traces that should be bitişik but do not quite share
vertices.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

from ..common.prd import prd


@dataclass(frozen=True)
class EdgeKey:
    mid_x: float
    mid_y: float
    angle_rad: float


@dataclass(frozen=True)
class EdgeRecord:
    key: EdgeKey
    owner_parcel_id: str
    owner_height_m: float | None
    start: tuple[float, float]
    end: tuple[float, float]
    length_m: float


@prd("004", "PartyWallIndex")
class PartyWallIndex:
    MIDPOINT_TOL_M = 0.8
    NEAR_PARALLEL_GAP_TOL_M = 1.2
    ANGLE_TOL_RAD = math.radians(15.0)
    UNKNOWN_ADJACENT_HEIGHT_M = 999.0

    def __init__(self) -> None:
        self._edges: list[EdgeRecord] = []

    def register(self, owner_parcel_id: str, polygon_utm: Polygon, owner_height_m: float | None = None) -> None:
        coords = list(polygon_utm.exterior.coords)
        if coords and coords[0] == coords[-1]:
            coords = coords[:-1]
        for i in range(len(coords)):
            a = coords[i]
            b = coords[(i + 1) % len(coords)]
            dx = b[0] - a[0]
            dy = b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.4:
                continue
            mid_x = (a[0] + b[0]) / 2
            mid_y = (a[1] + b[1]) / 2
            angle = math.atan2(dy, dx) % math.pi   # undirected
            self._edges.append(EdgeRecord(
                key=EdgeKey(mid_x, mid_y, angle),
                owner_parcel_id=owner_parcel_id,
                owner_height_m=owner_height_m,
                start=(a[0], a[1]),
                end=(b[0], b[1]),
                length_m=length,
            ))

    def is_party(self, owner_parcel_id: str, edge_utm_start, edge_utm_end) -> bool:
        return self.adjacent_height(owner_parcel_id, edge_utm_start, edge_utm_end) is not None

    def adjacent_height(self, owner_parcel_id: str, edge_utm_start, edge_utm_end) -> float | None:
        dx = edge_utm_end[0] - edge_utm_start[0]
        dy = edge_utm_end[1] - edge_utm_start[1]
        length = math.hypot(dx, dy)
        if length < 0.4:
            return None
        mx = (edge_utm_start[0] + edge_utm_end[0]) / 2
        my = (edge_utm_start[1] + edge_utm_end[1]) / 2
        angle = math.atan2(dy, dx) % math.pi
        axis = (dx / length, dy / length)
        current_line = LineString([edge_utm_start, edge_utm_end])
        matched_height: float | None = None
        matched = False
        for other in self._edges:
            if other.owner_parcel_id == owner_parcel_id:
                continue
            dtheta = abs(other.key.angle_rad - angle)
            dtheta = min(dtheta, math.pi - dtheta)
            if dtheta > self.ANGLE_TOL_RAD:
                continue

            # Fast path for nearly identical traced edges.
            dist = math.hypot(other.key.mid_x - mx, other.key.mid_y - my)
            midpoint_match = dist <= self.MIDPOINT_TOL_M

            # Robust path for KML/SHP traces that should be bitişik but have
            # slightly shifted vertices or different split lengths. We treat
            # close, parallel, substantially overlapping edges as party walls.
            overlap = _projected_overlap(edge_utm_start, edge_utm_end, other.start, other.end, axis)
            min_overlap = max(0.45, min(length, other.length_m) * 0.25)
            close_parallel = (
                overlap >= min_overlap
                and current_line.distance(LineString([other.start, other.end])) <= self.NEAR_PARALLEL_GAP_TOL_M
            )

            if midpoint_match or close_parallel:
                matched = True
                other_height = (
                    other.owner_height_m
                    if other.owner_height_m is not None
                    else self.UNKNOWN_ADJACENT_HEIGHT_M
                )
                matched_height = max(matched_height or 0.0, other_height)
        if matched:
            return matched_height if matched_height is not None else self.UNKNOWN_ADJACENT_HEIGHT_M
        return None


def _projected_overlap(a0, a1, b0, b1, axis: tuple[float, float]) -> float:
    def dot(p):
        return p[0] * axis[0] + p[1] * axis[1]

    a_min, a_max = sorted((dot(a0), dot(a1)))
    b_min, b_max = sorted((dot(b0), dot(b1)))
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))
