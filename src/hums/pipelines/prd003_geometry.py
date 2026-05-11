"""PRD-003 pipeline orchestrator — buildings.json → IFC + glTF + reports."""
from __future__ import annotations
import json
from pathlib import Path

from shapely.geometry import Polygon, shape

from ..common.heritage_profile import PROFILE
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
from ..render.scene.street_mesh import load_block_ring_local
from ..render.special.church_builder import ChurchBuilder
from ..render.special.landscape_builder import CourtyardGardenBuilder, N50_REAR_LIGHTWELL_UTM
from .render_manual import ManualRenderer

BUILDINGS_JSON = PARSED / "buildings.json"
OUTPUT = PROJECT_ROOT / "output"
IFC_DIR = OUTPUT / "ifc"
GLTF_DIR = OUTPUT / "gltf"
REPORT_DIR = OUTPUT / "reports"

MANUAL_SCENE_REPLACEMENTS = {
    "N-40-42": {"N-40", "N-42"},
    "N-52-54-E2": {"N-52", "N-54", "E-2"},
    "S-41-43-45-E16": {"S-41", "S-43", "S-45", "E-16"},
    "W-34-36-FIRIN": {"W-34", "W-36"},
    "W-39-1": {"W-39/1"},
}


@prd("003", "Pipeline")
class Prd003Pipeline:
    def run(self) -> dict:
        buildings = [_building_from_dict(d) for d in json.loads(BUILDINGS_JSON.read_text())]
        geom_builder = BuildingGeometryBuilder()
        meshes = []
        manual_meshes, replaced_parcels = _manual_replacement_meshes()
        for b in buildings:
            if b.parcel_id in replaced_parcels:
                continue
            _apply_map_review_overrides(b)
            m = geom_builder.build(b)
            if m:
                meshes.append(m)
        meshes.extend(manual_meshes)

        block_centroid = _block_centroid()
        church_mesh = ChurchBuilder().build(block_centroid)
        if church_mesh is not None:
            meshes.append(church_mesh)
        meshes.extend(CourtyardGardenBuilder().build_all())
        scene = SceneAssembler().assemble(meshes, block_centroid)
        block_ring = load_block_ring_local(block_centroid)
        if block_ring:
            scene.metadata["block_ring_local"] = block_ring

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


def _apply_map_review_overrides(building: Building) -> None:
    """Corrections from direct Pervititch-map rereads that supersede Excel text.

    Keep these narrow: they are only for parcels where the enlarged map crop
    contradicts the parsed register enough to affect visible massing.
    """
    if building.parcel_id == "E-12":
        building.notes["map_review_2026_05_11"] = (
            "Raw map reads closer to 1p.Mg/VF with a barrel/vault roof mark; "
            "do not model the old parsed 2p as a full second storey."
        )
        # The previous 2p parse generated upper windows. The map reread treats
        # this as a one-storey shop, so keep only ground-level/door openings.
        building.storeys = [
            s for s in building.storeys
            if s.is_basement or s.level == 0
        ]
        for seg in building.wall_segments:
            seg.openings = [
                op for op in seg.openings
                if op.kind == "door" or op.storey_level == 0
            ]
        if building.roof:
            building.roof.shape = "vault_flat"
            building.roof.material = "tile_TF"
            building.roof.pitch_deg = 12.0
            building.roof.slope_direction = (
                "Barrel/vault roof from map VF mark; tile material retained from TF note"
            )

    elif building.parcel_id == "E-10":
        building.notes["map_review_2026_05_11"] = (
            "Map has an additional direction marker near the 10 entrance. "
            "Keep as one-storey VF/TF shop but preserve the direction note for roof review."
        )
        if building.roof:
            building.roof.slope_direction = "Map direction marker near 10 entrance; not a height split"

    elif building.parcel_id == "E-14":
        building.notes["map_review_2026_05_11"] = (
            "Checked for a possible two-height split. Crop shows roof/hatch marks "
            "and the entrance arrow, but no confirmed internal height boundary."
        )

    elif building.parcel_id == "N-50":
        building.notes["map_review_2026_05_11"] = (
            "Georeferenced reread found a small rectangular rear open lightwell "
            "between N-50 and the N-52/54 corner mass. The short rear-east face "
            "is treated as courtyard-exposed, not a same-height party wall."
        )
        _cut_n50_rear_lightwell_from_mass(building)
        _ensure_n50_rear_lightwell_windows(building)


