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

        # Project footprint vertices onto perp to find min/max span
        t_values = [v[0] * perp[0] + v[1] * perp[1] for v in ring]
        t_min, t_max = min(t_values), max(t_values)
        span = t_max - t_min
        rise = (span / 2.0) * math.tan(pitch_rad)

        # Ridge line = midline along axis
        t_mid = (t_min + t_max) / 2.0

        # Build roof faces: for each pair of consecutive vertices, raise them
        # to a ridge-projected point and emit two sloped quads.
        pid = building.parcel_id
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            t_a = a[0] * perp[0] + a[1] * perp[1]
            t_b = b[0] * perp[0] + b[1] * perp[1]
            # determine z at each vertex: linear from eaves → eaves+rise at ridge
            z_a = eaves_z + (1 - abs(t_a - t_mid) / max(span / 2.0, 0.001)) * rise
            z_b = eaves_z + (1 - abs(t_b - t_mid) / max(span / 2.0, 0.001)) * rise
            # Wind CCW from above so normal has +Z component (points up/out).
            mesh.add_quad(
                p0=(a[0], a[1], eaves_z), p1=(a[0], a[1], z_a),
                p2=(b[0], b[1], z_b), p3=(b[0], b[1], eaves_z),
                role="RoofSurface",
                surface_id=f"{pid}.roof.{i}",
                material_key="tile_terracotta",
            )
