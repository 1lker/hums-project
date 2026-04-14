"""PRD-001 · Data Foundation §6 step 2 — assembles footprints.geojson.

Orchestrates: SourceRegistry → FootprintReader → CrsTransformer → Classifier
→ GeoJSON FeatureCollections partitioned by kind.
"""
from __future__ import annotations
import json
from pathlib import Path

from shapely.geometry import Polygon, mapping

from ...common.paths import (
    FOOTPRINTS_GEOJSON,
    NON_PARCEL_FOOTPRINTS_GEOJSON,
    BLOCK_GEOJSON,
    ensure_parsed_dir,
)
from ...common.prd import prd
from ...geo.crs import CrsTransformer, UTM_35N
from .classifier import FilenameClassifier, FootprintKind
from .reader import KmlReader, ShapefileReader, FootprintReader
from .source_registry import SourceRegistry, FootprintSource


@prd("001", "§4 footprints.geojson")
class FootprintBuilder:
    MIN_AREA_M2 = 0.1

    def __init__(self, root: Path) -> None:
        self._registry = SourceRegistry(root)
        self._classifier = FilenameClassifier()
        self._crs = CrsTransformer()
        self._shp_reader: FootprintReader = ShapefileReader()
        self._kml_reader: FootprintReader = KmlReader()

    def build(self) -> dict[str, list[dict]]:
        parcel, non_parcel, block = [], [], []

        for src in self._registry.discover():
            reader = self._shp_reader if src.shp else self._kml_reader
            try:
                rings = reader.read(src.primary)
            except Exception as e:  # pragma: no cover
                print(f"  ! failed to read {src.primary.name}: {e}")
                continue

            cls = self._classifier.classify(src.display_name)

            for ring in rings:
                poly = self._to_metric_polygon(ring)
                if poly.is_empty or poly.area < self.MIN_AREA_M2:
                    continue
                feat = self._feature(poly, src, cls)
                bucket = self._bucket_for(cls.kind)
                {"parcel": parcel, "non_parcel": non_parcel, "block": block}[bucket].append(feat)

        return {"parcel": parcel, "non_parcel": non_parcel, "block": block}

    def build_and_persist(self) -> dict[str, int]:
        groups = self.build()
        ensure_parsed_dir()
        FOOTPRINTS_GEOJSON.write_text(json.dumps(_fc(groups["parcel"]), indent=2))
        NON_PARCEL_FOOTPRINTS_GEOJSON.write_text(json.dumps(_fc(groups["non_parcel"]), indent=2))
        if groups["block"]:
            BLOCK_GEOJSON.write_text(json.dumps(_fc(groups["block"]), indent=2))
        return {k: len(v) for k, v in groups.items()}

    # ---- helpers ----
    def _to_metric_polygon(self, ring_lonlat) -> Polygon:
        utm_pts = self._crs.points(ring_lonlat)
        poly = Polygon(utm_pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        return poly

    def _feature(self, poly: Polygon, src: FootprintSource, cls) -> dict:
        c = poly.centroid
        base_props = {
            "source_file": src.primary.name,
            "source_format": src.primary_format,
            "area_m2": round(poly.area, 3),
            "perimeter_m": round(poly.length, 3),
            "centroid_utm": [round(c.x, 3), round(c.y, 3)],
            "kind": cls.kind.value,
        }
        if cls.kind == FootprintKind.PARCEL:
            base_props.update({
                "parcel_numbers": cls.parcel_numbers,
                "match_confidence": "high" if cls.parcel_numbers and len(cls.parcel_numbers) == 1 else "shared-footprint",
            })
        elif cls.kind == FootprintKind.BLOCK_OUTLINE:
            base_props["name"] = "Block 147 outline"
        else:
            base_props["name"] = src.display_name
        return {"type": "Feature", "geometry": mapping(poly), "properties": base_props}

    @staticmethod
    def _bucket_for(kind: FootprintKind) -> str:
        if kind == FootprintKind.PARCEL:
            return "parcel"
        if kind == FootprintKind.BLOCK_OUTLINE:
            return "block"
        return "non_parcel"


def _fc(features: list[dict]) -> dict:
    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": UTM_35N}},
        "features": features,
    }
