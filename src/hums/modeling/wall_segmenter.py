"""PRD-002 · §5 — polygon edges → WallSegment list.

Classifies each segment as street-facing (edge on block boundary) or interior,
and assigns cardinal face (N/E/S/W/INT) from edge normal in UTM space.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon

from ..common.prd import prd
from .building import WallSegment, Face
from .party_wall_index import PartyWallIndex


@dataclass
class WallSegmenterConfig:
    boundary_tol_m: float = 2.0  # loose — block outline and parcel traces need not be precisely coincident


@prd("002", "§5 WallSegmenter")
class WallSegmenter:
    def __init__(self, block_outline: Polygon | None,
                 party_index: PartyWallIndex | None = None,
                 cfg: WallSegmenterConfig | None = None) -> None:
        self._block = block_outline
        self._party_index = party_index
        self._cfg = cfg or WallSegmenterConfig()

    def segment(
        self,
        footprint_local: list[tuple[float, float]],
        footprint_utm: Polygon,
        thickness_m: float,
        parcel_id: str | None = None,
        building_height_m: float | None = None,
    ) -> list[WallSegment]:
        # Pair local and utm coords by index (both have same orientation).
        utm_coords = list(footprint_utm.exterior.coords)
        if utm_coords[0] == utm_coords[-1]:
            utm_coords = utm_coords[:-1]
        if _signed_area(utm_coords) < 0:
            utm_coords.reverse()

        # footprint_local is CCW; keep UTM in the same winding so edge-indexed
        # street/party-wall classification attaches to the same local segment.
        if len(utm_coords) != len(footprint_local):
            # fallback: derive faces purely from local; skip street detection
            return self._segment_from_local_only(footprint_local, thickness_m)

        segments: list[WallSegment] = []
        n = len(footprint_local)
        for i in range(n):
            a_local = footprint_local[i]
            b_local = footprint_local[(i + 1) % n]
            a_utm = utm_coords[i]
            b_utm = utm_coords[(i + 1) % n]
            on_block = self._on_block_boundary(a_utm, b_utm)
            adjacent_height = (
                self._party_index.adjacent_height(parcel_id, a_utm, b_utm)
                if self._party_index is not None and parcel_id is not None and not on_block
                else None
            )
            is_party = adjacent_height is not None
            # New, simpler classification for block-scale reconstruction:
            #   * edge shared with a neighbour → party wall (no openings)
            #   * everything else → exterior, can have openings
            # We retain `is_street_facing` as "on the block perimeter" for
            # the shop-window placer (shops front the street, not the
            # courtyard), but windows/doors now get placed on ANY exterior
            # (non-party) face rather than only the perimeter ones.
            is_exterior = not is_party
            is_street = on_block and is_exterior
            face = self._classify_face(a_utm, b_utm, is_exterior)
            segments.append(WallSegment(
                start=a_local, end=b_local,
                thickness_m=thickness_m,
                face=face,
                is_street_facing=is_exterior,     # read as "opening-eligible"
                is_party_wall=is_party,
                adjacent_height_m=adjacent_height,
            ))
            # Store the strict on-block flag in a metadata channel for shops.
            segments[-1].hatch_pattern = "_street" if is_street else None
        return segments

    def _segment_from_local_only(self, ring, thickness_m):
        segs = []
        n = len(ring)
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            segs.append(WallSegment(a, b, thickness_m, "INT", False))
        return segs

    def _on_block_boundary(self, a_utm, b_utm) -> bool:
        if self._block is None:
            return False
        line = LineString([a_utm, b_utm])
        length = line.length
        if length < 0.4:
            return False
        dx = b_utm[0] - a_utm[0]
        dy = b_utm[1] - a_utm[1]
        angle = math.atan2(dy, dx) % math.pi
        axis = (dx / length, dy / length)
        block_coords = list(self._block.exterior.coords)
        for i in range(len(block_coords) - 1):
            c = block_coords[i]
            d = block_coords[i + 1]
            bdx = d[0] - c[0]
            bdy = d[1] - c[1]
            block_len = math.hypot(bdx, bdy)
            if block_len < 0.4:
                continue
            block_angle = math.atan2(bdy, bdx) % math.pi
            dtheta = abs(block_angle - angle)
            dtheta = min(dtheta, math.pi - dtheta)
            if dtheta > math.radians(15.0):
                continue
            overlap = _projected_overlap(a_utm, b_utm, c, d, axis)
            min_overlap = max(0.45, min(length, block_len) * 0.25)
            if overlap >= min_overlap and line.distance(LineString([c, d])) <= self._cfg.boundary_tol_m:
                return True
        return False

    def _classify_face(self, a_utm, b_utm, is_street: bool) -> Face:
        if not is_street:
            return "INT"
        # outward normal = perpendicular-right of edge direction (polygon is CCW in UTM too normally)
        dx = b_utm[0] - a_utm[0]
        dy = b_utm[1] - a_utm[1]
        # right-hand normal (points outward for CCW)
        nx = dy
        ny = -dx
        ang = math.degrees(math.atan2(ny, nx))
        # map to compass: 0°=E, 90°=N, ±180°=W, -90°=S
        if -45 <= ang < 45:
            return "E"
        if 45 <= ang < 135:
            return "N"
        if ang >= 135 or ang < -135:
            return "W"
        return "S"


def _signed_area(ring: list[tuple[float, float]]) -> float:
    s = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def _projected_overlap(a0, a1, b0, b1, axis: tuple[float, float]) -> float:
    def dot(p):
        return p[0] * axis[0] + p[1] * axis[1]

    a_min, a_max = sorted((dot(a0), dot(a1)))
    b_min, b_max = sorted((dot(b0), dot(b1)))
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))
