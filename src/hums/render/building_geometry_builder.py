"""PRD-003 · §6 — assemble a BuildingMesh from a Building.

Composes: ground, walls, openings, roof, plus structure-specific extras
(chimneys, skylights, monument body). Pure-Python — no backend imports.
"""
from __future__ import annotations

from ..common.prd import prd
from ..modeling.building import Building
from .geometry.facade_banding import FacadeBanding
from .geometry.period_detail import PeriodDetail
from .geometry.roof import for_shape as roof_for_shape
from .geometry.roof.base import RoofGenerator
from .geometry.roof.overhang import RoofOverhang
from .geometry.shutters_balconies import ShuttersAndBalconies
from .geometry.wall_extruder import WallExtruder
from .geometry.wall_subdivider import WallSubdivider
from .mesh_graph import BuildingMesh


@prd("003", "§6 BuildingGeometryBuilder")
class BuildingGeometryBuilder:
    def __init__(self) -> None:
        self._wall_extruder = WallExtruder()
        self._wall_subdivider = WallSubdivider()
        self._roof_overhang = RoofOverhang()
        self._facade_banding = FacadeBanding()
        self._shutters_balconies = ShuttersAndBalconies()
        self._period_detail = PeriodDetail()

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
                "roof_shape": building.roof.shape if building.roof else None,
                "roof_material": building.roof.material if building.roof else None,
                "roof_pitch_deg": building.roof.pitch_deg if building.roof else None,
                "source_footprint_file": building.provenance.footprint_source_file,
            },
        )

        if building.structure_type == "fountain":
            self._build_monument(mesh, building)
            return mesh

        # Floors + ground slab (walls are emitted by the subdivider so the
        # extruder now only adds floors + ground; skip its wall-face emission).
        self._wall_extruder.extrude_slabs_only(mesh, building)

        # Walls with real punched openings.
        storey_heights = [s.height_m for s in building.storeys if not s.is_basement]
        self._wall_subdivider.emit(mesh, building, storey_heights)

        self._facade_banding.emit(mesh, building)
        self._shutters_balconies.emit(mesh, building)
        self._period_detail.emit(mesh, building, RoofGenerator.total_wall_height(building))

        eaves_z = RoofGenerator.total_wall_height(building)

        self._add_roof(mesh, building)
        self._add_roof_extras(mesh, building)
        return mesh

    def _emit_eaves_cap(self, mesh: BuildingMesh, building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        # Normal +Z (CCW from above preserves that since footprint_local is CCW).
        idx = [mesh.add_vertex(x, y, eaves_z) for (x, y) in ring]
        mesh.add_face(
            idx,
            role="RoofSurface",
            surface_id=f"{building.parcel_id}.eaves_cap",
            material_key=RoofGenerator.material_key(building),
        )

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
        """Brick shaft with a projecting stone cap (period-correct detail)."""
        ring = building.footprint_local
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        half = 0.22
        h = 2.2
        top = eaves_z + h
        corners = [
            (cx - half, cy - half), (cx + half, cy - half),
            (cx + half, cy + half), (cx - half, cy + half),
        ]
        for i in range(4):
            a = corners[i]; b = corners[(i + 1) % 4]
            mesh.add_quad(
                p0=(a[0], a[1], eaves_z), p1=(a[0], a[1], top),
                p2=(b[0], b[1], top), p3=(b[0], b[1], eaves_z),
                role="Chimney",
                surface_id=f"{building.parcel_id}.chimney.side.{i}",
                material_key="chimney_brick",
            )
        # projecting cap (wider than the shaft, 0.12 m tall)
        cap_half = half + 0.08
        cap_top = top + 0.14
        cap_corners = [
            (cx - cap_half, cy - cap_half), (cx + cap_half, cy - cap_half),
            (cx + cap_half, cy + cap_half), (cx - cap_half, cy + cap_half),
        ]
        for i in range(4):
            a = cap_corners[i]; b = cap_corners[(i + 1) % 4]
            mesh.add_quad(
                p0=(a[0], a[1], top), p1=(a[0], a[1], cap_top),
                p2=(b[0], b[1], cap_top), p3=(b[0], b[1], top),
                role="Chimney",
                surface_id=f"{building.parcel_id}.chimney.cap.side.{i}",
                material_key="plinth_stone",
            )
        top_idx = [mesh.add_vertex(x, y, cap_top) for (x, y) in cap_corners]
        mesh.add_face(top_idx, role="Chimney",
                      surface_id=f"{building.parcel_id}.chimney.cap.top",
                      material_key="plinth_stone")

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
