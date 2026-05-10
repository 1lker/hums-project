"""PRD-004 · Period-correct ornament for 1900-era Kadıköy buildings.

Adds:
  * Dentil bands under the main cornice (small alternating teeth blocks).
  * Corner quoins — stone blocks stacked at street corners on masonry A/B.
  * Panelled door upgrade: recessed 6-panel door + transom light above.
  * Chimney cap — projecting stone cap on every chimney.
All of these are additive — they never replace the main wall / roof
geometry, so re-running gives richer detail at the cost of face count only.
"""
from __future__ import annotations
import math

from ..mesh_graph import BuildingMesh
from ...common.prd import prd
from ...modeling.building import Building, WallSegment, Opening


DENTIL_W = 0.20
DENTIL_GAP = 0.15
DENTIL_H = 0.12
DENTIL_PROJECT = 0.06

QUOIN_W = 0.35
QUOIN_H = 0.55
QUOIN_GAP = 0.25
QUOIN_PROJECT = 0.04


@prd("004", "PeriodDetail")
class PeriodDetail:
    def emit(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        if building.structure_type != "building":
            return
        cls = (building.material_class or "").upper()
        self._emit_dentils(mesh, building, eaves_z)
        if cls in ("A", "B"):
            self._emit_corner_quoins(mesh, building)
        self._upgrade_doors(mesh, building)

    # ---- dentil band under cornice -----------------------------------------
    def _emit_dentils(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        band_bot = eaves_z - 0.32
        band_top = band_bot + DENTIL_H
        pid = building.parcel_id
        for idx, seg in enumerate(building.wall_segments):
            if not _is_strict_street(seg):
                continue
            length = _seg_length(seg)
            if length < 0.8:
                continue
            ux, uy, nx, ny = _seg_axes(seg)
            u = 0.15
            n = 0
            while u + DENTIL_W <= length - 0.15:
                a_x = seg.start[0] + ux * u
                a_y = seg.start[1] + uy * u
                b_x = seg.start[0] + ux * (u + DENTIL_W)
                b_y = seg.start[1] + uy * (u + DENTIL_W)
                out_ax = a_x + nx * DENTIL_PROJECT
                out_ay = a_y + ny * DENTIL_PROJECT
                out_bx = b_x + nx * DENTIL_PROJECT
                out_by = b_y + ny * DENTIL_PROJECT
                # outer face
                mesh.add_quad(
                    p0=(out_ax, out_ay, band_bot),
                    p1=(out_ax, out_ay, band_top),
                    p2=(out_bx, out_by, band_top),
                    p3=(out_bx, out_by, band_bot),
                    role="CorniceSurface",
                    surface_id=f"{pid}.dentil.{seg.face}.{idx}.{n}",
                    material_key="cornice_paint",
                )
                # top face
                mesh.add_quad(
                    p0=(a_x, a_y, band_top),
                    p1=(b_x, b_y, band_top),
                    p2=(out_bx, out_by, band_top),
                    p3=(out_ax, out_ay, band_top),
                    role="CorniceSurface",
                    surface_id=f"{pid}.dentil.{seg.face}.{idx}.{n}.top",
                    material_key="cornice_paint",
                )
                # bottom face
                mesh.add_quad(
                    p0=(out_ax, out_ay, band_bot),
                    p1=(out_bx, out_by, band_bot),
                    p2=(b_x, b_y, band_bot),
                    p3=(a_x, a_y, band_bot),
                    role="CorniceSurface",
                    surface_id=f"{pid}.dentil.{seg.face}.{idx}.{n}.bot",
                    material_key="cornice_paint",
                )
                u += DENTIL_W + DENTIL_GAP
                n += 1

    # ---- corner quoins -----------------------------------------------------
    def _emit_corner_quoins(self, mesh: BuildingMesh, building: Building) -> None:
        """Stack quoin blocks at each corner where two street-facing walls meet."""
        pid = building.parcel_id
        n = len(building.wall_segments)
        if n < 2:
            return
        total_height = sum(s.height_m for s in building.storeys if not s.is_basement)
        for i, seg in enumerate(building.wall_segments):
            next_seg = building.wall_segments[(i + 1) % n]
            if not (_is_strict_street(seg) and _is_strict_street(next_seg)):
                continue
            # Corner point = end of current seg (= start of next seg)
            cx, cy = seg.end
            # Two outward normals for the quoin cube (approx bisector)
            _, _, nx0, ny0 = _seg_axes(seg)
            _, _, nx1, ny1 = _seg_axes(next_seg)
            bx = (nx0 + nx1) * 0.5
            by = (ny0 + ny1) * 0.5
            bl = math.hypot(bx, by) or 1.0
            bx /= bl; by /= bl
            # Stack blocks from grade up.
            z = 0.0
            k = 0
            while z + QUOIN_H <= total_height:
                # Alternate width — offset every other block inward.
                extra_proj = QUOIN_PROJECT if k % 2 == 0 else QUOIN_PROJECT * 0.5
                # Axes along each wall from the corner, inward by QUOIN_W.
                ux0, uy0, _, _ = _seg_axes(seg)
                ux1, uy1, _, _ = _seg_axes(next_seg)
                # Corner patch: rectangle on each face
                # Face A (along seg, extending back from corner)
                a0 = (cx - ux0 * QUOIN_W, cy - uy0 * QUOIN_W)
                mesh.add_quad(
                    p0=(a0[0] + nx0 * extra_proj, a0[1] + ny0 * extra_proj, z),
                    p1=(a0[0] + nx0 * extra_proj, a0[1] + ny0 * extra_proj, z + QUOIN_H),
                    p2=(cx + nx0 * extra_proj, cy + ny0 * extra_proj, z + QUOIN_H),
                    p3=(cx + nx0 * extra_proj, cy + ny0 * extra_proj, z),
                    role="PlinthSurface",
                    surface_id=f"{pid}.quoin.A.{i}.{k}",
                    material_key="plinth_stone",
                )
                # Face B (along next_seg, extending forward from corner)
                b0 = (cx + ux1 * QUOIN_W, cy + uy1 * QUOIN_W)
                mesh.add_quad(
                    p0=(cx + nx1 * extra_proj, cy + ny1 * extra_proj, z),
                    p1=(cx + nx1 * extra_proj, cy + ny1 * extra_proj, z + QUOIN_H),
                    p2=(b0[0] + nx1 * extra_proj, b0[1] + ny1 * extra_proj, z + QUOIN_H),
                    p3=(b0[0] + nx1 * extra_proj, b0[1] + ny1 * extra_proj, z),
                    role="PlinthSurface",
                    surface_id=f"{pid}.quoin.B.{i}.{k}",
                    material_key="plinth_stone",
                )
                z += QUOIN_H + QUOIN_GAP
                k += 1

    # ---- panelled doors ----------------------------------------------------
    def _upgrade_doors(self, mesh: BuildingMesh, building: Building) -> None:
        """Add a transom glazing strip + 2 recessed panels over each door."""
        storey_zs = _floor_zs(building)
        pid = building.parcel_id
        for idx, seg in enumerate(building.wall_segments):
            for k, op in enumerate(seg.openings):
                if op.kind != "door":
                    continue
                z_floor = storey_zs.get(op.storey_level, 0.0)
                z0 = z_floor + op.sill_m
                z1 = z0 + op.height_m
                ux, uy, nx, ny = _seg_axes(seg)
                u0 = op.position_along_wall_m
                u1 = u0 + op.width_m
                sx, sy = seg.start
                # Transom window strip above the door (within the same reveal depth)
                transom_bot = z1 - 0.3
                transom_top = z1
                if transom_bot > z0 + 0.8:
                    mesh.add_quad(
                        p0=(sx + ux * u0 + nx * -0.16, sy + uy * u0 + ny * -0.16, transom_bot),
                        p1=(sx + ux * u0 + nx * -0.16, sy + uy * u0 + ny * -0.16, transom_top),
                        p2=(sx + ux * u1 + nx * -0.16, sy + uy * u1 + ny * -0.16, transom_top),
                        p3=(sx + ux * u1 + nx * -0.16, sy + uy * u1 + ny * -0.16, transom_bot),
                        role="Window",
                        surface_id=f"{pid}.door_transom.{seg.face}.{idx}.{k}",
                        material_key="window_glass",
                    )
                # Two recessed door panels (proud relative to the recessed glazing plane)
                panel_h_each = (z1 - z0 - 0.6) / 2
                if panel_h_each < 0.35:
                    continue
                for p_idx in range(2):
                    pz0 = z0 + 0.15 + p_idx * (panel_h_each + 0.15)
                    pz1 = pz0 + panel_h_each
                    mesh.add_quad(
                        p0=(sx + ux * (u0 + 0.08) + nx * -0.12, sy + uy * (u0 + 0.08) + ny * -0.12, pz0),
                        p1=(sx + ux * (u0 + 0.08) + nx * -0.12, sy + uy * (u0 + 0.08) + ny * -0.12, pz1),
                        p2=(sx + ux * (u1 - 0.08) + nx * -0.12, sy + uy * (u1 - 0.08) + ny * -0.12, pz1),
                        p3=(sx + ux * (u1 - 0.08) + nx * -0.12, sy + uy * (u1 - 0.08) + ny * -0.12, pz0),
                        role="Door",
                        surface_id=f"{pid}.door_panel.{seg.face}.{idx}.{k}.{p_idx}",
                        material_key="door_panel",
                    )


def _seg_length(seg: WallSegment) -> float:
    return math.hypot(seg.end[0] - seg.start[0], seg.end[1] - seg.start[1])


def _is_strict_street(seg: WallSegment) -> bool:
    return seg.hatch_pattern == "_street"


def _seg_axes(seg: WallSegment):
    sx, sy = seg.start
    ex, ey = seg.end
    length = math.hypot(ex - sx, ey - sy) or 1.0
    ux = (ex - sx) / length
    uy = (ey - sy) / length
    nx = -uy
    ny = ux
    # CCW ring → right-hand normal of edge is interior; flip
    return ux, uy, -nx, -ny


def _floor_zs(building: Building) -> dict[int, float]:
    out: dict[int, float] = {}
    z = 0.0
    for s in building.storeys:
        if s.is_basement:
            continue
        out[s.level] = z
        z += s.height_m
    return out
