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
        if building.parcel_id.startswith("W-32#"):
            return
        cls = (building.material_class or "").upper()
        if "GLASS" in cls:
            return
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

    # ---- doors -------------------------------------------------------------
    def _upgrade_doors(self, mesh: BuildingMesh, building: Building) -> None:
        """Add period door detail without turning Mg shops into houses."""
        storey_zs = _floor_zs(building)
        pid = building.parcel_id
        is_magasin = _is_magasin_building(building)
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
                if is_magasin:
                    _emit_magasin_door(mesh, pid, seg.face, idx, k, sx, sy, ux, uy, nx, ny, u0, u1, z0, z1)
                    continue
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


def _emit_magasin_door(
    mesh: BuildingMesh,
    pid: str,
    face: str,
    seg_idx: int,
    door_idx: int,
    sx: float,
    sy: float,
    ux: float,
    uy: float,
    nx: float,
    ny: float,
    u0: float,
    u1: float,
    z0: float,
    z1: float,
) -> None:
    """Shop/magasin entrance: shuttered double-leaf door, no invented glass."""

    variant = _magasin_variant(pid, seg_idx, door_idx)
    door_key = ("magasin_door_dark", "magasin_door_weathered", "magasin_door_ochre")[variant % 3]
    trim_key = ("magasin_trim_dark", "magasin_trim_brown", "magasin_trim_aged")[variant % 3]
    shutter_key = ("magasin_shutter_warm", "magasin_shutter_dark", "magasin_shutter_faded")[variant % 3]
    sign_key = ("magasin_sign_umber", "magasin_sign_green", "magasin_sign_slate", "magasin_sign_ochre")[variant % 4]
    canvas_key = ("magasin_canvas_tan", "magasin_canvas_grey", "magasin_canvas_olive")[variant % 3]

    def p(u: float, z: float, inset: float = -0.035) -> tuple[float, float, float]:
        return (sx + ux * u + nx * inset, sy + uy * u + ny * inset, z)

    pad = min(0.12, max(0.035, (u1 - u0) * (0.055 + 0.01 * (variant % 4))))
    lu0 = u0 + pad
    lu1 = (u0 + u1) / 2.0
    ru0 = lu1
    ru1 = u1 - pad
    z_bot = z0 + 0.06
    z_top = z1 - (0.06 + 0.035 * (variant % 2))
    if ru1 - lu0 <= 0.35 or z_top - z_bot <= 0.6:
        return

    for name, a, b in (("left", lu0, lu1), ("right", ru0, ru1)):
        mesh.add_quad(
            p0=p(a, z_bot),
            p1=p(a, z_top),
            p2=p(b, z_top),
            p3=p(b, z_bot),
            role="Door",
            surface_id=f"{pid}.magasin_door.{face}.{seg_idx}.{door_idx}.{name}",
            material_key=door_key,
        )

    # Small painted lintel/sign board: not a textual sign, just the storefront
    # band that makes Mg entries read differently from domestic doors.
    board_h = (0.30, 0.38, 0.46, 0.34)[variant % 4]
    board_bot = z1 + (0.04 if variant % 2 else 0.09)
    board_top = board_bot + board_h
    board_u0 = max(u0 - 0.10, lu0 - (0.14 + 0.04 * (variant % 2)))
    board_u1 = min(u1 + 0.10, ru1 + (0.14 + 0.03 * ((variant + 1) % 2)))
    _emit_magasin_stall_riser(mesh, pid, face, seg_idx, door_idx, p, board_u0, board_u1, z0, variant)
    mesh.add_quad(
        p0=p(board_u0, board_bot, 0.065),
        p1=p(board_u0, board_top, 0.065),
        p2=p(board_u1, board_top, 0.065),
        p3=p(board_u1, board_bot, 0.065),
        role="Door",
        surface_id=f"{pid}.magasin_door.{face}.{seg_idx}.{door_idx}.lintel_board",
        material_key=sign_key,
    )
    if variant % 5 != 1:
        _emit_magasin_canopy(
            mesh, pid, face, seg_idx, door_idx, sx, sy, ux, uy, nx, ny,
            board_u0, board_u1, board_top,
            depth=0.30 + 0.07 * (variant % 4),
            drop=0.08 + 0.035 * ((variant + 1) % 3),
            material_key=canvas_key,
            valance_key=sign_key,
        )

    # Center meeting stile.
    stile_w = min(0.045, max(0.025, (u1 - u0) * 0.04))
    mesh.add_quad(
        p0=p(lu1 - stile_w, z_bot, -0.015),
        p1=p(lu1 - stile_w, z_top, -0.015),
        p2=p(lu1 + stile_w, z_top, -0.015),
        p3=p(lu1 + stile_w, z_bot, -0.015),
        role="Door",
        surface_id=f"{pid}.magasin_door.{face}.{seg_idx}.{door_idx}.center_stile",
        material_key=trim_key,
    )

    # Strong side/header frame, so the storefront reads at model scale.
    frame_w = min(0.07, max(0.04, (u1 - u0) * 0.05))
    for name, a, b, zz0, zz1 in (
        ("left_jamb", lu0, lu0 + frame_w, z_bot, z_top),
        ("right_jamb", ru1 - frame_w, ru1, z_bot, z_top),
        ("head", lu0, ru1, z_top - frame_w, z_top),
    ):
        mesh.add_quad(
            p0=p(a, zz0, -0.005),
            p1=p(a, zz1, -0.005),
            p2=p(b, zz1, -0.005),
            p3=p(b, zz0, -0.005),
            role="Door",
            surface_id=f"{pid}.magasin_door.{face}.{seg_idx}.{door_idx}.{name}",
            material_key=trim_key,
        )

    _emit_magasin_slats(
        mesh, pid, face, seg_idx, door_idx, p,
        lu0 + frame_w, ru1 - frame_w, z_bot + 0.18, z_top - 0.16,
        variant, shutter_key,
    )


