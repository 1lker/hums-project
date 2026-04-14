"""PRD-002 · §7 — persist stubs.geojson for interior INT-* parcels."""
from __future__ import annotations
import json

from shapely.geometry import Polygon, mapping, shape

from ..common.paths import (
    BLOCK_GEOJSON, FOOTPRINTS_GEOJSON, NON_PARCEL_FOOTPRINTS_GEOJSON, PARSED,
)
from ..common.prd import prd
from ..geo.crs import UTM_35N
from .interior_sectoriser import InteriorSectoriser, DEFAULT_SECTORS

STUBS_GEOJSON = PARSED / "stubs.geojson"


@prd("002", "§7 StubGenerator")
class StubGenerator:
    def generate_and_persist(self) -> dict[str, Polygon]:
        block = _first_polygon(BLOCK_GEOJSON)
        traced = [shape(f["geometry"]) for f in _features(FOOTPRINTS_GEOJSON)]
        church = _largest_church(NON_PARCEL_FOOTPRINTS_GEOJSON)
        if block is None or church is None:
            STUBS_GEOJSON.write_text(json.dumps({"type": "FeatureCollection",
                                                  "crs": {"type": "name", "properties": {"name": UTM_35N}},
                                                  "features": []}, indent=2))
            return {}

        sectoriser = InteriorSectoriser(block, traced, church)
        stubs = sectoriser.generate(DEFAULT_SECTORS)

        features = []
        for pid, poly in stubs.items():
            features.append({
                "type": "Feature",
                "geometry": mapping(poly),
                "properties": {
                    "parcel_id": pid,
                    "kind": "stub",
                    "match_confidence": "inferred-sector",
                    "area_m2": round(poly.area, 3),
                },
            })
        STUBS_GEOJSON.write_text(json.dumps({
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": UTM_35N}},
            "features": features,
        }, indent=2))
        return stubs


def _features(path):
    if not path.exists():
        return []
    return json.loads(path.read_text())["features"]


def _first_polygon(path):
    feats = _features(path)
    return shape(feats[0]["geometry"]) if feats else None


def _largest_church(path):
    feats = [f for f in _features(path) if f["properties"].get("kind") == "church"]
    if not feats:
        return None
    feats.sort(key=lambda f: f["properties"].get("area_m2", 0), reverse=True)
    return shape(feats[0]["geometry"])
