"""PRD-003 · §11 — per-building geometry manifest + LOD3 coverage report."""
from __future__ import annotations
import json
from pathlib import Path

from ...common.paths import PARSED
from ...common.prd import prd
from ..mesh_graph import SceneGraph


REQUIRED_LOD3_ROLES = ["GroundSurface", "WallSurface", "RoofSurface", "Window", "Door"]


@prd("003", "§11 geometry_manifest")
def write_reports(scene: SceneGraph, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_manifest(scene, out_dir / "geometry_manifest.md")
    _write_lod3_coverage(scene, out_dir / "lod3_coverage.md")
    _write_opening_audit(scene, out_dir / "opening_audit.md")
    _write_roof_visual_audit(scene, out_dir / "roof_visual_audit.md")
    _write_scene_source_audit(scene, out_dir / "scene_source_audit.md")
    _write_adjacency_opening_audit(out_dir / "adjacency_opening_audit.md")


def _write_manifest(scene: SceneGraph, path: Path) -> None:
    lines = ["# PRD-003 Geometry Manifest\n",
             f"Buildings: **{len(scene.buildings)}**",
             f"Block centroid (UTM 35N): {scene.block_centroid_utm}\n",
             "| parcel_id | vertices | faces | roles | palette.source | footprint |",
             "|---|---|---|---|---|---|"]
    for b in scene.buildings:
        roles = ", ".join(sorted(b.face_count_by_role()))
        palette_src = getattr(b.palette, "source", "") if b.palette else ""
        lines.append(
            f"| {b.parcel_id} | {len(b.vertices)} | {len(b.faces)} | {roles} | "
            f"{palette_src} | {b.metadata.get('footprint_source','?')} |")
    path.write_text("\n".join(lines) + "\n")


def _write_lod3_coverage(scene: SceneGraph, path: Path) -> None:
    lines = ["# PRD-003 LOD3 Role Coverage\n",
             "Required roles per building: " + ", ".join(REQUIRED_LOD3_ROLES)
             + ". One-storey Mg/shop volumes may intentionally have no Window role when the map gives a door but no vitrine/window evidence.\n",
             "| parcel_id | GroundSurface | WallSurface | RoofSurface | Window | Door | complete? |",
             "|---|---|---|---|---|---|---|"]
    incomplete: list[str] = []
    intentional_closed = _intentional_no_exterior_openings()
    for b in scene.buildings:
        counts = b.face_count_by_role()
        row = [b.parcel_id]
        complete = True
        for role in REQUIRED_LOD3_ROLES:
            n = counts.get(role, 0)
            row.append(str(n))
            if (
                n == 0
                and b.metadata.get("structure_type") == "building"
                and not (role in {"Window", "Door"} and b.parcel_id in intentional_closed)
                and not (role == "Window" and _window_absence_is_intentional(counts))
                and not _manual_opening_absence_is_intentional(b, role)
            ):
                complete = False
        row.append("✅" if complete else "⚠️")
        if not complete:
            incomplete.append(b.parcel_id)
        lines.append("| " + " | ".join(row) + " |")

    if incomplete:
        lines.append("\n## Incomplete buildings (missing required roles)\n")
        for pid in incomplete:
            lines.append(f"- {pid}")
    path.write_text("\n".join(lines) + "\n")


def _window_absence_is_intentional(counts: dict[str, int]) -> bool:
    # Ground-floor-only shops/magazines often have only the mapped entrance.
    # Do not force invented windows where the Pervititch map gives no vitrine,
    # no camli note, and no upper storey.
    return counts.get("Door", 0) > 0 and counts.get("FloorSurface", 0) == 0


def _manual_opening_absence_is_intentional(mesh, role: str) -> bool:
    if role not in {"Window", "Door"}:
        return False
    notes = mesh.metadata.get("notes") or {}
    if not isinstance(notes, dict):
        return False
    text = " ".join(str(v) for v in (
        notes.get("zone_id"),
        notes.get("description"),
        " ".join(notes.get("map_labels") or []),
    ) if v).lower()
    return any(token in text for token in (
        "church_service_annex",
        "church edge",
        "opaque timber annex",
        "wooden/yellow",
    ))


def _intentional_no_exterior_openings() -> set[str]:
    buildings_path = PARSED / "buildings.json"
    if not buildings_path.exists():
        return set()
    out: set[str] = set()
    for b in json.loads(buildings_path.read_text()):
        segments = b.get("wall_segments") or []
        opening_count = sum(len(s.get("openings") or []) for s in segments)
        if opening_count:
            continue
        text_parts = [
            (b.get("excel_snapshot") or {}).get("bim_notes"),
            ((b.get("excel_snapshot") or {}).get("street_facing")),
            str(b.get("notes") or ""),
        ]
        text = " ".join(str(t) for t in text_parts if t).lower()
        if any(token in text for token in ("internal only", "no street", "no direct street", "no arrow")):
            out.add(b["parcel_id"])
    return out


def _write_opening_audit(scene: SceneGraph, path: Path) -> None:
    buildings_path = PARSED / "buildings.json"
    if not buildings_path.exists():
        path.write_text("# Opening And Material Audit\n\n_No buildings.json available._\n")
        return

    buildings = json.loads(buildings_path.read_text())
    visible_meshes = {mesh.parcel_id: mesh for mesh in scene.buildings}
    replaced_parcels = {
        parcel_id
        for mesh in scene.buildings
        for parcel_id in mesh.metadata.get("replaces_parcels", [])
    }
    lines = [
        "# Opening And Material Audit\n",
        "Doors, shopfronts, and vitrines are restricted to map/manual evidence. Upper-floor windows are allowed only on geometry-detected exposed street/courtyard faces or party walls exposed by a lower neighbor.\n",
        "| parcel_id | material | footprint | strict street edges | doors | shopfronts | upper windows | source notes |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for b in buildings:
        if b.get("parcel_id") in replaced_parcels:
            continue
        if b.get("footprint_source") in {"missing", "absorbed"}:
            continue
        mesh = visible_meshes.get(b.get("parcel_id"))
        segments = b.get("wall_segments") or []
        counts = {"door": 0, "shop_window": 0, "window": 0}
        source_counts: dict[str, int] = {}
        if mesh and mesh.metadata.get("opening_counts"):
            counts.update(mesh.metadata.get("opening_counts") or {})
            source_counts.update(mesh.metadata.get("opening_source_counts") or {})
        else:
            for seg in segments:
                for op in seg.get("openings") or []:
                    kind = op.get("kind")
                    if kind in counts:
                        counts[kind] += 1
                    src = op.get("color_source") or "unknown"
                    source_counts[src] = source_counts.get(src, 0) + 1

        notes = []
        bim_notes = (b.get("excel_snapshot") or {}).get("bim_notes")
        visible_notes = (mesh.metadata.get("notes") if mesh else None) or b.get("notes") or {}
        source_text = " ".join(str(v) for v in (bim_notes, visible_notes) if v).lower()
        if counts["door"] == 0 and counts["shop_window"] == 0 and counts["window"] == 0:
            if b.get("structure_type") != "building":
                notes.append("non-building asset")
            elif any(token in source_text for token in ("internal only", "no street", "no direct street", "no arrow")):
                notes.append("closed by map/notes")
            else:
                notes.append("needs manual opening placement")
        notes.extend(f"{src}: {n}" for src, n in sorted(source_counts.items()))
        if bim_notes and any(token in str(bim_notes).lower() for token in ("no street", "internal", "glazed", "dual", "arrow")):
            notes.append(str(bim_notes).replace("|", "/"))
        if isinstance(visible_notes, dict) and visible_notes.get("map_review_2026_05_11"):
            notes.append(str(visible_notes["map_review_2026_05_11"]).replace("|", "/"))

        lines.append(
            "| {pid} | {mat} | {footprint} | {streets} | {doors} | {shops} | {windows} | {notes} |".format(
                pid=b.get("parcel_id"),
                mat=b.get("material_class") or "",
                footprint=(b.get("provenance") or {}).get("footprint_source_file") or b.get("footprint_source") or "",
                streets=sum(1 for s in segments if s.get("hatch_pattern") == "_street"),
                doors=counts["door"],
                shops=counts["shop_window"],
                windows=counts["window"],
                notes="<br>".join(notes) if notes else "none",
            )
        )
    for mesh in scene.buildings:
        label = mesh.metadata.get("manual_scene_replacement")
        if not label:
            continue
        counts = mesh.metadata.get("opening_counts") or {}
        lines.append(
            "| {pid} | {mat} | {footprint} | {streets} | {doors} | {shops} | {windows} | {notes} |".format(
                pid=mesh.parcel_id,
                mat=mesh.metadata.get("material_class") or "",
                footprint=mesh.metadata.get("source_footprint_file") or "manual",
                streets="manual",
                doors=counts.get("door", 0),
                shops=counts.get("shop_window", 0),
                windows=counts.get("window", 0),
                notes=f"manual map-zoned replacement for {', '.join(mesh.metadata.get('replaces_parcels', []))}",
            )
        )
    path.write_text("\n".join(lines) + "\n")


def _write_roof_visual_audit(scene: SceneGraph, path: Path) -> None:
    lines = [
        "# Roof Visual Audit\n",
        "Roof shapes and materials used by the visible scene. Material keys are the glTF/BIM presentation materials, not raw Pervititch text.\n",
        "| parcel_id | shape | source material | pitch | rendered roof materials | note |",
        "|---|---|---|---:|---|---|",
    ]
    for mesh in scene.buildings:
        roof_materials = sorted({
            f.material_key
            for f in mesh.faces
            if f.semantic_role in {"RoofSurface", "ChurchDome", "Skylight"}
        })
        shape = mesh.metadata.get("roof_shape") or (
            "church_special" if mesh.metadata.get("structure_type") == "church" else ""
        )
        material = mesh.metadata.get("roof_material") or (
            "kiremit + lead/zinc dome" if mesh.metadata.get("structure_type") == "church" else ""
        )
        pitch = mesh.metadata.get("roof_pitch_deg")
        note = ""
        if "window_glass" in roof_materials and material == "glass_roof":
            note = "Camlı/Vitre rendered as glazed roof"
        elif "roof_unknown_muted" in roof_materials:
            note = "map roof material unreadable; muted neutral used"
        elif "vault_roof_masonry" in roof_materials:
            note = "VF/VT rendered as shallow barrel/vault roof"
        elif "tile_marseille" in roof_materials:
            note = "TF rendered as French/Marseille clay tile"
        elif "sheet_metal_grey" in roof_materials:
            note = "T rendered as aged sheet metal"
        elif mesh.metadata.get("structure_type") == "church":
            clocher_top = mesh.metadata.get("clocher_top_m")
            clocher_src = mesh.metadata.get("clocher_source")
            dome_src = mesh.metadata.get("dome_center_source")
            dome_center = mesh.metadata.get("dome_center_utm")
            if clocher_top and clocher_src:
                note = f"special church roof: low tile body, high drum/kubbe"
                if dome_src and dome_center:
                    note += f"; kubbe centered at {dome_center} from {dome_src}"
                note += f"; clocher {clocher_top} m from {clocher_src}"
            else:
                note = "special church roof: low tile body, high drum/kubbe, clocher"
        direction = mesh.metadata.get("roof_slope_direction")
        if direction and mesh.parcel_id in {"E-10", "E-12", "E-14"}:
            note = f"{note}; {direction}" if note else str(direction)
        lines.append(
            "| {pid} | {shape} | {material} | {pitch} | {keys} | {note} |".format(
                pid=mesh.parcel_id,
                shape=shape,
                material=material,
                pitch="" if pitch is None else pitch,
                keys=", ".join(roof_materials) if roof_materials else "",
                note=note,
            )
        )
    path.write_text("\n".join(lines) + "\n")


def _write_scene_source_audit(scene: SceneGraph, path: Path) -> None:
    lines = [
        "# Scene Source Audit\n",
        "Visible 3D meshes only. This report is used to catch any independent interior/stub buildings that were not traced from a KML/SHP/manual source.\n",
        "| parcel_id | footprint_source | source file | manual replacement | warning |",
        "|---|---|---|---|---|",
    ]
    warnings: list[str] = []
    for mesh in scene.buildings:
        source = mesh.metadata.get("source_footprint_file") or ""
        manual = mesh.metadata.get("manual_scene_replacement") or ""
        footprint_source = mesh.metadata.get("footprint_source") or ""
        structure_type = mesh.metadata.get("structure_type") or ""
        warning = ""
        if footprint_source not in {"traced"}:
            warning = "not traced"
        if footprint_source == "map-interpreted" and structure_type in {
            "courtyard_garden",
            "courtyard_lightwell",
        }:
            warning = ""
        if mesh.parcel_id.startswith("INT-"):
            warning = "independent INT mesh should not be visible"
        if not source and not manual and mesh.parcel_id != "CHURCH":
            warning = warning or "missing source file"
        if warning:
            warnings.append(mesh.parcel_id)
        lines.append(
            f"| {mesh.parcel_id} | {footprint_source} | {source} | {manual} | {warning} |"
        )
    if warnings:
        lines.append("\n## Warnings\n")
        for pid in warnings:
            lines.append(f"- {pid}")
    else:
        lines.append("\nNo independent INT/stub/missing-source meshes are visible in the scene.")
    path.write_text("\n".join(lines) + "\n")


def _write_adjacency_opening_audit(path: Path) -> None:
    buildings_path = PARSED / "buildings.json"
    if not buildings_path.exists():
        path.write_text("# Adjacency Opening Audit\n\n_No buildings.json available._\n")
        return
    buildings = json.loads(buildings_path.read_text())
    lines = [
        "# Adjacency Opening Audit\n",
        "Checks the rule: no openings on same-height party walls; openings on party walls are allowed only where the current building rises above the neighbor.\n",
        "| parcel_id | party openings | height-difference party openings | same-height violations | exterior/courtyard upper windows | street upper windows |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    total_violations = 0
    for b in buildings:
        if b.get("footprint_source") != "traced":
            continue
        party = height_diff = violations = courtyard = street = 0
        height = sum(s.get("height_m", 0.0) for s in b.get("storeys") or [] if not s.get("is_basement"))
        for seg in b.get("wall_segments") or []:
            adjacent = seg.get("adjacent_height_m")
            for op in seg.get("openings") or []:
                if op.get("kind") != "window":
                    continue
                src = op.get("color_source") or ""
                if seg.get("is_party_wall"):
                    party += 1
                    if "height-difference" in src:
                        height_diff += 1
                    else:
                        if adjacent is None or adjacent >= height - 0.2:
                            violations += 1
                elif seg.get("hatch_pattern") == "_street":
                    street += 1
                else:
                    courtyard += 1
        total_violations += violations
        if any((party, height_diff, violations, courtyard, street)):
            lines.append(
                f"| {b.get('parcel_id')} | {party} | {height_diff} | {violations} | {courtyard} | {street} |"
            )
    lines.append(f"\nSame-height party-wall opening violations: **{total_violations}**")
    path.write_text("\n".join(lines) + "\n")
