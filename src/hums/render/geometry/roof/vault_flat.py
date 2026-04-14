"""PRD-003 · §6.2 — near-flat vault roof (VF/VT).

For LOD3 exterior we model VF/VT as a shallow sloped deck (~2.86°). Interior
vault ceiling geometry is deferred to PRD-005.
"""
from __future__ import annotations
import math

from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from .base import RoofGenerator


@prd("003", "§6.2 VaultFlatRoof")
class VaultFlatRoof(RoofGenerator):
    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        pitch_rad = math.radians(building.roof.pitch_deg if building.roof else 2.86)

        # Project onto first-edge axis to establish slope direction.
        ax, ay = ring[0]
        bx, by = ring[1]
        dx = bx - ax
        dy = by - ay
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length

        t_values = [(x - ax) * ux + (y - ay) * uy for (x, y) in ring]
        t_min = min(t_values)
        t_max = max(t_values)
        span = t_max - t_min
        rise = span * math.tan(pitch_rad)

        def z_at(t: float) -> float:
            return eaves_z + ((t - t_min) / max(span, 0.001)) * rise

        indices = [mesh.add_vertex(x, y, z_at(t)) for (x, y), t in zip(ring, t_values)]
        mesh.add_face(
            indices, role="RoofSurface",
            surface_id=f"{building.parcel_id}.roof.vault_flat",
            material_key="roof",
        )