def _cut_n50_rear_lightwell_from_mass(building: Building) -> None:
    """Cut the map-visible rectangular void out of parcel 50's massing.

    The traced N-50 SHP includes the small right/rear rectangular void visible
    on the Pervititch crop. Rendering the SHP literally makes the void vanish
    under the building roof, so the scene-level correction must change the
    actual N-50 footprint, not just add a lightwell marker on top.
    """
    if not building.local_frame or not building.footprint_local:
        return
    ox, oy = building.local_frame.origin_utm
    current = Polygon([(x + ox, y + oy) for x, y in building.footprint_local]).buffer(0)
    void = Polygon(N50_REAR_LIGHTWELL_UTM).buffer(0)
    cut = current.difference(void).buffer(0)
    if cut.is_empty:
        return
    if cut.geom_type == "MultiPolygon":
        polys = [p for p in cut.geoms if p.area > 0.25]
        if not polys:
            return
        cut = max(polys, key=lambda p: p.area)
    if cut.geom_type != "Polygon" or cut.area < current.area * 0.70:
        return

    coords = _clean_ring([(x, y) for x, y in list(cut.exterior.coords)[:-1]])
    if len(coords) < 4:
        return
    if _signed_area_utm(coords) < 0:
        coords.reverse()

    building.footprint_local = [
        (round(x - ox, 4), round(y - oy, 4))
        for x, y in coords
    ]
    building.wall_segments = _n50_segments_from_cut_ring(building, coords)
    building.notes["n50_rear_lightwell_cut"] = (
        "N-50 massing footprint cut by the map-visible rectangular rear/right "
        "void; void area is approximately one eighth of the original parcel."
    )


def _n50_segments_from_cut_ring(building: Building, coords_utm: list[tuple[float, float]]) -> list[WallSegment]:
    assert building.local_frame is not None
    ox, oy = building.local_frame.origin_utm
    local = [(x - ox, y - oy) for x, y in coords_utm]
    total_h = sum(s.height_m for s in building.storeys if not s.is_basement)

    segments: list[WallSegment] = []
    for idx, (a, b) in enumerate(zip(local, local[1:] + local[:1])):
        au = coords_utm[idx]
        bu = coords_utm[(idx + 1) % len(coords_utm)]
        length = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        face = _face_from_utm_edge(au, bu)
        is_top_street = length < 4.2 and max(au[1], bu[1]) > 4539716.0
        is_lightwell_edge = _edge_touches_n50_lightwell(au, bu)
        adjacent = None if is_top_street or is_lightwell_edge else (
            7.0 if length > 8.0 else total_h
        )
        seg = WallSegment(
            start=(round(a[0], 4), round(a[1], 4)),
            end=(round(b[0], 4), round(b[1], 4)),
            thickness_m=0.55,
            face=face if (is_top_street or is_lightwell_edge or adjacent is None) else "INT",
            is_street_facing=is_top_street or is_lightwell_edge or adjacent is None,
            is_party_wall=adjacent is not None and not is_lightwell_edge and not is_top_street,
            adjacent_height_m=adjacent,
            hatch_pattern="_street" if is_top_street else None,
        )
        segments.append(seg)

    _restore_n50_openings_after_cut(building, segments)
    return segments


def _restore_n50_openings_after_cut(building: Building, segments: list[WallSegment]) -> None:
    o = PROFILE.openings
    top = max(
        (s for s in segments if s.length_m > 1.5),
        key=lambda s: ((s.start[1] + s.end[1]) * 0.5, -abs(s.length_m - 3.4)),
    )
    door_w = min(o.door_w_m, max(0.78, top.length_m - 0.9))
    door_pos = max(0.28, (top.length_m - door_w) / 2.0)
    top.openings.append(Opening(
        kind="door",
        storey_level=0,
        position_along_wall_m=round(door_pos, 3),
        width_m=round(door_w, 3),
        height_m=o.door_h_m,
        sill_m=0.0,
        style="rectangular",
        frame_profile="moulded",
        color_source="map:pervititch",
    ))
    for level in (1, 2):
        top.openings.append(Opening(
            kind="window",
            storey_level=level,
            position_along_wall_m=round(door_pos, 3),
            width_m=round(min(o.upper_window_w_m, door_w), 3),
            height_m=o.upper_window_h_m,
            sill_m=o.upper_window_sill_m,
            style="rectangular",
            pane_layout="2x2",
            frame_profile="moulded",
            color_source="map:geometry-detected:street-exposed-facade",
        ))

    long_party = [
        s for s in segments
        if s.length_m > 7.0 and s.is_party_wall and (s.adjacent_height_m or 0) < 9.0
    ]
    if long_party:
        seg = max(long_party, key=lambda s: s.length_m)
        for pos in (seg.length_m * 0.23, seg.length_m * 0.50, seg.length_m * 0.77):
            seg.openings.append(Opening(
                kind="window",
                storey_level=2,
                position_along_wall_m=round(max(0.35, min(seg.length_m - o.upper_window_w_m - 0.35, pos)), 3),
                width_m=o.upper_window_w_m,
                height_m=o.upper_window_h_m,
                sill_m=o.upper_window_sill_m,
                style="rectangular",
                pane_layout="2x2",
                frame_profile="moulded",
                color_source="map:geometry-detected:height-difference-exposed-party-wall",
            ))


