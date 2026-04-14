"""PRD-004 · Party-wall detector.

Two adjacent parcel polygons typically share a segment of their outline
(the common wall between neighbour buildings). No windows or doors can
exist on such a shared edge. This index pre-computes a set of
``(midpoint, direction)`` fingerprints from every traced polygon's edges
and exposes a cheap lookup: *is this edge shared with any other parcel?*

Adjacency tolerance: 0.8 m midpoint distance + within 15° of the same
edge direction (handles imperfect traces that don't quite share vertices).
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from shapely.geometry import Polygon

from ..common.prd import prd


@dataclass(frozen=True)
class EdgeKey:
    mid_x: float
    mid_y: float
    angle_rad: float


@prd("004", "PartyWallIndex")
class PartyWallIndex:
    MIDPOINT_TOL_M = 0.8
    ANGLE_TOL_RAD = math.radians(15.0)

    def __init__(self) -> None:
        self._edges: list[tuple[EdgeKey, str]] = []   # (key, owner_parcel_id)

    def register(self, owner_parcel_id: str, polygon_utm: Polygon) -> None:
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
            self._edges.append((EdgeKey(mid_x, mid_y, angle), owner_parcel_id))

    def is_party(self, owner_parcel_id: str, edge_utm_start, edge_utm_end) -> bool:
        dx = edge_utm_end[0] - edge_utm_start[0]
        dy = edge_utm_end[1] - edge_utm_start[1]
        length = math.hypot(dx, dy)
        if length < 0.4:
            return False
        mx = (edge_utm_start[0] + edge_utm_end[0]) / 2
        my = (edge_utm_start[1] + edge_utm_end[1]) / 2
        angle = math.atan2(dy, dx) % math.pi
        for other_key, other_owner in self._edges:
            if other_owner == owner_parcel_id:
                continue
            if abs(other_key.mid_x - mx) > self.MIDPOINT_TOL_M:
                continue
            if abs(other_key.mid_y - my) > self.MIDPOINT_TOL_M:
                continue
            dist = math.hypot(other_key.mid_x - mx, other_key.mid_y - my)
            if dist > self.MIDPOINT_TOL_M:
                continue
            dtheta = abs(other_key.angle_rad - angle)
            dtheta = min(dtheta, math.pi - dtheta)
            if dtheta <= self.ANGLE_TOL_RAD:
                return True
        return False
