"""PRD-004 · Track B — shutters flanking windows + balcony slabs.

Drives off ``Opening.has_shutters`` / ``Opening.has_balcony`` set during
PRD-002 (opening_placer). Emits simple but readable geometry.
"""
from __future__ import annotations
import math

from ...common.prd import prd
from ...modeling.building import Building, Opening, WallSegment
from ..mesh_graph import BuildingMesh


SHUTTER_WIDTH = 0.35
SHUTTER_DEPTH = 0.04
BALCONY_PROJECT = 0.7
BALCONY_SLAB_THICKNESS = 0.10
RAILING_HEIGHT = 0.95


@prd("004", "ShuttersBalconies")
class ShuttersAndBalconies:
    def emit(self, mesh: BuildingMesh, building: Building) -> None:
        if building.structure_type != "building":
            return
        storey_heights = [s.height_m for s in building.storeys if not s.is_basement]
        floor_zs = _floor_zs(storey_heights)
        pid = building.parcel_id
        for idx, seg in enumerate(building.wall_segments):
            if not _is_strict_street(seg):
                continue
            for k, op in enumerate(seg.openings):
                z0 = floor_zs.get(op.storey_level, 0.0) + op.sill_m
                z1 = z0 + op.height_m
                if op.has_shutters:
                    self._emit_shutters(mesh, pid, seg, idx, op, k, z0, z1)
                if op.has_balcony:
                    self._emit_balcony(mesh, pid, seg, idx, op, k, floor_zs.get(op.storey_level, 0.0))

    def _emit_shutters(self, mesh: BuildingMesh, pid: str, seg: WallSegment,
                        idx: int, op: Opening, k: int, z0: float, z1: float) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        length = math.hypot(ex - sx, ey - sy)
        if length < 0.3:
            return
        ux = (ex - sx) / length
        uy = (ey - sy) / length
        nx, ny = uy, -ux
        nx, ny = -nx, -ny
        proj = 0.02

        def P(u, z, off=0.0):
            return (sx + ux * u + nx * off, sy + uy * u + ny * off, z)

        # left shutter
        u0 = op.position_along_wall_m - SHUTTER_WIDTH - 0.02
        u1 = op.position_along_wall_m - 0.02
        if u0 >= 0:
            mesh.add_quad(
                p0=P(u0, z0, proj), p1=P(u0, z1, proj),
                p2=P(u1, z1, proj), p3=P(u1, z0, proj),
                role="Shutter",
                surface_id=f"{pid}.shutter.L.{seg.face}.{idx}.{k}",
                material_key="shutters",
            )
        # right shutter
        u2 = op.position_along_wall_m + op.width_m + 0.02
        u3 = u2 + SHUTTER_WIDTH
        if u3 <= length:
            mesh.add_quad(
                p0=P(u2, z0, proj), p1=P(u2, z1, proj),
                p2=P(u3, z1, proj), p3=P(u3, z0, proj),
                role="Shutter",
                surface_id=f"{pid}.shutter.R.{seg.face}.{idx}.{k}",
                material_key="shutters",
            )

    def _emit_balcony(self, mesh: BuildingMesh, pid: str, seg: WallSegment,
                       idx: int, op: Opening, k: int, floor_z: float) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        length = math.hypot(ex - sx, ey - sy)
        if length < 0.3:
            return
        ux = (ex - sx) / length
        uy = (ey - sy) / length
        nx, ny = uy, -ux
        nx, ny = -nx, -ny

        u0 = max(0.0, op.position_along_wall_m - 0.2)
        u1 = min(length, op.position_along_wall_m + op.width_m + 0.2)

        def Q(u, off, z):
            return (sx + ux * u + nx * off, sy + uy * u + ny * off, z)

        z_top = floor_z + BALCONY_SLAB_THICKNESS
        # slab top
        mesh.add_quad(
            p0=Q(u0, 0, z_top), p1=Q(u0, BALCONY_PROJECT, z_top),
            p2=Q(u1, BALCONY_PROJECT, z_top), p3=Q(u1, 0, z_top),
            role="Balcony",
            surface_id=f"{pid}.balcony.top.{seg.face}.{idx}.{k}",
            material_key="plinth_stone",
        )
        # slab front edge
        mesh.add_quad(
            p0=Q(u0, BALCONY_PROJECT, floor_z), p1=Q(u0, BALCONY_PROJECT, z_top),
            p2=Q(u1, BALCONY_PROJECT, z_top), p3=Q(u1, BALCONY_PROJECT, floor_z),
            role="Balcony",
            surface_id=f"{pid}.balcony.front.{seg.face}.{idx}.{k}",
            material_key="plinth_stone",
        )
        # railing: single thin "bar" strip
        railing_bot = z_top + 0.05
        railing_top = z_top + RAILING_HEIGHT
        mesh.add_quad(
            p0=Q(u0, BALCONY_PROJECT - 0.02, railing_bot),
            p1=Q(u0, BALCONY_PROJECT - 0.02, railing_top),
            p2=Q(u1, BALCONY_PROJECT - 0.02, railing_top),
            p3=Q(u1, BALCONY_PROJECT - 0.02, railing_bot),
            role="Balcony",
            surface_id=f"{pid}.balcony.railing.{seg.face}.{idx}.{k}",
            material_key="balcony_iron",
        )


def _floor_zs(heights: list[float]) -> dict[int, float]:
    out: dict[int, float] = {}
    z = 0.0
    for lvl, h in enumerate(heights):
        out[lvl] = z
        z += h
    return out


def _is_strict_street(seg: WallSegment) -> bool:
    return seg.hatch_pattern == "_street"
