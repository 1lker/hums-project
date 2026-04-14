"""PRD-004 · Interior annex placer for INT-* parcels.

INT-* parcels in Excel are rear wings attached to street-fronting buildings,
not standalone courtyard buildings. This placer reads the Pervititch-map
intuition + Excel metadata into a table of (parent, width, depth) hints and
snaps a rectangular annex footprint onto the rear (courtyard-facing) edge of
the parent parcel.

Output: ``data/parsed/stubs.geojson`` (same file path as before) but with
``kind = "annex"`` and each feature carrying ``parent_parcel_id``. The
PRD-002 pipeline picks them up as footprint_source = "stub" and the
geometry builder renders them with the parent's material + palette.

Hand-derived attachment table — based on reading the 1923 Pervititch
screenshot + Excel ``zone`` / ``bim_notes`` for each INT-*:

  INT-N1  parent N-42  ≈ 7.0 × 4.5 m  — wedge S of N-42 facing church
  INT-N2  parent N-44  ≈ 5.0 × 3.5 m  — small annex behind N-44 bakery rear
  INT-N3  parent N-52  ≈ 6.0 × 4.0 m  — between N-frontage and NE corner
  INT-E2  parent E-4   ≈ 4.5 × 3.0 m  — church-E-wall wooden shop
  INT-S1  parent S-41  ≈ 5.5 × 6.0 m  — immediately S of clocher
  INT-S2  parent S-43  ≈ 5.0 × 6.0 m  — SE of clocher

Depth = how far the annex projects from the parent's rear edge into the
courtyard. Sizes are approximate (Excel storeys + BIM notes don't give
floor area); treat them as 'plausible placeholder'.
"""
from __future__ import annotations
import json
import math
from dataclasses import dataclass

from shapely.geometry import Polygon, shape
from shapely.geometry.polygon import orient

from ..common.paths import FOOTPRINTS_GEOJSON, BLOCK_GEOJSON, PARSED
from ..common.prd import prd
from ..geo.crs import UTM_35N
from .stub_generator import STUBS_GEOJSON


@dataclass
class AnnexSpec:
    parcel_id: str
    parent_parcel_id: str
    width_m: float
    depth_m: float


DEFAULT_ANNEXES: list[AnnexSpec] = [
    AnnexSpec("INT-N1", "N-42", 7.0, 4.5),
    AnnexSpec("INT-N2", "N-44", 5.0, 3.5),
    AnnexSpec("INT-N3", "N-52", 6.0, 4.0),
    AnnexSpec("INT-E2", "E-4",  4.5, 3.0),
    AnnexSpec("INT-S1", "S-41", 5.5, 6.0),
    AnnexSpec("INT-S2", "S-43", 5.0, 6.0),
]


@prd("004", "AnnexPlacer")
class AnnexPlacer:
    def generate_and_persist(self, specs: list[AnnexSpec] = DEFAULT_ANNEXES) -> dict[str, Polygon]:
        parents = _load_parents()
        block = _load_block()
        if block is None:
            return {}
        block_centroid = block.centroid
        results: dict[str, Polygon] = {}

        features: list[dict] = []
        for spec in specs:
            parent = parents.get(spec.parent_parcel_id)
            if parent is None:
                continue
            poly = self._attach(parent, block_centroid, spec)
            if poly is None:
                continue
            # Keep clipped-to-block so annexes never stick outside the block.
            clipped = poly.intersection(block)
            if clipped.is_empty:
                clipped = poly
            if hasattr(clipped, "geoms"):
                clipped = max(clipped.geoms, key=lambda g: g.area)
            # Avoid overlap with any other traced footprint.
            for other_feat in _load_traced_features():
                other = shape(other_feat["geometry"])
                clipped = clipped.difference(other)
                if clipped.is_empty:
                    break
            if clipped.is_empty or clipped.geom_type != "Polygon" or clipped.area < 1.0:
                continue
            results[spec.parcel_id] = clipped
            features.append(_feature(spec, clipped))

        STUBS_GEOJSON.write_text(json.dumps({
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": UTM_35N}},
            "features": features,
        }, indent=2))
        return results

    def _attach(self, parent: Polygon, block_centroid, spec: AnnexSpec) -> Polygon | None:
        """Attach a rectangle to the parent's edge that faces the block centroid."""
        parent = orient(parent, sign=1.0)
        coords = list(parent.exterior.coords)[:-1]
        if len(coords) < 3:
            return None
        # Pick the edge whose midpoint is closest to the block centroid (facing
        # the courtyard/church side).
        best = None
        best_d = float("inf")
        for i in range(len(coords)):
            a = coords[i]
            b = coords[(i + 1) % len(coords)]
            mx = (a[0] + b[0]) / 2
            my = (a[1] + b[1]) / 2
            d = math.hypot(mx - block_centroid.x, my - block_centroid.y)
            if d < best_d:
                best_d = d
                best = (a, b)
        if best is None:
            return None

        (ax, ay), (bx, by) = best
        length = math.hypot(bx - ax, by - ay)
        if length < 0.3:
            return None
        ux = (bx - ax) / length
        uy = (by - ay) / length
        # outward normal (edge runs CCW around the ring → right-hand normal is
        # interior for CCW polygons, so FLIP to get outward-to-courtyard).
        nx = uy
        ny = -ux
        # ensure normal points TOWARD the block centroid (i.e. into courtyard)
        mx = (ax + bx) / 2
        my = (ay + by) / 2
        if (block_centroid.x - mx) * nx + (block_centroid.y - my) * ny < 0:
            nx, ny = -nx, -ny

        # Centre the annex along this edge's midpoint.
        mid_x = (ax + bx) / 2
        mid_y = (ay + by) / 2
        half_w = spec.width_m / 2
        # along-edge endpoints
        p0 = (mid_x - ux * half_w, mid_y - uy * half_w)
        p1 = (mid_x + ux * half_w, mid_y + uy * half_w)
        # outward projection
        p2 = (p1[0] + nx * spec.depth_m, p1[1] + ny * spec.depth_m)
        p3 = (p0[0] + nx * spec.depth_m, p0[1] + ny * spec.depth_m)
        return Polygon([p0, p1, p2, p3])


def _feature(spec: AnnexSpec, poly: Polygon) -> dict:
    from shapely.geometry import mapping
    c = poly.centroid
    return {
        "type": "Feature",
        "geometry": mapping(poly),
        "properties": {
            "parcel_id": spec.parcel_id,
            "parent_parcel_id": spec.parent_parcel_id,
            "kind": "annex",
            "match_confidence": "map-inferred-annex",
            "area_m2": round(poly.area, 3),
            "centroid_utm": [round(c.x, 3), round(c.y, 3)],
        },
    }


def _load_parents() -> dict[str, Polygon]:
    if not FOOTPRINTS_GEOJSON.exists():
        return {}
    fc = json.loads(FOOTPRINTS_GEOJSON.read_text())
    out: dict[str, Polygon] = {}
    for f in fc["features"]:
        for pid in (f["properties"].get("parcel_ids_matched") or []):
            out.setdefault(pid, shape(f["geometry"]))
    return out


def _load_traced_features() -> list[dict]:
    if not FOOTPRINTS_GEOJSON.exists():
        return []
    return json.loads(FOOTPRINTS_GEOJSON.read_text())["features"]


def _load_block() -> Polygon | None:
    if not BLOCK_GEOJSON.exists():
        return None
    feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
    return shape(feats[0]["geometry"]) if feats else None
