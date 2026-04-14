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
from ..footprint_ops import inset as inset_ring
from .base import RoofGenerator


@prd("003", "§6.2 HipRoof")
class HipRoof(RoofGenerator):
    EAVES_OVERHANG = 0.3  # outward overhang in metres

    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        pitch_rad = math.radians(building.roof.pitch_deg if building.roof else 30.0)

        # Inset by half the min-dim for a reasonable apex footprint.
        from shapely.geometry import Polygon
        poly = Polygon(ring)
        minx, miny, maxx, maxy = poly.bounds
        half_min = min(maxx - minx, maxy - miny) / 2.0
        inset_distance = max(0.1, half_min * 0.8)
        inner = inset_ring(ring, inset_distance)
        rise = inset_distance * math.tan(pitch_rad)

        pid = building.parcel_id
        if not inner:
            # Roof collapses to a point (tight footprint) — fall back to a single peak
            cx = sum(p[0] for p in ring) / len(ring)
            cy = sum(p[1] for p in ring) / len(ring)
            apex_z = eaves_z + rise
            apex = mesh.add_vertex(cx, cy, apex_z)
            for i in range(len(ring)):
                a = ring[i]
                b = ring[(i + 1) % len(ring)]
                ia = mesh.add_vertex(a[0], a[1], eaves_z)
                ib = mesh.add_vertex(b[0], b[1], eaves_z)
                mesh.add_face([ia, ib, apex], role="RoofSurface",
                              surface_id=f"{pid}.roof.tri.{i}", material_key="roof")
            return

        # Build hip quads: outer edge → matching inner edge
        n = len(ring)
        for i in range(n):
            a = ring[i]
            b = ring[(i + 1) % n]
            # pair with closest inner vertices by index ratio
            ia_idx = int(round(i * len(inner) / n)) % len(inner)
            ib_idx = (ia_idx + 1) % len(inner)
            ia = inner[ia_idx]
            ib = inner[ib_idx]
            mesh.add_quad(
                p0=(a[0], a[1], eaves_z), p1=(b[0], b[1], eaves_z),
                p2=(ib[0], ib[1], eaves_z + rise), p3=(ia[0], ia[1], eaves_z + rise),
                role="RoofSurface",
                surface_id=f"{pid}.roof.hip.{i}",
                material_key="roof",
            )
        # Top deck (small flat ridge region when inset didn't collapse to a point)
        top_idx = [mesh.add_vertex(x, y, eaves_z + rise) for (x, y) in inner]
        mesh.add_face(top_idx, role="RoofSurface",
                      surface_id=f"{pid}.roof.deck", material_key="roof")
