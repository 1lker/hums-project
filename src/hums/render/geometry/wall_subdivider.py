"""PRD-004 · Track B — real wall cutouts via rectangular strip subdivision.

For each WallSegment we split the wall into a grid of axis-aligned rectangles
in wall-local (u, z) space where u = distance along the wall. Openings carve
holes in that grid; the pieces around the hole emit wall quads, while the hole
itself gets an inset glazing pane + jamb/sill/head reveals (real depth).

This gives true "holes" through the wall without needing a CSG library.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from ...common.prd import prd
from ...modeling.building import Building, Opening, WallSegment
from ..mesh_graph import BuildingMesh


REVEAL_DEPTH = 0.15   # how far the glazing is recessed from the outer wall face
SILL_PROJECTION = 0.05   # sill protrudes slightly beyond the wall face
MIN_SLIVER = 0.05        # drop slivers narrower than this
ARCH_RISE_FRACTION = 0.35   # arch height = width * this (segmental arch)
ARCH_SEGMENTS = 7           # triangle count for each arch


@dataclass
class _Rect:
    u0: float
    u1: float
    z0: float
    z1: float

    def valid(self) -> bool:
        return (self.u1 - self.u0) > MIN_SLIVER and (self.z1 - self.z0) > MIN_SLIVER


@prd("004", "Track B WallSubdivider")
class WallSubdivider:
    def emit(self, mesh: BuildingMesh, building: Building, storey_heights: list[float]) -> None:
        """Replace monolithic wall faces with subdivided wall + real cutouts."""
        for idx, seg in enumerate(building.wall_segments):
            self._emit_segment(mesh, building, seg, idx, storey_heights)

    # -- per-segment -----------------------------------------------------------
    def _emit_segment(self, mesh, building, seg: WallSegment, idx: int, storey_heights: list[float]) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        length = math.hypot(ex - sx, ey - sy)
        if length < 0.3:
            return

        # direction + outward normal (ring is CCW → right-hand normal points outward from above).
        ux = (ex - sx) / length
        uy = (ey - sy) / length
        nx = uy     # right-hand normal of edge direction, for CCW outer ring = inward.
        ny = -ux
        # we need OUTWARD normal → flip
        nx = -nx
        ny = -ny

        total_height = sum(storey_heights)

        # Collect openings with (u0, z0, u1, z1) in wall-local coords.
        holes: list[tuple[float, float, float, float, Opening]] = []
        z_floors = _storey_floor_zs(storey_heights)
        for op in seg.openings:
            u0 = max(0.0, op.position_along_wall_m)
            u1 = min(length, u0 + op.width_m)
            z0 = z_floors[op.storey_level] + op.sill_m
            z1 = z0 + op.height_m
            if u1 - u0 > MIN_SLIVER and z1 - z0 > MIN_SLIVER:
                holes.append((u0, z0, u1, z1, op))
        holes.sort(key=lambda h: (h[1], h[0]))  # by z, then u

        pid = building.parcel_id
        face_id_prefix = f"{pid}.wall.{seg.face}.{idx}"
        wall_mat = _wall_material(building)

        # Subdivide the wall rectangle [0,length] × [0,total_height] minus holes.
        rects = _subtract_holes_axis(length, total_height, [(h[0], h[1], h[2], h[3]) for h in holes])
        for j, rect in enumerate(rects):
            self._emit_wall_rect(mesh, face_id_prefix, sx, sy, ux, uy, 0.0, rect, j, wall_mat)

        # Now emit reveals + glazing per hole.
        for k, (u0, z0, u1, z1, op) in enumerate(holes):
            self._emit_opening(mesh, building, face_id_prefix, sx, sy, ux, uy, nx, ny, u0, z0, u1, z1, op, k, wall_mat)

    # -- wall rect ------------------------------------------------------------
    def _emit_wall_rect(self, mesh, prefix, sx, sy, ux, uy, n_off, rect: _Rect, j: int, wall_mat: str) -> None:
        if not rect.valid():
            return
        p_bl = (sx + ux * rect.u0, sy + uy * rect.u0, rect.z0)
        p_br = (sx + ux * rect.u1, sy + uy * rect.u1, rect.z0)
        p_tr = (sx + ux * rect.u1, sy + uy * rect.u1, rect.z1)
        p_tl = (sx + ux * rect.u0, sy + uy * rect.u0, rect.z1)
        # winding: bottom-left → top-left → top-right → bottom-right (outward normal)
        mesh.add_quad(
            p0=p_bl, p1=p_tl, p2=p_tr, p3=p_br,
            role="WallSurface",
            surface_id=f"{prefix}.piece.{j}",
            material_key=wall_mat,
        )

    # -- opening --------------------------------------------------------------
    def _emit_opening(self, mesh, building, prefix, sx, sy, ux, uy, nx, ny,
                      u0: float, z0: float, u1: float, z1: float, op: Opening, k: int,
                      wall_mat: str) -> None:
        pid = building.parcel_id
        # outward points (wall face, z is already known)
        def P(u, z, inset=0.0):
            return (sx + ux * u + nx * inset, sy + uy * u + ny * inset, z)

        role = "Door" if op.kind == "door" else "Window"
        glass_mat = "door_panel" if op.kind == "door" else "window_glass"
        reveal_mat = "trim"

        # outer corners on the wall plane
        out_bl = P(u0, z0)
        out_br = P(u1, z0)
        out_tr = P(u1, z1)
        out_tl = P(u0, z1)
        # inner corners on the recessed glazing plane
        in_bl = P(u0, z0, -REVEAL_DEPTH)
        in_br = P(u1, z0, -REVEAL_DEPTH)
        in_tr = P(u1, z1, -REVEAL_DEPTH)
        in_tl = P(u0, z1, -REVEAL_DEPTH)

        # jamb: left + right side reveals (facing into the hole)
        mesh.add_quad(p0=in_bl, p1=in_tl, p2=out_tl, p3=out_bl,
                      role="JambSurface", surface_id=f"{prefix}.{op.kind}.{k}.jamb.L",
                      material_key=reveal_mat)
        mesh.add_quad(p0=out_br, p1=out_tr, p2=in_tr, p3=in_br,
                      role="JambSurface", surface_id=f"{prefix}.{op.kind}.{k}.jamb.R",
                      material_key=reveal_mat)
        # head (top reveal, normal down)
        mesh.add_quad(p0=in_tl, p1=in_tr, p2=out_tr, p3=out_tl,
                      role="HeaderSurface", surface_id=f"{prefix}.{op.kind}.{k}.head",
                      material_key=reveal_mat)
        # sill (bottom reveal, normal up) — include a small projection beyond the wall face for drip
        proj_bl = P(u0, z0, +SILL_PROJECTION)
        proj_br = P(u1, z0, +SILL_PROJECTION)
        mesh.add_quad(p0=in_bl, p1=in_br, p2=proj_br, p3=proj_bl,
                      role="SillSurface", surface_id=f"{prefix}.{op.kind}.{k}.sill",
                      material_key=reveal_mat)

        # glazing plane (inset)
        mesh.add_quad(p0=in_bl, p1=in_tl, p2=in_tr, p3=in_br,
                      role=role, surface_id=f"{prefix}.{op.kind}.{k}.glass",
                      material_key=glass_mat, storey_level=op.storey_level)

        # Arches are only emitted when the data/model explicitly marks the
        # opening as arched. Pervititch parcel maps do not show window shapes.
        if op.kind == "window" and op.style == "arched" and op.storey_level is not None and op.storey_level >= 1:
            arch_rise = (u1 - u0) * ARCH_RISE_FRACTION
            arch_apex_z = z1 + arch_rise
            # Apex vertex on the glazing plane
            mid_u = (u0 + u1) / 2
            apex_in = P(mid_u, arch_apex_z, -REVEAL_DEPTH)
            apex_out = P(mid_u, arch_apex_z)
            # Fan triangles on glazing plane + reveal underside + outer header
            # Split the arch into segments for a smooth curve on the inside.
            for s in range(ARCH_SEGMENTS):
                t0 = s / ARCH_SEGMENTS
                t1 = (s + 1) / ARCH_SEGMENTS
                u_a = u0 + (u1 - u0) * t0
                u_b = u0 + (u1 - u0) * t1
                # parametric arch: z(t) = z1 + arch_rise * sin(pi*t)
                z_a = z1 + arch_rise * math.sin(math.pi * t0)
                z_b = z1 + arch_rise * math.sin(math.pi * t1)
                # outer wall surround (fills between rectangular top and arch)
                mesh.add_quad(
                    p0=P(u_a, z1),
                    p1=P(u_a, z_a),
                    p2=P(u_b, z_b),
                    p3=P(u_b, z1),
                    role="WallSurface",
                    surface_id=f"{prefix}.{op.kind}.{k}.arch_wall.{s}",
                    material_key=wall_mat,
                )
                # inner arch glass panel
                mesh.add_quad(
                    p0=P(u_a, z1, -REVEAL_DEPTH),
                    p1=P(u_a, z_a, -REVEAL_DEPTH),
                    p2=P(u_b, z_b, -REVEAL_DEPTH),
                    p3=P(u_b, z1, -REVEAL_DEPTH),
                    role="Window",
                    surface_id=f"{prefix}.{op.kind}.{k}.arch_glass.{s}",
                    material_key=glass_mat,
                )

        # mullions on wide panes (≥1 m) — vertical trim, thin quad on the glazing plane
        if op.kind != "door" and (u1 - u0) >= 1.0:
            mid = (u0 + u1) / 2.0
            mull_half_w = 0.03
            mesh.add_quad(
                p0=P(mid - mull_half_w, z0, -REVEAL_DEPTH + 0.001),
                p1=P(mid - mull_half_w, z1, -REVEAL_DEPTH + 0.001),
                p2=P(mid + mull_half_w, z1, -REVEAL_DEPTH + 0.001),
                p3=P(mid + mull_half_w, z0, -REVEAL_DEPTH + 0.001),
                role="Mullion", surface_id=f"{prefix}.{op.kind}.{k}.mullion.V",
                material_key=reveal_mat,
            )
        if op.kind != "door" and (z1 - z0) >= 1.2:
            mid_z = (z0 + z1) / 2.0
            mull_half = 0.03
            mesh.add_quad(
                p0=P(u0, mid_z - mull_half, -REVEAL_DEPTH + 0.001),
                p1=P(u0, mid_z + mull_half, -REVEAL_DEPTH + 0.001),
                p2=P(u1, mid_z + mull_half, -REVEAL_DEPTH + 0.001),
                p3=P(u1, mid_z - mull_half, -REVEAL_DEPTH + 0.001),
                role="Mullion", surface_id=f"{prefix}.{op.kind}.{k}.mullion.H",
                material_key=reveal_mat,
            )


# -- helpers -------------------------------------------------------------------

def _storey_floor_zs(heights: list[float]) -> list[float]:
    out = [0.0]
    for h in heights[:-1]:
        out.append(out[-1] + h)
    return out


def _wall_material(building: Building) -> str:
    cls = (building.material_class or "").lower()
    notes = " ".join(str(v) for v in (building.notes or {}).values()).lower()
    snapshot = building.excel_snapshot or {}
    source = " ".join(str(v) for v in (
        cls,
        notes,
        snapshot.get("bim_notes"),
        ((snapshot.get("material") or {}).get("raw_material_label") if isinstance(snapshot.get("material"), dict) else None),
        ((snapshot.get("material") or {}).get("decoded") if isinstance(snapshot.get("material"), dict) else None),
        snapshot.get("vault_code"),
    ) if v is not None).lower()
    roof_mat = ((building.roof.material if building.roof else "") or "").lower()
    if any(token in source for token in ("not glass", "not a glass", "opaque", "not all-glass")):
        return "wall_main"
    if "glass" in cls or roof_mat == "glass_roof":
        return "window_glass"
    if "glazed" in source or "camlı" in source or "camli" in source or "vitre" in source:
        return "window_glass"
    return "wall_main"


def _subtract_holes_axis(width: float, height: float,
                         holes: list[tuple[float, float, float, float]]) -> list[_Rect]:
    """Split [0,width] x [0,height] into axis-aligned rectangles avoiding holes.

    Strategy: build the unique u-lines and z-lines from hole edges + outer
    bounds, iterate cells, and keep cells that don't lie inside any hole.
    """
    u_lines = sorted({0.0, width} | {h[0] for h in holes} | {h[2] for h in holes})
    z_lines = sorted({0.0, height} | {h[1] for h in holes} | {h[3] for h in holes})

    rects: list[_Rect] = []
    for i in range(len(u_lines) - 1):
        for j in range(len(z_lines) - 1):
            u0, u1 = u_lines[i], u_lines[i + 1]
            z0, z1 = z_lines[j], z_lines[j + 1]
            uc = (u0 + u1) / 2
            zc = (z0 + z1) / 2
            inside_hole = any(h[0] < uc < h[2] and h[1] < zc < h[3] for h in holes)
            if not inside_hole:
                rects.append(_Rect(u0, u1, z0, z1))
    # merge horizontally-adjacent rectangles that share z bounds and neither
    # neighbours a hole — cheap pass, keeps face count reasonable.
    return _merge_horizontal(rects)


def _merge_horizontal(rects: list[_Rect]) -> list[_Rect]:
    out: list[_Rect] = []
    # group by (z0, z1)
    buckets: dict[tuple[float, float], list[_Rect]] = {}
    for r in rects:
        buckets.setdefault((r.z0, r.z1), []).append(r)
    for key, group in buckets.items():
        group.sort(key=lambda r: r.u0)
        merged = [group[0]]
        for r in group[1:]:
            if abs(merged[-1].u1 - r.u0) < 1e-4:
                merged[-1] = _Rect(merged[-1].u0, r.u1, merged[-1].z0, merged[-1].z1)
            else:
                merged.append(r)
        out.extend(merged)
    return out
