"""PRD-003 · §6.2 — flat roof + parapet."""
from __future__ import annotations

from shapely.ops import triangulate

from ....common.heritage_profile import PROFILE
from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from ..footprint_ops import to_polygon
from .base import RoofGenerator


@prd("003", "§6.2 FlatRoof")
class FlatRoof(RoofGenerator):
    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        parapet = PROFILE.storeys.parapet_m
        roof_mat = self.material_key(building)
        # Deck at eaves_z. Emit clipped triangles so L-shaped/notched roofs
        # keep their open voids instead of being fan-filled across the notch.
        poly = to_polygon(ring)
        deck_n = 0
        for tri in triangulate(poly):
            clipped = tri.intersection(poly)
            if clipped.is_empty:
                continue
            polys = [clipped] if clipped.geom_type == "Polygon" else [
                g for g in getattr(clipped, "geoms", []) if g.geom_type == "Polygon"
            ]
            for face_poly in polys:
                if face_poly.area < 0.01:
                    continue
                coords = list(face_poly.exterior.coords)
                if coords and coords[0] == coords[-1]:
                    coords = coords[:-1]
                if len(coords) < 3:
                    continue
                deck_idx = [mesh.add_vertex(x, y, eaves_z) for (x, y) in coords]
                mesh.add_face(
                    deck_idx, role="RoofSurface",
                    surface_id=f"{building.parcel_id}.roof.deck.{deck_n}",
                    material_key=roof_mat,
                )
                deck_n += 1
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
