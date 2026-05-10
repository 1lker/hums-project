"""PRD-003 · §6.2 — gable roof.

Approximation: pick the longest edge of the footprint as the ridge axis,
project footprint onto that axis, raise ridge midline to eaves + rise.
Fine for rectangular-ish footprints; wonky for very L-shaped plans (use
complex_pitched for those).
"""
from __future__ import annotations
import math

from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from .base import RoofGenerator


@prd("003", "§6.2 GableRoof")
class GableRoof(RoofGenerator):
    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 4:
            return
        pitch_rad = math.radians(building.roof.pitch_deg if building.roof else 30.0)
        roof_mat = self.material_key(building)

        # Find longest edge → ridge direction
        best_len = 0.0
        best_axis = (1.0, 0.0)
        for i in range(len(ring)):
            ax, ay = ring[i]
            bx, by = ring[(i + 1) % len(ring)]
            d = math.hypot(bx - ax, by - ay)
            if d > best_len:
                best_len = d
                best_axis = ((bx - ax) / d, (by - ay) / d)

        # Perpendicular to ridge = span direction
        perp = (-best_axis[1], best_axis[0])

        # Project footprint vertices onto the roof coordinate frame.
        u_values = [v[0] * best_axis[0] + v[1] * best_axis[1] for v in ring]
        t_values = [v[0] * perp[0] + v[1] * perp[1] for v in ring]
        u_min, u_max = min(u_values), max(u_values)
        t_min, t_max = min(t_values), max(t_values)
        span = t_max - t_min
        if span <= 0.2 or (u_max - u_min) <= 0.2:
            return
        rise = max(0.35, min((span / 2.0) * math.tan(pitch_rad), 3.0))
        t_mid = (t_min + t_max) / 2.0

        pid = building.parcel_id

        def p(u: float, t: float, z: float) -> tuple[float, float, float]:
            return (
                best_axis[0] * u + perp[0] * t,
                best_axis[1] * u + perp[1] * t,
                z,
            )

        z_ridge = eaves_z + rise
        # Two real pitched planes with a continuous ridge. This is intentionally
        # bbox-based: most Pervititch parcels here are narrow rectangles, and a
        # clear roof silhouette reads much better than a nearly-flat fan.
        mesh.add_quad(
            p0=p(u_min, t_min, eaves_z),
            p1=p(u_max, t_min, eaves_z),
            p2=p(u_max, t_mid, z_ridge),
            p3=p(u_min, t_mid, z_ridge),
            role="RoofSurface",
            surface_id=f"{pid}.roof.slope.low",
            material_key=roof_mat,
        )
        mesh.add_quad(
            p0=p(u_min, t_mid, z_ridge),
            p1=p(u_max, t_mid, z_ridge),
            p2=p(u_max, t_max, eaves_z),
            p3=p(u_min, t_max, eaves_z),
            role="RoofSurface",
            surface_id=f"{pid}.roof.slope.high",
            material_key=roof_mat,
        )

        # Gable end walls close the triangular ends under the roof.
        for label, u in (("start", u_min), ("end", u_max)):
            e0 = mesh.add_vertex(*p(u, t_min, eaves_z))
            ridge = mesh.add_vertex(*p(u, t_mid, z_ridge))
            e1 = mesh.add_vertex(*p(u, t_max, eaves_z))
            mesh.add_face(
                [e0, ridge, e1],
                role="WallSurface",
                surface_id=f"{pid}.gable_end.{label}",
                material_key="wall_main",
            )

        # A narrow cap at the ridge gives the roof a finished, less-CAD-flat edge.
        cap_w = min(0.16, span * 0.035)
        mesh.add_quad(
            p0=p(u_min, t_mid - cap_w, z_ridge + 0.03),
            p1=p(u_max, t_mid - cap_w, z_ridge + 0.03),
            p2=p(u_max, t_mid + cap_w, z_ridge + 0.03),
            p3=p(u_min, t_mid + cap_w, z_ridge + 0.03),
            role="RoofSurface",
            surface_id=f"{pid}.roof.ridge_cap",
            material_key=roof_mat,
        )
