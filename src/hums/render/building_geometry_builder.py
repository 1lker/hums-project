"""PRD-003 · §6 — assemble a BuildingMesh from a Building.

Composes: ground, walls, openings, roof, plus structure-specific extras
(chimneys, skylights, monument body). Pure-Python — no backend imports.
"""
from __future__ import annotations

from ..common.prd import prd
from ..modeling.building import Building
from .geometry.opening_cutter import OpeningCutter
from .geometry.roof import for_shape as roof_for_shape
from .geometry.roof.base import RoofGenerator
from .geometry.wall_extruder import WallExtruder
from .mesh_graph import BuildingMesh


@prd("003", "§6 BuildingGeometryBuilder")
class BuildingGeometryBuilder:
    def __init__(self) -> None:
        self._wall_extruder = WallExtruder()
        self._opening_cutter = OpeningCutter()

    def build(self, building: Building) -> BuildingMesh | None:
        if not building.footprint_local or not building.local_frame:
            return None

        mesh = BuildingMesh(
            parcel_id=building.parcel_id,
            placement_origin_utm=building.local_frame.origin_utm,
            placement_rotation_deg=building.local_frame.street_rotation_deg,
            palette=building.facade_palette,
            metadata={
                "material_class": building.material_class,
                "structure_type": building.structure_type,
                "footprint_source": building.footprint_source,
                "notes": building.notes,
                "shared_footprint_group_id": building.shared_footprint_group_id,
            },
        )

        if building.structure_type == "fountain":
            self._build_monument(mesh, building)
            return mesh

        self._wall_extruder.extrude(mesh, building)
        self._opening_cutter.cut(mesh, building)
        self._add_roof(mesh, building)
        self._add_roof_extras(mesh, building)
        return mesh

    def _add_roof(self, mesh: BuildingMesh, building: Building) -> None:
        generator: RoofGenerator = roof_for_shape(
            building.roof.shape if building.roof else "gable"
        )
        eaves_z = RoofGenerator.total_wall_height(building)
        generator.generate(mesh, building, eaves_z)

    def _add_roof_extras(self, mesh: BuildingMesh, building: Building) -> None:
        if not building.roof:
            return
        eaves_z = RoofGenerator.total_wall_height(building)
        if building.roof.has_chimney:
            self._add_chimney(mesh, building, eaves_z)
        if building.roof.has_skylight:
            self._add_skylight(mesh, building, eaves_z)

    def _add_chimney(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        # Simple square chimney 0.4×0.4×1.8 at footprint centroid.
        ring = building.footprint_local
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        half = 0.2
        h = 1.8
        top = eaves_z + h
        corners = [
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        ]
        # 4 sides + top
        for i in range(4):
            a = corners[i]; b = corners[(i + 1) % 4]
            mesh.add_quad(
                p0=(a[0], a[1], eaves_z), p1=(b[0], b[1], eaves_z),
                p2=(b[0], b[1], top), p3=(a[0], a[1], top),
                role="Chimney",
                surface_id=f"{building.parcel_id}.chimney.side.{i}",
                material_key="chimney_brick",
            )
        top_idx = [mesh.add_vertex(x, y, top) for (x, y) in corners]
        mesh.add_face(top_idx, role="Chimney",
                      surface_id=f"{building.parcel_id}.chimney.top",
                      material_key="chimney_brick")

    def _add_skylight(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        half_w, half_d = 0.6, 0.4
        z = eaves_z + 0.3
        mesh.add_quad(
            p0=(cx - half_w, cy - half_d, z),
            p1=(cx + half_w, cy - half_d, z),
            p2=(cx + half_w, cy + half_d, z),
            p3=(cx - half_w, cy + half_d, z),
            role="Skylight",
            surface_id=f"{building.parcel_id}.skylight",
            material_key="window_glass",
        )

    def _build_monument(self, mesh: BuildingMesh, building: Building) -> None:
        """Çeşme / fountain: single solid body extruded to the body storey height."""
        ring = building.footprint_local
        if not ring:
            return
        height = building.storeys[0].height_m if building.storeys else 1.8
        # Ground
        base_idx = [mesh.add_vertex(x, y, 0.0) for (x, y) in ring]
        mesh.add_face(base_idx, role="GroundSurface",
                      surface_id=f"{building.parcel_id}.ground",
                      material_key="monument_stone")
        # Side faces
        for i, (x, y) in enumerate(ring):
            nx, ny = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(x, y, 0.0), p1=(nx, ny, 0.0),
                p2=(nx, ny, height), p3=(x, y, height),
                role="MonumentBody",
                surface_id=f"{building.parcel_id}.monument.{i}",
                material_key="monument_stone",
            )
        # Top cap
        top_idx = [mesh.add_vertex(x, y, height) for (x, y) in ring]
        mesh.add_face(top_idx, role="RoofSurface",
                      surface_id=f"{building.parcel_id}.monument.cap",
                      material_key="monument_stone")
