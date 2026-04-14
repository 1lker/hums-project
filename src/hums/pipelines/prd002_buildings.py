"""PRD-002 orchestrator: parcels + footprints + stubs + imagery → buildings.json."""
from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path

from shapely.geometry import shape

from ..common.paths import (
    BLOCK_GEOJSON, FOOTPRINTS_GEOJSON, PARCELS_JSON, PARSED, ensure_parsed_dir,
)
from ..common.prd import prd
from ..imagery.reference_manifest import ReferenceManifest
from ..modeling.assumption_tracker import AssumptionTracker
from ..modeling.building_builder import BuildingBuilder
from ..stubs.stub_generator import StubGenerator, STUBS_GEOJSON

BUILDINGS_JSON = PARSED / "buildings.json"
ASSUMPTIONS_MANIFEST = PARSED / "assumptions_manifest.md"


@prd("002", "Pipeline")
class Prd002Pipeline:
    def run(self) -> dict:
        ensure_parsed_dir()
        parcels = json.loads(PARCELS_JSON.read_text())
        block = _first_polygon(BLOCK_GEOJSON)

        # Index footprints by matched parcel_id.
        traced_by_pid: dict[str, dict] = {}
        for feat in json.loads(FOOTPRINTS_GEOJSON.read_text())["features"]:
            for pid in feat["properties"].get("parcel_ids_matched") or []:
                traced_by_pid.setdefault(pid, feat)  # first match wins

        # Generate stubs for INT-* parcels.
        stubs = StubGenerator().generate_and_persist()

        tracker = AssumptionTracker()
        builder = BuildingBuilder(block)
        buildings = []

        for parcel in parcels:
            pid = parcel["parcel_id"]
            feat = traced_by_pid.get(pid)
            footprint_source = None
            source_file = None
            polygon = None

            if feat:
                polygon = shape(feat["geometry"])
                # Handle shared footprints: split along long axis by parcel count.
                matched_ids = feat["properties"].get("parcel_ids_matched") or []
                if len(matched_ids) > 1:
                    polygon = _split_share(polygon, matched_ids, pid)
                footprint_source = "traced"
                source_file = feat["properties"].get("source_file")
            elif pid in stubs:
                polygon = stubs[pid]
                footprint_source = "stub"
                source_file = "stubs.geojson"
            else:
                footprint_source = "missing"

            building = builder.build(parcel, polygon, footprint_source, source_file, tracker)
            building.reference_imagery = ReferenceManifest.load_for(pid)
            if feat and len(feat["properties"].get("parcel_ids_matched") or []) > 1:
                building.shared_footprint_group_id = "|".join(feat["properties"]["parcel_ids_matched"])
            buildings.append(building)

        _persist_buildings(buildings)
        _persist_manifest(tracker)

        return {
            "buildings": len(buildings),
            "traced": sum(1 for b in buildings if b.footprint_source == "traced"),
            "stubbed": sum(1 for b in buildings if b.footprint_source == "stub"),
            "missing": sum(1 for b in buildings if b.footprint_source == "missing"),
            "assumptions": len(tracker.entries),
        }


def _split_share(polygon, matched_ids, pid: str):
    """Split a shared footprint into equal strips along its long axis; pick the strip for `pid`."""
    from shapely.affinity import rotate
    from shapely.geometry import box
    minx, miny, maxx, maxy = polygon.bounds
    # rotate to axis-align longest dimension if wider than tall? keep simple: split along X.
    width = maxx - minx
    height = maxy - miny
    count = len(matched_ids)
    idx = matched_ids.index(pid)
    if width >= height:
        strip_w = width / count
        strip = box(minx + idx * strip_w, miny, minx + (idx + 1) * strip_w, maxy)
    else:
        strip_h = height / count
        strip = box(minx, miny + idx * strip_h, maxx, miny + (idx + 1) * strip_h)
    clipped = polygon.intersection(strip)
    if clipped.is_empty:
        return polygon
    if hasattr(clipped, "geoms"):
        clipped = max(clipped.geoms, key=lambda g: g.area)
    return clipped


def _persist_buildings(buildings):
    payload = [b.to_dict() for b in buildings]
    BUILDINGS_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _persist_manifest(tracker):
    per_parcel = tracker.per_parcel()
    lines = ["# PRD-002 Assumptions Manifest\n",
             f"Total assumption entries: **{len(tracker.entries)}**",
             f"Parcels with assumptions: **{len(per_parcel)}**\n"]
    for pid in sorted(per_parcel):
        lines.append(f"## {pid}\n")
        lines.append("| field | source | value |")
        lines.append("|---|---|---|")
        for e in per_parcel[pid]:
            val = str(e.value)
            if len(val) > 60:
                val = val[:57] + "..."
            lines.append(f"| {e.field_path} | {e.source} | {val} |")
        lines.append("")
    ASSUMPTIONS_MANIFEST.write_text("\n".join(lines))


def _first_polygon(path: Path):
    if not path.exists():
        return None
    feats = json.loads(path.read_text()).get("features", [])
    return shape(feats[0]["geometry"]) if feats else None


def main():
    r = Prd002Pipeline().run()
    print(f"[PRD-002] buildings={r['buildings']}  traced={r['traced']}  "
          f"stubbed={r['stubbed']}  missing={r['missing']}  "
          f"assumptions={r['assumptions']}")


if __name__ == "__main__":
    main()
