"""PRD-004 · Track B — plinth band + horizontal stringcourses.

Emits thin rectangular strips around the building at:
  * ground level (plinth: stone base, 0.5 m tall on class A/B masonry)
  * each storey floor height (stringcourse: 0.08 m projection, trim material)
Only on street-facing walls — interior walls stay plain.
"""
from __future__ import annotations
import math

from ...common.prd import prd
from ...modeling.building import Building, WallSegment
from ..mesh_graph import BuildingMesh

PLINTH_H = 0.50
PLINTH_DEPTH = 0.05       # outward thickness of the plinth lip
STRINGCOURSE_H = 0.08


@prd("004", "FacadeBanding")
class FacadeBanding:
    def emit(self, mesh: BuildingMesh, building: Building) -> None:
        if building.structure_type != "building":
            return
        pid = building.parcel_id
        cls = (building.material_class or "").upper()

        # Plinth — all masonry A/B get a stone base. Wooden C gets a subtler
        # dark plinth (painted).
        plinth_mat = "plinth_stone" if cls in ("A", "B") else "trim"
        for idx, seg in enumerate(building.wall_segments):
            if not seg.is_street_facing:
                continue
            self._emit_strip(
                mesh, seg, z0=0.0, z1=PLINTH_H,
                outward_depth=PLINTH_DEPTH,
                role="PlinthSurface",
                surface_id=f"{pid}.plinth.{seg.face}.{idx}",
                material_key=plinth_mat,
            )

        # Stringcourses — above each storey except the last.
        floor_zs = [0.0]
        for s in (building.storeys or []):
            if s.is_basement:
                continue
            floor_zs.append(floor_zs[-1] + s.height_m)
        for i, z in enumerate(floor_zs[1:-1], start=1):
            for idx, seg in enumerate(building.wall_segments):
                if not seg.is_street_facing:
                    continue
                self._emit_strip(
                    mesh, seg,
                    z0=z - STRINGCOURSE_H / 2,
                    z1=z + STRINGCOURSE_H / 2,
                    outward_depth=0.04,
                    role="StringcourseSurface",
                    surface_id=f"{pid}.stringcourse.{i}.{seg.face}.{idx}",
                    material_key="cornice_paint",
                )

    def _emit_strip(self, mesh: BuildingMesh, seg: WallSegment,
                    z0: float, z1: float, outward_depth: float,
                    role: str, surface_id: str, material_key: str) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        length = math.hypot(ex - sx, ey - sy)
        if length < 0.3 or z1 - z0 < 0.02:
            return
        ux = (ex - sx) / length
        uy = (ey - sy) / length
        # outward normal (ring CCW → right-hand of edge points inward; flip)
        nx, ny = uy, -ux
        nx, ny = -nx, -ny

        ox_s = sx + nx * outward_depth
        oy_s = sy + ny * outward_depth
        ox_e = ex + nx * outward_depth
        oy_e = ey + ny * outward_depth

        # outer face
        mesh.add_quad(
            p0=(ox_s, oy_s, z0), p1=(ox_s, oy_s, z1),
            p2=(ox_e, oy_e, z1), p3=(ox_e, oy_e, z0),
            role=role, surface_id=f"{surface_id}.outer", material_key=material_key,
        )
        # top face (cornice top)
        mesh.add_quad(
            p0=(sx, sy, z1), p1=(ex, ey, z1),
            p2=(ox_e, oy_e, z1), p3=(ox_s, oy_s, z1),
            role=role, surface_id=f"{surface_id}.top", material_key=material_key,
        )
        # bottom face (drip underside)
        mesh.add_quad(
            p0=(ox_s, oy_s, z0), p1=(ox_e, oy_e, z0),
            p2=(ex, ey, z0), p3=(sx, sy, z0),
            role=role, surface_id=f"{surface_id}.bot", material_key=material_key,
        )