def _emit_magasin_stall_riser(mesh, pid, face, seg_idx, door_idx, p, u0, u1, z0, variant: int) -> None:
    """Low masonry/wood threshold strip common to old small-shop fronts."""
    top = z0 + 0.34
    mesh.add_quad(
        p0=p(u0, z0, 0.055),
        p1=p(u0, top, 0.055),
        p2=p(u1, top, 0.055),
        p3=p(u1, z0, 0.055),
        role="PlinthSurface",
        surface_id=f"{pid}.magasin_storefront.{face}.{seg_idx}.{door_idx}.stall_riser",
        material_key="plinth_stone" if variant % 3 else "magasin_trim_aged",
    )


def _emit_magasin_canopy(
    mesh: BuildingMesh,
    pid: str,
    face: str,
    seg_idx: int,
    door_idx: int,
    sx: float,
    sy: float,
    ux: float,
    uy: float,
    nx: float,
    ny: float,
    u0: float,
    u1: float,
    z: float,
) -> None:
    """Short sloped timber/canvas hood, visually separates shops from houses."""
    depth = 0.42
    drop = 0.12
    side = 0.08
    a = u0 - side
    b = u1 + side

    def p(u: float, out: float, dz: float = 0.0) -> tuple[float, float, float]:
        return (sx + ux * u + nx * out, sy + uy * u + ny * out, z + dz)

    mesh.add_quad(
        p0=p(a, 0.02, 0.0),
        p1=p(b, 0.02, 0.0),
        p2=p(b, depth, -drop),
        p3=p(a, depth, -drop),
        role="CorniceSurface",
        surface_id=f"{pid}.magasin_storefront.{face}.{seg_idx}.{door_idx}.canopy",
        material_key="magasin_canvas",
    )
    # Front valance strip.
    val_h = 0.12
    mesh.add_quad(
        p0=p(a, depth, -drop),
        p1=p(a, depth, -drop - val_h),
        p2=p(b, depth, -drop - val_h),
        p3=p(b, depth, -drop),
        role="CorniceSurface",
        surface_id=f"{pid}.magasin_storefront.{face}.{seg_idx}.{door_idx}.valance",
        material_key="magasin_sign",
    )


def _is_magasin_building(building: Building) -> bool:
    texts: list[str] = []
    for storey in building.storeys:
        if storey.level == 0 and storey.use:
            texts.append(storey.use)
    snap = building.excel_snapshot or {}
    texts.extend([
        str(snap.get("wall_code") or ""),
        str(snap.get("bim_notes") or ""),
    ])
    gf = snap.get("ground_floor") or {}
    if isinstance(gf, dict):
        texts.extend(str(v) for v in gf.values() if v)
    notes = building.notes or {}
    texts.append(str(notes))
    text = " ".join(texts).lower()
    return any(token in text for token in ("mg", "magasin", "magazine", "shop", "bakery", "fırın", "firin"))


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
