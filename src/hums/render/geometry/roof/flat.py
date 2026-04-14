"""PRD-003 · §6.2 — flat roof + parapet."""
from __future__ import annotations

from ....common.heritage_profile import PROFILE
from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from .base import RoofGenerator


@prd("003", "§6.2 FlatRoof")
class FlatRoof(RoofGenerator):
    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        parapet = PROFILE.storeys.parapet_m
        # Deck at eaves_z
        deck_idx = [mesh.add_vertex(x, y, eaves_z) for (x, y) in ring]
        mesh.add_face(
            deck_idx, role="RoofSurface",
            surface_id=f"{building.parcel_id}.roof.deck",
            material_key="roof",
        )
        # Parapet outer strip
        for i, (x, y) in enumerate(ring):
            nx, ny = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(x, y, eaves_z), p1=(nx, ny, eaves_z),
                p2=(nx, ny, eaves_z + parapet), p3=(x, y, eaves_z + parapet),
                role="WallSurface",
                surface_id=f"{building.parcel_id}.parapet.{i}",
                material_key="wall_main",
            )
