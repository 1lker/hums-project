"""PRD-004 · Track B — roof overhang (eaves) + soffit + cornice band.

Emits an apron of geometry along each street-facing wall at eaves height:
  • a horizontal cornice strip (painted trim) 0.15 m tall against the wall,
  • a soffit strip (downward-facing) 0.4 m out from the wall,
  • a fascia strip at the outer eaves edge,
  • and extends the existing roof plane outward by OVERHANG metres.

Lightweight enough to run on every traced building; fountains are skipped.
"""
from __future__ import annotations
import math

from ....common.prd import prd

from ....modeling.building import Building, WallSegment
from ...mesh_graph import BuildingMesh

OVERHANG = 0.4
CORNICE_H = 0.15
FASCIA_H = 0.18


@prd("004", "roof_overhang")
class RoofOverhang:
    def emit(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        if building.structure_type != "building":
            return
        for idx, seg in enumerate(building.wall_segments):
            if not seg.is_street_facing:
                continue
            self._emit_segment_apron(mesh, building, seg, idx, eaves_z)

    def _emit_segment_apron(self, mesh, building, seg: WallSegment, idx: int, eaves_z: float) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        length = math.hypot(ex - sx, ey - sy)
        if length < 0.5:
            return
        ux = (ex - sx) / length
        uy = (ey - sy) / length
        # outward normal
        nx = -uy
        ny = ux
        # For CCW polygon, right-hand normal of edge is inward → flip
        nx = -nx
        ny = -ny

        pid = building.parcel_id

        # Cornice band: flat vertical strip on the wall, from (eaves_z - cornice_h) to eaves_z
        z_top = eaves_z
        z_bot = eaves_z - CORNICE_H
        mesh.add_quad(
            p0=(sx, sy, z_bot),
            p1=(sx, sy, z_top),
            p2=(ex, ey, z_top),
            p3=(ex, ey, z_bot),
            role="CorniceSurface",
            surface_id=f"{pid}.cornice.{seg.face}.{idx}",
            material_key="cornice_paint",
        )

        # Soffit (underside of overhang). Wound so the normal faces DOWN
        # (p0 wall-start → p1 outer-start → p2 outer-end → p3 wall-end is
        # clockwise when viewed from above → right-hand normal points -Z).
        ox_s = sx + nx * OVERHANG
        oy_s = sy + ny * OVERHANG
        ox_e = ex + nx * OVERHANG
        oy_e = ey + ny * OVERHANG
        mesh.add_quad(
            p0=(sx, sy, z_top),
            p1=(ox_s, oy_s, z_top),
            p2=(ox_e, oy_e, z_top),
            p3=(ex, ey, z_top),
            role="SoffitSurface",
            surface_id=f"{pid}.soffit.{seg.face}.{idx}",
            material_key="cornice_paint",
        )

        # Fascia: outer vertical edge of the overhang, above the eaves
        z_fascia_top = z_top + FASCIA_H
        mesh.add_quad(
            p0=(ox_s, oy_s, z_top),
            p1=(ox_e, oy_e, z_top),
            p2=(ox_e, oy_e, z_fascia_top),
            p3=(ox_s, oy_s, z_fascia_top),
            role="CorniceSurface",
            surface_id=f"{pid}.fascia.{seg.face}.{idx}",
            material_key="trim",
        )
