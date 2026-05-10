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
            is_party = (self._party_index is not None and parcel_id is not None
                        and self._party_index.is_party(parcel_id, a_utm, b_utm))
            # New, simpler classification for block-scale reconstruction:
            #   * edge shared with a neighbour → party wall (no openings)
            #   * everything else → exterior, can have openings
            # We retain `is_street_facing` as "on the block perimeter" for
            # the shop-window placer (shops front the street, not the
            # courtyard), but windows/doors now get placed on ANY exterior
            # (non-party) face rather than only the perimeter ones.
            on_block = self._on_block_boundary(a_utm, b_utm)
            is_exterior = not is_party
            is_street = on_block and is_exterior
            face = self._classify_face(a_utm, b_utm, is_exterior)
            segments.append(WallSegment(
                start=a_local, end=b_local,
                thickness_m=thickness_m,
                face=face,
                is_street_facing=is_exterior,     # read as "opening-eligible"
                is_party_wall=is_party,
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


def _signed_area(ring: list[tuple[float, float]]) -> float:
    s = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return s / 2.0
