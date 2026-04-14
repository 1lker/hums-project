"""PRD-005 · Per-building render + analysis.

Workflow: ``python -m hums render-building N-40`` emits

    output/buildings/N-40/
        N-40.glb            — focused glTF of just this building + small ground pad
        N-40_profile.md     — markdown report joining Excel data, map hints,
                              geometry stats, party-wall / neighbour info,
                              and a TODO checklist for remaining issues.

This lets us verify one parcel at a time against the Pervititch screenshot
rather than chasing bugs across all 30 in bulk.
"""
from __future__ import annotations
import json
from pathlib import Path

from shapely.geometry import shape

from ..common.paths import BLOCK_GEOJSON, FOOTPRINTS_GEOJSON, PARCELS_JSON, PROJECT_ROOT
from ..common.prd import prd
from ..render.backends.gltf_backend import GltfBackend
from ..render.building_geometry_builder import BuildingGeometryBuilder
from ..render.mesh_graph import SceneGraph
from ..render.scene_assembler import SceneAssembler
from ..render.reports.diagnostic_map import PALETTE  # unused but shows we reuse styling
from .prd003_geometry import _building_from_dict  # reconstitute dataclasses

OUT_ROOT = PROJECT_ROOT / "output" / "buildings"


@prd("005", "render-building")
def render_building(parcel_id: str) -> Path:
    target_path = OUT_ROOT / parcel_id.replace("/", "_")
    target_path.mkdir(parents=True, exist_ok=True)

    buildings = json.loads((PROJECT_ROOT / "data/parsed/buildings.json").read_text())
    parcels = {p["parcel_id"]: p for p in json.loads(PARCELS_JSON.read_text())}
    target = _find(buildings, parcel_id)
    if target is None:
        raise SystemExit(f"parcel {parcel_id!r} not found in buildings.json")

    building = _building_from_dict(target)
    mesh = BuildingGeometryBuilder().build(building)
    if mesh is None:
        raise SystemExit(f"no geometry for {parcel_id} "
                         f"(footprint_source={building.footprint_source})")

    block_centroid = _block_centroid()
    scene = SceneAssembler().assemble([mesh], block_centroid)
    scene.metadata["block_ring_local"] = _block_ring_local(block_centroid)

    glb_path = target_path / f"{parcel_id.replace('/','_')}.glb"
    GltfBackend().export_scene(scene, glb_path)

    profile = _write_profile(parcel_id, target, parcels.get(parcel_id.split("#")[0], {}),
                              mesh, target_path)
    print(f"Rendered {parcel_id}")
    print(f"  3D: {glb_path.relative_to(PROJECT_ROOT)}")
    print(f"  report: {profile.relative_to(PROJECT_ROOT)}")
    return target_path


def _find(buildings: list[dict], parcel_id: str) -> dict | None:
    for b in buildings:
        if b["parcel_id"] == parcel_id:
            return b
    return None


def _block_centroid() -> tuple[float, float]:
    if not BLOCK_GEOJSON.exists():
        return (0.0, 0.0)
    feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
    if not feats:
        return (0.0, 0.0)
    c = shape(feats[0]["geometry"]).centroid
    return (c.x, c.y)


def _block_ring_local(block_centroid) -> list[tuple[float, float]]:
    if not BLOCK_GEOJSON.exists():
        return []
    feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
    if not feats:
        return []
    poly = shape(feats[0]["geometry"])
    cx, cy = block_centroid
    return [(x - cx, y - cy) for (x, y) in list(poly.exterior.coords)[:-1]]


def _write_profile(parcel_id: str, building_dict: dict, excel_row: dict,
                   mesh, out_dir: Path) -> Path:
    from collections import Counter
    lines: list[str] = []
    lines.append(f"# {parcel_id} — Building Profile\n")

    # Excel summary
    snap = building_dict.get("excel_snapshot") or {}
    mat = (snap.get("material") or {}) if isinstance(snap.get("material"), dict) else {}
    lines.append("## Excel register (from authoritative spreadsheet)\n")
    lines.append(f"- parcel_number: **{snap.get('parcel_number') or '—'}**")
    lines.append(f"- zone: {snap.get('zone') or '—'}")
    lines.append(f"- street_facing: {snap.get('street_facing') or '—'}")
    lines.append(f"- material class: **{mat.get('class') or '—'}** "
                 f"({mat.get('decoded') or '—'}; map colour {mat.get('map_colour') or '—'})")
    lines.append(f"- wall_code: `{snap.get('wall_code') or '—'}`")
    lines.append(f"- vault_code: `{snap.get('vault_code') or '—'}`")
    lines.append(f"- storeys_raw: **{snap.get('storeys_raw') or '—'}**")
    lines.append(f"- bim_notes: {snap.get('bim_notes') or '—'}\n")

    # Roof / doors
    r = building_dict.get("roof") or {}
    op = building_dict.get("openings") if isinstance(building_dict.get("openings"), dict) else {}
    lines.append("## Roof + openings (Excel-derived)\n")
    lines.append(f"- roof shape: **{r.get('shape')}** · material **{r.get('material')}** · "
                 f"pitch {r.get('pitch_deg')}°")
    lines.append(f"- chimney: {r.get('has_chimney')}, skylight: {r.get('has_skylight')}")
    lines.append(f"- primary door face (Excel hint): **{excel_row.get('openings',{}).get('primary_door_face') if isinstance(excel_row.get('openings'), dict) else '—'}**\n")

    # Geometry stats
    lines.append("## Current geometry (what the 3D exporter actually built)\n")
    lines.append(f"- vertices: {len(mesh.vertices)}")
    lines.append(f"- faces: {len(mesh.faces)}")
    lines.append(f"- footprint_source: **{building_dict.get('footprint_source')}**")
    lines.append(f"- local frame rotation: {(building_dict.get('local_frame') or {}).get('street_rotation_deg', 0)}°")
    face_counter = Counter(f.semantic_role for f in mesh.faces)
    for role, n in sorted(face_counter.items(), key=lambda x: -x[1]):
        lines.append(f"  - {role}: {n}")
    lines.append("")

    # Wall segment table
    lines.append("## Wall segments\n")
    lines.append("| # | face | length (m) | street | party | openings |")
    lines.append("|---|---|---|---|---|---|")
    for i, seg in enumerate(building_dict.get("wall_segments") or []):
        import math
        length = math.hypot(seg["end"][0] - seg["start"][0],
                            seg["end"][1] - seg["start"][1])
        lines.append(f"| {i} | {seg['face']} | {length:.2f} "
                     f"| {'✓' if seg['is_street_facing'] else '·'} "
                     f"| {'⚠' if seg.get('is_party_wall') else '·'} "
                     f"| {len(seg.get('openings') or [])} |")

    # Review checklist
    lines.append("\n## Verification checklist (compare with Pervititch screenshot)\n")
    lines.append("- [ ] Footprint shape matches map outline")
    lines.append("- [ ] Street-facing side is correct (not on a party wall)")
    lines.append("- [ ] Door is on the face Excel says")
    lines.append("- [ ] Storey count visibly matches Excel")
    lines.append("- [ ] Roof shape matches map indication (gable/hip/vault)")
    lines.append("- [ ] Chimney present when map shows FIRIN or equivalent")
    lines.append("- [ ] Party walls have no windows")
    lines.append("- [ ] Material palette looks right for class A/B/C")
    lines.append("- [ ] Windows reasonable count/size for street length")

    out = out_dir / f"{parcel_id.replace('/','_')}_profile.md"
    out.write_text("\n".join(lines))
    return out