def _ensure_n50_rear_lightwell_windows(building: Building) -> None:
    candidates = [
        seg for seg in building.wall_segments
        if 2.0 <= seg.length_m <= 5.0
        and (
            seg.adjacent_height_m is not None and seg.adjacent_height_m >= 9.0
            or _local_edge_touches_n50_lightwell(building, seg)
        )
    ]
    if not candidates:
        return
    target = max(candidates, key=lambda seg: seg.length_m)
    target.is_party_wall = False
    target.is_street_facing = True
    target.adjacent_height_m = None
    target.hatch_pattern = None

    source = "map:georeference:n50-rear-lightwell-window"
    if any(op.kind == "window" and op.color_source == source for op in target.openings):
        return
    o = PROFILE.openings
    width = min(o.upper_window_w_m, max(0.72, target.length_m - 0.72))
    pos = max(0.28, (target.length_m - width) / 2.0)
    upper_levels = [
        s.level for s in building.storeys
        if s.level >= 1 and not s.is_basement
    ]
    for level in upper_levels[:2]:
        target.openings.append(Opening(
            kind="window",
            storey_level=level,
            position_along_wall_m=round(pos, 3),
            width_m=round(width, 3),
            height_m=o.upper_window_h_m,
            sill_m=o.upper_window_sill_m,
            style="rectangular",
            pane_layout="2x2",
            has_shutters=building.material_class == "C",
            frame_profile="moulded",
            color_source=source,
        ))


def _clean_ring(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
    deduped: list[tuple[float, float]] = []
    for p in coords:
        if not deduped or _pt_dist(p, deduped[-1]) > 0.08:
            deduped.append(p)
    if len(deduped) > 1 and _pt_dist(deduped[0], deduped[-1]) <= 0.08:
        deduped.pop()

    changed = True
    while changed and len(deduped) >= 4:
        changed = False
        out: list[tuple[float, float]] = []
        n = len(deduped)
        for i, p in enumerate(deduped):
            a = deduped[(i - 1) % n]
            b = deduped[(i + 1) % n]
            if _point_line_distance(p, a, b) < 0.06:
                changed = True
                continue
            out.append(p)
        deduped = out
    return deduped


def _face_from_utm_edge(a: tuple[float, float], b: tuple[float, float]) -> str:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    ang = __import__("math").degrees(__import__("math").atan2(-dx, dy))
    if -45 <= ang < 45:
        return "N"
    if 45 <= ang < 135:
        return "E"
    if -135 <= ang < -45:
        return "W"
    return "S"


def _edge_touches_n50_lightwell(a: tuple[float, float], b: tuple[float, float]) -> bool:
    from shapely.geometry import LineString
    line = LineString([a, b])
    void_edge = Polygon(N50_REAR_LIGHTWELL_UTM).exterior
    if line.intersection(void_edge).length > 0.20:
        return True
    # If the coordinates are slightly off after polygon difference, require
    # an actual edge overlap area, not just a shared corner point.
    return line.buffer(0.04, cap_style=2).intersection(void_edge.buffer(0.04)).area > 0.025


def _local_edge_touches_n50_lightwell(building: Building, seg: WallSegment) -> bool:
    if not building.local_frame:
        return False
    ox, oy = building.local_frame.origin_utm
    a = (seg.start[0] + ox, seg.start[1] + oy)
    b = (seg.end[0] + ox, seg.end[1] + oy)
    return _edge_touches_n50_lightwell(a, b)


def _signed_area_utm(coords: list[tuple[float, float]]) -> float:
    return sum(
        coords[i][0] * coords[(i + 1) % len(coords)][1]
        - coords[(i + 1) % len(coords)][0] * coords[i][1]
        for i in range(len(coords))
    ) / 2.0


def _point_line_distance(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    import math
    ax, ay = a
    bx, by = b
    px, py = p
    dx = bx - ax
    dy = by - ay
    denom = math.hypot(dx, dy)
    if denom <= 0.001:
        return _pt_dist(p, a)
    return abs(dy * px - dx * py + bx * ay - by * ax) / denom


def _pt_dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _block_centroid() -> tuple[float, float]:
    feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
    if not feats:
        return (0.0, 0.0)
    c = shape(feats[0]["geometry"]).centroid
    return (c.x, c.y)


def _manual_replacement_meshes() -> tuple[list, set[str]]:
    meshes = []
    replaced_parcels: set[str] = set()
    renderer = ManualRenderer()
    for label_key, configured_parcels in MANUAL_SCENE_REPLACEMENTS.items():
        label, label_meshes, _ = renderer.build_meshes(label_key)
        meshes.extend(label_meshes)
        replaced_parcels.update(configured_parcels)
        replaced_parcels.update(label.parcel_ids)
        for mesh in label_meshes:
            mesh.metadata["manual_scene_replacement"] = label.label
            mesh.metadata["replaces_parcels"] = sorted(label.parcel_ids)
    return meshes, replaced_parcels


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
            is_party_wall=seg.get("is_party_wall", False),
            adjacent_height_m=seg.get("adjacent_height_m"),
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
