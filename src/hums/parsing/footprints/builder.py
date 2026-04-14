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
            rings, source_path = self._read_with_fallback(src)
            if not rings:
                continue

            cls = self._classifier.classify(src.display_name)

            for ring in rings:
                poly = self._to_metric_polygon(ring)
                if poly.is_empty or poly.area < self.MIN_AREA_M2:
                    continue
                feat = self._feature(poly, src, cls, source_path)
                bucket = self._bucket_for(cls.kind)
                {"parcel": parcel, "non_parcel": non_parcel, "block": block}[bucket].append(feat)

        return {"parcel": parcel, "non_parcel": non_parcel, "block": block}

    def _read_with_fallback(self, src):
        """Prefer shapefile; fall back to KML if shapefile has no geometry
        (some of our shapefiles are empty 100-byte headers — authored in QGIS
        before the polygon was drawn, then the geometry was saved only to KML).
        """
        if src.shp:
            try:
                rings = self._shp_reader.read(src.shp)
            except Exception as e:  # pragma: no cover
                print(f"  ! shp read failed {src.shp.name}: {e}")
                rings = []
            if rings:
                return rings, src.shp
        if src.kml:
            try:
                rings = self._kml_reader.read(src.kml)
                return rings, src.kml
            except Exception as e:  # pragma: no cover
                print(f"  ! kml read failed {src.kml.name}: {e}")
        return [], src.primary

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

    def _feature(self, poly: Polygon, src: FootprintSource, cls, source_path: "Path | None" = None) -> dict:
        c = poly.centroid
        chosen = source_path or src.primary
        base_props = {
            "source_file": chosen.name,
            "source_format": chosen.suffix.lstrip(".").lower(),
            "area_m2": round(poly.area, 3),
            "perimeter_m": round(poly.length, 3),
            "centroid_utm": [round(c.x, 3), round(c.y, 3)],
            "kind": cls.kind.value,
        }
        if cls.kind == FootprintKind.PARCEL:
            if cls.parcel_ids_override:
                base_props.update({
                    "parcel_numbers": None,
                    "parcel_ids_override": cls.parcel_ids_override,
                    "match_confidence": "override",
                })
            else:
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
