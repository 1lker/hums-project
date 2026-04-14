"""PRD-003 · §6.2 — mansard roof (steep lower band + shallow upper deck)."""
from __future__ import annotations
import math

from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from ..footprint_ops import inset as inset_ring
from .base import RoofGenerator


@prd("003", "§6.2 MansardRoof")
class MansardRoof(RoofGenerator):
    LOWER_PITCH_DEG = 70.0
    UPPER_PITCH_DEG = 15.0
    LOWER_BAND_FRACTION = 0.4   # inset distance as fraction of half-min-dim

    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        from shapely.geometry import Polygon
        poly = Polygon(ring)
        minx, miny, maxx, maxy = poly.bounds
        half_min = min(maxx - minx, maxy - miny) / 2.0
        lower_inset = max(0.15, half_min * self.LOWER_BAND_FRACTION)
        upper_inset = max(0.25, lower_inset + half_min * 0.3)

        lower_rise = lower_inset * math.tan(math.radians(self.LOWER_PITCH_DEG))
        upper_rise = (upper_inset - lower_inset) * math.tan(math.radians(self.UPPER_PITCH_DEG))

        lower = inset_ring(ring, lower_inset)
        upper = inset_ring(ring, upper_inset)
        if not lower or not upper:
            return
        pid = building.parcel_id
        n = len(ring)
        # Lower steep band
        for i in range(n):
            a = ring[i]; b = ring[(i + 1) % n]
            ia = lower[int(round(i * len(lower) / n)) % len(lower)]
            ib = lower[(int(round(i * len(lower) / n)) + 1) % len(lower)]
            mesh.add_quad(
                p0=(a[0], a[1], eaves_z), p1=(b[0], b[1], eaves_z),
                p2=(ib[0], ib[1], eaves_z + lower_rise), p3=(ia[0], ia[1], eaves_z + lower_rise),
                role="RoofSurface",
                surface_id=f"{pid}.roof.mansard_lower.{i}", material_key="roof",
            )
        # Upper shallow band
        for i in range(len(lower)):
            a = lower[i]; b = lower[(i + 1) % len(lower)]
            ia = upper[int(round(i * len(upper) / len(lower))) % len(upper)]
            ib = upper[(int(round(i * len(upper) / len(lower))) + 1) % len(upper)]
            mesh.add_quad(
                p0=(a[0], a[1], eaves_z + lower_rise), p1=(b[0], b[1], eaves_z + lower_rise),
                p2=(ib[0], ib[1], eaves_z + lower_rise + upper_rise), p3=(ia[0], ia[1], eaves_z + lower_rise + upper_rise),
                role="RoofSurface",
                surface_id=f"{pid}.roof.mansard_upper.{i}", material_key="roof",
            )
        # Flat top deck
        deck = [mesh.add_vertex(x, y, eaves_z + lower_rise + upper_rise) for (x, y) in upper]
        mesh.add_face(deck, role="RoofSurface",
                      surface_id=f"{pid}.roof.deck", material_key="roof")
