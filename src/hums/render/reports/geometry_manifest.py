"""PRD-003 · §11 — per-building geometry manifest + LOD3 coverage report."""
from __future__ import annotations
from pathlib import Path

from ...common.prd import prd
from ..mesh_graph import SceneGraph


REQUIRED_LOD3_ROLES = ["GroundSurface", "WallSurface", "RoofSurface", "Window", "Door"]


@prd("003", "§11 geometry_manifest")
def write_reports(scene: SceneGraph, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_manifest(scene, out_dir / "geometry_manifest.md")
    _write_lod3_coverage(scene, out_dir / "lod3_coverage.md")


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
             "Required roles per building: " + ", ".join(REQUIRED_LOD3_ROLES) + ".\n",
             "| parcel_id | GroundSurface | WallSurface | RoofSurface | Window | Door | complete? |",
             "|---|---|---|---|---|---|---|"]
    incomplete: list[str] = []
    for b in scene.buildings:
        counts = b.face_count_by_role()
        row = [b.parcel_id]
        complete = True
        for role in REQUIRED_LOD3_ROLES:
            n = counts.get(role, 0)
            row.append(str(n))
            if n == 0 and b.metadata.get("structure_type") == "building":
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
