"""PRD-003 · §6.2 — hip roof (inset-and-raise approximation).

True straight-skeleton requires scikit-geometry. For LOD3 at 1923 block scale
the inset-and-raise approximation is acceptable: raise the inset ring to an
apex height ``inset * tan(pitch)``, and connect each outer edge to its
corresponding inset edge via a single quad. Works for any convex or weakly
non-convex footprint.
"""
from __future__ import annotations
import math

from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from .base import RoofGenerator


@prd("003", "§6.2 HipRoof")
class HipRoof(RoofGenerator):
    EAVES_OVERHANG = 0.3  # outward overhang in metres
    MIN_INSET = 0.3       # below this we switch to pyramid-at-centroid

    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        pitch_rad = math.radians(building.roof.pitch_deg if building.roof else 30.0)
        roof_mat = self.material_key(building)

        pid = building.parcel_id

        # Use the longest footprint edge as ridge direction. A hip roof should
        # resolve to a ridge or point, not a broad flat deck, for presentation
        # models.
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
        length = u_max - u_min
        width = v_max - v_min
        if length <= 0.2 or width <= 0.2:
            return

        v_mid = (v_min + v_max) / 2.0
        half_width = width / 2.0
        rise = max(0.35, min(half_width * math.tan(pitch_rad), 3.0))
        z_top = eaves_z + rise
        ridge_margin = min(half_width, length * 0.38)
        r0 = u_min + ridge_margin
        r1 = u_max - ridge_margin

        def p(u: float, v: float, z: float) -> tuple[float, float, float]:
            return (axis[0] * u + perp[0] * v, axis[1] * u + perp[1] * v, z)

        if r1 <= r0 + 0.2:
            apex = mesh.add_vertex(*p((u_min + u_max) / 2.0, v_mid, z_top))
            corners = [
                p(u_min, v_min, eaves_z),
                p(u_max, v_min, eaves_z),
                p(u_max, v_max, eaves_z),
                p(u_min, v_max, eaves_z),
            ]
            for i in range(4):
                ia = mesh.add_vertex(*corners[i])
                ib = mesh.add_vertex(*corners[(i + 1) % 4])
                mesh.add_face([ia, apex, ib], role="RoofSurface",
                              surface_id=f"{pid}.roof.pyramid.{i}", material_key=roof_mat)
            return

        # Two long trapezoid slopes and two triangular hips.
        mesh.add_quad(
            p0=p(u_min, v_min, eaves_z), p1=p(u_max, v_min, eaves_z),
            p2=p(r1, v_mid, z_top), p3=p(r0, v_mid, z_top),
            role="RoofSurface", surface_id=f"{pid}.roof.hip.long_a",
            material_key=roof_mat,
        )
        mesh.add_quad(
            p0=p(r0, v_mid, z_top), p1=p(r1, v_mid, z_top),
            p2=p(u_max, v_max, eaves_z), p3=p(u_min, v_max, eaves_z),
            role="RoofSurface", surface_id=f"{pid}.roof.hip.long_b",
            material_key=roof_mat,
        )
        for label, u, ridge_u in (("start", u_min, r0), ("end", u_max, r1)):
            e0 = mesh.add_vertex(*p(u, v_min, eaves_z))
            ridge = mesh.add_vertex(*p(ridge_u, v_mid, z_top))
            e1 = mesh.add_vertex(*p(u, v_max, eaves_z))
            mesh.add_face([e0, ridge, e1], role="RoofSurface",
                          surface_id=f"{pid}.roof.hip.{label}",
                          material_key=roof_mat)

        cap_w = min(0.14, width * 0.03)
        mesh.add_quad(
            p0=p(r0, v_mid - cap_w, z_top + 0.03),
            p1=p(r1, v_mid - cap_w, z_top + 0.03),
            p2=p(r1, v_mid + cap_w, z_top + 0.03),
            p3=p(r0, v_mid + cap_w, z_top + 0.03),
            role="RoofSurface",
            surface_id=f"{pid}.roof.ridge_cap",
            material_key=roof_mat,
        )
