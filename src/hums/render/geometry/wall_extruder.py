"""PRD-003 · §6.1 — extrude WallSegments into wall + floor + ground surfaces.

Each segment becomes:
  * One outer WallSurface face (street side) or InteriorWallSurface (inside).
  * One GroundSurface shared quad contributed to the floor plate.
  * One FloorSurface per storey (internal slab top, visible in section).
Openings are NOT cut here — OpeningCutter consumes the emitted wall faces and
replaces them with sub-faces + Window/Door geometry.
"""
from __future__ import annotations

from ...common.prd import prd
from ...modeling.building import Building, WallSegment, Storey
from ..mesh_graph import BuildingMesh


@prd("003", "§6.1 WallExtruder")
class WallExtruder:
    def extrude(self, mesh: BuildingMesh, building: Building) -> None:
        non_basement = [s for s in building.storeys if not s.is_basement]
        if not non_basement:
            return

        # z offsets: stack storeys upward
        z_levels = [0.0]
        for s in non_basement:
            z_levels.append(z_levels[-1] + s.height_m)
        total_height = z_levels[-1]

        # Ground surface: fan-triangulate the footprint at z=0.
        self._emit_ground(mesh, building)

        # For each wall segment, emit outer face from z=0 to total_height.
        for idx, seg in enumerate(building.wall_segments):
            self._emit_wall_face(mesh, building, seg, idx, total_height)

        # FloorSurface planes at each intermediate storey top.
        self._emit_floor_slabs(mesh, building, z_levels, non_basement)

    def _emit_ground(self, mesh: BuildingMesh, building: Building) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        # Ground surface faces DOWN (CityGML convention). Reverse the ring so
        # the winding gives a -Z normal.
        indices = [mesh.add_vertex(x, y, 0.0) for (x, y) in reversed(ring)]
        mesh.add_face(
            indices,
            role="GroundSurface",
            surface_id=f"{building.parcel_id}.ground",
            material_key="wall_main",
            storey_level=0,
        )

    def _emit_wall_face(self, mesh, building, seg: WallSegment, idx: int, top_z: float) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        face_id = f"{building.parcel_id}.wall.{seg.face}.{idx}"
        role = "WallSurface" if seg.is_street_facing or seg.face != "INT" else "WallSurface"
        material = "wall_main"
        # Outer wall quad. Ring is CCW from above, so for the wall normal to
        # face OUTWARD we must wind bottom-start → top-start → top-end →
        # bottom-end (clockwise when viewed from outside). Right-hand rule
        # then gives an outward normal.
        mesh.add_quad(
            p0=(sx, sy, 0.0),
            p1=(sx, sy, top_z),
            p2=(ex, ey, top_z),
            p3=(ex, ey, 0.0),
            role=role,
            surface_id=face_id,
            material_key=material,
            storey_level=None,
        )

    def _emit_floor_slabs(self, mesh, building, z_levels, storeys: list[Storey]) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        # One FloorSurface per storey-top (excluding final roof level — that's roof).
        for i, z in enumerate(z_levels[1:-1], start=1):
            indices = [mesh.add_vertex(x, y, z) for (x, y) in ring]
            mesh.add_face(
                indices,
                role="FloorSurface",
                surface_id=f"{building.parcel_id}.floor.{i}",
                material_key="wall_accent",
                storey_level=i,
            )
