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
    ) -> list[WallSegment]:
        # Pair local and utm coords by index (both have same orientation).
        utm_coords = list(footprint_utm.exterior.coords)
        if utm_coords[0] == utm_coords[-1]:
            utm_coords = utm_coords[:-1]

        # footprint_local already CCW; utm may differ. Align by index modulo.
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
            is_party = (self._party_index is not None and parcel_id is not None
                        and self._party_index.is_party(parcel_id, a_utm, b_utm))
            # A party wall (shared with a neighbour) is never street-facing —
            # even if it happens to lie close to the block outline.
            on_block = self._on_block_boundary(a_utm, b_utm)
            is_street = on_block and not is_party
            face = self._classify_face(a_utm, b_utm, is_street)
            segments.append(WallSegment(
                start=a_local, end=b_local,
                thickness_m=thickness_m,
                face=face,
                is_street_facing=is_street,
                is_party_wall=is_party,
            ))

        # Fallback: if we found zero street-facing AND zero party walls,
        # promote the longest edge. If there ARE party walls but no street
        # walls we leave it alone — interior annex buildings genuinely have
        # no street facade.
        has_party = any(s.is_party_wall for s in segments)
        if not any(s.is_street_facing for s in segments) and not has_party and segments:
            longest = max(segments, key=lambda s: s.length_m)
            longest.is_street_facing = True
            i_longest = segments.index(longest)
            longest.face = self._classify_face(utm_coords[i_longest],
                                               utm_coords[(i_longest + 1) % n],
                                               True)
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
        return LineString([a_utm, b_utm]).distance(self._block.exterior) <= self._cfg.boundary_tol_m

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
