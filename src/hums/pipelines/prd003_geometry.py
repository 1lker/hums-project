"""PRD-003 pipeline orchestrator — buildings.json → IFC + glTF + reports."""
from __future__ import annotations
import json
from pathlib import Path

from shapely.geometry import shape

from ..common.paths import BLOCK_GEOJSON, PARSED, PROJECT_ROOT
from ..common.prd import prd
from ..modeling.building import (
    Building, FacadePalette, LocalFrame, Opening, Provenance, ReferenceImage,
    RoofDescriptor, Storey, WallSegment,
)
from ..render.backends.gltf_backend import GltfBackend
from ..render.backends.ifc_backend import IfcBackend
from ..render.building_geometry_builder import BuildingGeometryBuilder
from ..render.reports.geometry_manifest import write_reports
from ..render.scene_assembler import SceneAssembler

BUILDINGS_JSON = PARSED / "buildings.json"
OUTPUT = PROJECT_ROOT / "output"
IFC_DIR = OUTPUT / "ifc"
GLTF_DIR = OUTPUT / "gltf"
REPORT_DIR = OUTPUT / "reports"


@prd("003", "Pipeline")
class Prd003Pipeline:
    def run(self) -> dict:
        buildings = [_building_from_dict(d) for d in json.loads(BUILDINGS_JSON.read_text())]
        geom_builder = BuildingGeometryBuilder()
        meshes = []
        for b in buildings:
            m = geom_builder.build(b)
            if m:
                meshes.append(m)

        block_centroid = _block_centroid()
        scene = SceneAssembler().assemble(meshes, block_centroid)

        # Backends
        IFC_DIR.mkdir(parents=True, exist_ok=True)
        GLTF_DIR.mkdir(parents=True, exist_ok=True)

        gltf = GltfBackend()
        gltf.export_scene(scene, GLTF_DIR / "block147.glb")

        ifc = IfcBackend()
        ifc.export_scene(scene, IFC_DIR / "block147.ifc")

        # Per-building glTF (handy for previews)
        for mesh in meshes:
            gltf.export_building(mesh, GLTF_DIR / f"{mesh.parcel_id.replace('/','_')}.glb")

        write_reports(scene, REPORT_DIR)

        return {
            "buildings_input": len(buildings),
            "meshes_generated": len(meshes),
            "faces_total": sum(len(m.faces) for m in meshes),
            "roles": scene.face_count_by_role(),
            "outputs": {
                "gltf_scene": str((GLTF_DIR / "block147.glb").relative_to(PROJECT_ROOT)),
                "ifc_scene": str((IFC_DIR / "block147.ifc").relative_to(PROJECT_ROOT)),
                "reports": str(REPORT_DIR.relative_to(PROJECT_ROOT)),
            },
        }


def _block_centroid() -> tuple[float, float]:
    feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
    if not feats:
        return (0.0, 0.0)
    c = shape(feats[0]["geometry"]).centroid
    return (c.x, c.y)


def _building_from_dict(d: dict) -> Building:
    """Reconstitute a Building from its persisted JSON form.

    We intentionally re-hydrate into real dataclasses rather than operating on
    raw dicts downstream — keeps the geometry layer typed.
    """
    lf = d.get("local_frame")
    local_frame = LocalFrame(
        origin_utm=tuple(lf["origin_utm"]) if lf else None,
        street_rotation_deg=lf["street_rotation_deg"] if lf else 0.0,
    ) if lf else None

    palette_d = d.get("facade_palette") or None
    palette = FacadePalette(**{**palette_d,
                                "wall_main": tuple(palette_d["wall_main"]),
                                "trim": tuple(palette_d["trim"]),
                                "roof": tuple(palette_d["roof"]),
                                "wall_accent": tuple(palette_d["wall_accent"]) if palette_d.get("wall_accent") else None,
                                "shutters": tuple(palette_d["shutters"]) if palette_d.get("shutters") else None,
                                "gf_shopfront": tuple(palette_d["gf_shopfront"]) if palette_d.get("gf_shopfront") else None,
                                }) if palette_d else None

    roof_d = d.get("roof") or None
    roof = RoofDescriptor(**roof_d) if roof_d else None

    storeys = [Storey(**s) for s in d.get("storeys") or []]
    segments = []
    for seg in d.get("wall_segments") or []:
        openings = [Opening(**o) for o in seg.get("openings") or []]
        segments.append(WallSegment(
            start=tuple(seg["start"]), end=tuple(seg["end"]),
            thickness_m=seg["thickness_m"], face=seg["face"],
            is_street_facing=seg["is_street_facing"],
            hatch_pattern=seg.get("hatch_pattern"),
            openings=openings,
        ))
    ref_imgs = [ReferenceImage(**r) for r in d.get("reference_imagery") or []]
    prov = Provenance(**(d.get("provenance") or {}))

    return Building(
        parcel_id=d["parcel_id"],
        material_class=d.get("material_class"),
        footprint_source=d.get("footprint_source") or "missing",
        local_frame=local_frame,
        structure_type=d.get("structure_type") or "building",
        notes=d.get("notes") or {},
        footprint_local=[tuple(p) for p in d.get("footprint_local") or []],
        storeys=storeys,
        wall_segments=segments,
        roof=roof,
        facade_palette=palette,
        reference_imagery=ref_imgs,
        shared_footprint_group_id=d.get("shared_footprint_group_id"),
        provenance=prov,
        excel_snapshot=d.get("excel_snapshot") or {},
    )


def main() -> None:
    r = Prd003Pipeline().run()
    print(f"[PRD-003] meshes={r['meshes_generated']}/{r['buildings_input']}  "
          f"faces={r['faces_total']}  roles={r['roles']}")
    print("  outputs:")
    for k, v in r["outputs"].items():
        print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
