"""PRD-003 · §6.2 — gable roof.

Approximation: pick the longest edge of the footprint as the ridge axis,
project footprint onto that axis, raise ridge midline to eaves + rise.
Fine for rectangular-ish footprints; wonky for very L-shaped plans (use
complex_pitched for those).
"""
from __future__ import annotations
import math

from shapely.geometry import LineString, Point
from shapely.ops import split

from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from ..footprint_ops import to_polygon
from .base import RoofGenerator


@prd("003", "§6.2 GableRoof")
class GableRoof(RoofGenerator):
    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
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

        def z_at(x: float, y: float) -> float:
            t = x * perp[0] + y * perp[1]
            return eaves_z + (1 - abs(t - t_mid) / max(span / 2.0, 0.001)) * rise

        poly = to_polygon(ring)
        margin = max(u_max - u_min, span) + 5.0
        ridge_line = LineString([
            p(u_min - margin, t_mid, eaves_z)[:2],
            p(u_max + margin, t_mid, eaves_z)[:2],
        ])
        try:
            pieces = list(split(poly, ridge_line).geoms)
        except Exception:
            pieces = [poly]

        if len(pieces) < 2:
            # Fallback remains exact to the KML footprint: no bbox roof.
            pieces = [poly]

        closure_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
        for idx, piece in enumerate(pieces):
            if piece.is_empty or piece.area < 0.01:
                continue
            coords = list(piece.exterior.coords)
            if coords and coords[0] == coords[-1]:
                coords = coords[:-1]
            if len(coords) < 3:
                continue
            for a, b in zip(coords, coords[1:] + coords[:1]):
                mx = (a[0] + b[0]) / 2.0
                my = (a[1] + b[1]) / 2.0
                if poly.exterior.distance(Point(mx, my)) < 0.02:
                    closure_segments.append(((a[0], a[1]), (b[0], b[1])))
            verts = [mesh.add_vertex(x, y, z_at(x, y)) for x, y in coords]
            mesh.add_face(
                verts,
                role="RoofSurface",
                surface_id=f"{pid}.roof.kml_gable.{idx}",
                material_key=roof_mat,
            )

        _emit_gable_edge_closures(mesh, pid, closure_segments, eaves_z, z_at)


def _emit_gable_edge_closures(
    mesh: BuildingMesh,
    pid: str,
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
    eaves_z: float,
    z_at,
) -> None:
    """Fill vertical gable-end gaps between wall top and sloping roof edge.

    The roof planes are clipped exactly to the KML/SHP footprint. On gable
    ends, that sloped roof boundary rises above the rectangular wall top and
    leaves triangular voids unless we add these closure faces.
    """
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    n = 0
    for a, b in segments:
        key_pts = sorted([
            (round(a[0] * 1000), round(a[1] * 1000)),
            (round(b[0] * 1000), round(b[1] * 1000)),
        ])
        key = (key_pts[0], key_pts[1])
        if key in seen:
            continue
        seen.add(key)

        za = z_at(a[0], a[1])
        zb = z_at(b[0], b[1])
        if max(za, zb) <= eaves_z + 0.03:
            continue

        a_base = mesh.add_vertex(a[0], a[1], eaves_z)
        b_base = mesh.add_vertex(b[0], b[1], eaves_z)
        verts = []
        if za > eaves_z + 0.03:
            verts.append(mesh.add_vertex(a[0], a[1], za))
        if zb > eaves_z + 0.03:
            verts.append(mesh.add_vertex(b[0], b[1], zb))

        if len(verts) == 2:
            mesh.add_face(
                [a_base, verts[0], verts[1], b_base],
                role="WallSurface",
                surface_id=f"{pid}.gable_closure.{n}",
                material_key="wall_main",
            )
        elif za > eaves_z + 0.03:
            mesh.add_face(
                [a_base, verts[0], b_base],
                role="WallSurface",
                surface_id=f"{pid}.gable_closure.{n}",
                material_key="wall_main",
            )
        elif zb > eaves_z + 0.03:
            mesh.add_face(
                [a_base, verts[0], b_base],
                role="WallSurface",
                surface_id=f"{pid}.gable_closure.{n}",
                material_key="wall_main",
            )
        n += 1
