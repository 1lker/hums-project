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
        roof_mat = self.material_key(building)

        # Use the longest edge as the vault barrel direction and arch across
        # the short span. This keeps VF/VT zones visually distinct from plain
        # flat roofs while remaining modest enough for exterior LOD3.
        best_len = 0.0
        axis = (1.0, 0.0)
        for i in range(len(ring)):
            ax, ay = ring[i]
            bx, by = ring[(i + 1) % len(ring)]
            d = math.hypot(bx - ax, by - ay)
            if d > best_len:
                best_len = d
                axis = ((bx - ax) / d, (by - ay) / d)
        perp = (-axis[1], axis[0])
        u_values = [x * axis[0] + y * axis[1] for x, y in ring]
        v_values = [x * perp[0] + y * perp[1] for x, y in ring]
        u_min, u_max = min(u_values), max(u_values)
        v_min, v_max = min(v_values), max(v_values)
        width = v_max - v_min
        if (u_max - u_min) <= 0.2 or width <= 0.2:
            return

        rise = max(0.35, min(width * 0.16, 1.15))
        segments = 8

        def p(u: float, v: float, z: float) -> tuple[float, float, float]:
            return (axis[0] * u + perp[0] * v, axis[1] * u + perp[1] * v, z)

        rows: list[tuple[float, float]] = []
        for j in range(segments + 1):
            t = j / segments
            v = v_min + width * t
            z = eaves_z + math.sin(math.pi * t) * rise
            rows.append((v, z))

        pid = building.parcel_id
        for j in range(segments):
            v0, z0 = rows[j]
            v1, z1 = rows[j + 1]
            mesh.add_quad(
                p0=p(u_min, v0, z0),
                p1=p(u_max, v0, z0),
                p2=p(u_max, v1, z1),
                p3=p(u_min, v1, z1),
                role="RoofSurface",
                surface_id=f"{pid}.roof.vault.{j}",
                material_key=roof_mat,
            )

        # Close visible barrel ends with wall-colored lunettes.
        v_mid = (v_min + v_max) / 2.0
        z_top = eaves_z + rise
        for label, u in (("start", u_min), ("end", u_max)):
            e0 = mesh.add_vertex(*p(u, v_min, eaves_z))
            crown = mesh.add_vertex(*p(u, v_mid, z_top))
            e1 = mesh.add_vertex(*p(u, v_max, eaves_z))
            mesh.add_face([e0, crown, e1], role="WallSurface",
                          surface_id=f"{pid}.vault_lunette.{label}",
                          material_key="wall_main")
