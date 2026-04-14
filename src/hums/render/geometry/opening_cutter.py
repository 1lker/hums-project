"""PRD-003 · §6.1 — punch openings into the already-emitted wall faces.

Design trade-off: a full boolean cutter would be complex. For LOD3 at block
scale, emit the **glazing plane inset by 0.05 m** per opening, plus a
rectangular *frame ring* when frame_profile == 'moulded'. We leave the wall
face uncut (it becomes the "backdrop" visible through the window). This is
visually indistinguishable at render distances beyond 5 m and keeps the mesh
graph tractable. A higher-fidelity CSG pass can be added in PRD-005.
"""
from __future__ import annotations
import math

from ...common.prd import prd
from ...modeling.building import Building, Opening, WallSegment
from ..mesh_graph import BuildingMesh


@prd("003", "§6.1 OpeningCutter")
class OpeningCutter:
    INSET = 0.05          # glazing plane inset from wall outer face
    FRAME_DEPTH = 0.06
    FRAME_WIDTH = 0.08

    def cut(self, mesh: BuildingMesh, building: Building) -> None:
        for w_idx, seg in enumerate(building.wall_segments):
            # need a z0 baseline for each opening at its storey
            z_at_storey = _storey_floor_z(building)
            for o_idx, opening in enumerate(seg.openings):
                self._emit_opening(
                    mesh, building, seg, opening,
                    z_floor=z_at_storey.get(opening.storey_level, 0.0),
                    wall_idx=w_idx, opening_idx=o_idx,
                )

    def _emit_opening(self, mesh, building, seg: WallSegment, op: Opening,
                      z_floor: float, wall_idx: int, opening_idx: int) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        length = math.hypot(ex - sx, ey - sy)
        if length < 0.5 or op.width_m <= 0:
            return

        # unit vector along wall + inward normal (toward building interior)
        ux = (ex - sx) / length
        uy = (ey - sy) / length
        # left-hand normal of CCW ring points inward
        nx = -uy
        ny = ux

        # opening corners in local plane
        t0 = op.position_along_wall_m
        t1 = min(length, t0 + op.width_m)
        z0 = z_floor + op.sill_m
        z1 = z0 + op.height_m

        # pull glazing inward by INSET
        ax = sx + ux * t0 + nx * self.INSET
        ay = sy + uy * t0 + ny * self.INSET
        bx = sx + ux * t1 + nx * self.INSET
        by = sy + uy * t1 + ny * self.INSET

        role = "Door" if op.kind == "door" else "Window"
        material = "door_panel" if op.kind == "door" else "window_glass"
        face_id = f"{building.parcel_id}.{op.kind}.{seg.face}.{wall_idx}.{opening_idx}"

        mesh.add_quad(
            p0=(ax, ay, z0),
            p1=(bx, by, z0),
            p2=(bx, by, z1),
            p3=(ax, ay, z1),
            role=role,
            surface_id=face_id,
            material_key=material,
            storey_level=op.storey_level,
        )

        if op.frame_profile == "moulded":
            self._emit_frame_ring(
                mesh, building.parcel_id,
                p_ll=(ax, ay, z0), p_lr=(bx, by, z0),
                p_ur=(bx, by, z1), p_ul=(ax, ay, z1),
                seg_face=seg.face, kind=op.kind,
                wall_idx=wall_idx, opening_idx=opening_idx,
            )

    def _emit_frame_ring(self, mesh, parcel_id, p_ll, p_lr, p_ur, p_ul,
                         seg_face: str, kind: str, wall_idx: int, opening_idx: int) -> None:
        w = self.FRAME_WIDTH
        # Thin quads approximating a frame around the opening. Each quad lies
        # in the same glazing plane, offset outward by ``w`` from the glazing edge.
        def shifted(p, dx, dy, dz):
            return (p[0] + dx, p[1] + dy, p[2] + dz)

        fid = f"{parcel_id}.{kind}_frame.{seg_face}.{wall_idx}.{opening_idx}"
        # top frame
        mesh.add_quad(
            p0=p_ul, p1=p_ur,
            p2=shifted(p_ur, 0, 0, w), p3=shifted(p_ul, 0, 0, w),
            role="Window" if kind != "door" else "Door",
            surface_id=f"{fid}.top", material_key="trim",
        )
        # bottom frame
        mesh.add_quad(
            p0=shifted(p_ll, 0, 0, -w), p1=shifted(p_lr, 0, 0, -w),
            p2=p_lr, p3=p_ll,
            role="Window" if kind != "door" else "Door",
            surface_id=f"{fid}.bot", material_key="trim",
        )


def _storey_floor_z(building: Building) -> dict[int, float]:
    """Return z-coordinate of each storey's floor level."""
    z = 0.0
    out: dict[int, float] = {}
    for s in building.storeys:
        if s.is_basement:
            continue
        out[s.level] = z
        z += s.height_m
    return out
