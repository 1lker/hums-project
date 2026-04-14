"""PRD-004 · Track C — Ayia Eftimia church + clocher + kubbe.

Reads the main church polygon from ``non_parcel_footprints.geojson`` (the
largest "church"-kind feature) and composes three volumes:

  1. Body (nave) — extruded footprint, hip-capped at 7 m + 25° pitch.
  2. Kubbe (central dome) — hemisphere over body centroid.
  3. Clocher (bell tower) — slim square tower at the south edge of the body.

The whole thing is returned as one BuildingMesh so backends can place it by
the scene centroid like any other building.
"""
from __future__ import annotations
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, shape

from ...common.paths import NON_PARCEL_FOOTPRINTS_GEOJSON
from ...common.prd import prd
from ...modeling.building import FacadePalette
from ..mesh_graph import BuildingMesh


BODY_HEIGHT = 7.0
ROOF_PITCH_DEG = 25.0
DOME_RADIUS = 3.5
DOME_BASE_Z = 7.8        # top of body + a small drum
DOME_SEGMENTS = 16
DOME_RINGS = 8
CLOCHER_SIDE = 3.0
CLOCHER_HEIGHT = 12.0
CLOCHER_ROOF_HEIGHT = 3.5


STONE_PALETTE = FacadePalette(
    wall_main=(216, 204, 179),
    wall_accent=(196, 182, 156),
    trim=(120, 100, 80),
    roof=(98, 104, 110),
    shutters=None,
    gf_shopfront=None,
    source="church_period_default",
)


@prd("004", "ChurchBuilder")
class ChurchBuilder:
    def build(self, block_centroid_utm: tuple[float, float]) -> BuildingMesh | None:
        poly = _load_church_polygon()
        if poly is None:
            return None

        c = poly.centroid
        origin_utm = (c.x, c.y)

        # Convert polygon to local coords centred on the church centroid.
        ring_local = [(x - c.x, y - c.y) for (x, y) in list(poly.exterior.coords)[:-1]]

        mesh = BuildingMesh(
            parcel_id="CHURCH",
            placement_origin_utm=origin_utm,
            placement_rotation_deg=0.0,
            palette=STONE_PALETTE,
            metadata={
                "material_class": "A",
                "structure_type": "church",
                "footprint_source": "traced",
                "notes": {"role": "Rum Ortodoks Kilisesi Ayia Eftimia"},
                "block_centroid_utm": block_centroid_utm,
            },
        )

        self._emit_body(mesh, ring_local)
        self._emit_hip_roof(mesh, ring_local)
        self._emit_kubbe(mesh, ring_local)
        self._emit_clocher(mesh, ring_local)
        return mesh

    # -- body + simple hip roof -----------------------------------------------
    def _emit_body(self, mesh: BuildingMesh, ring: list[tuple[float, float]]) -> None:
        pid = mesh.parcel_id
        # Ground (CityGML normal -Z → reverse ring)
        gidx = [mesh.add_vertex(x, y, 0.0) for (x, y) in reversed(ring)]
        mesh.add_face(gidx, role="GroundSurface",
                      surface_id=f"{pid}.ground", material_key="plinth_stone")
        # Walls (CCW footprint; outward normal from bottom-start → top-start → top-end → bottom-end)
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(a[0], a[1], 0.0),
                p1=(a[0], a[1], BODY_HEIGHT),
                p2=(b[0], b[1], BODY_HEIGHT),
                p3=(b[0], b[1], 0.0),
                role="ChurchBody",
                surface_id=f"{pid}.body.{i}",
                material_key="wall_main",
            )
        # Plinth band (0.6 m tall) with slightly outward offset
        plinth_h = 0.6
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(a[0], a[1], 0.0),
                p1=(a[0], a[1], plinth_h),
                p2=(b[0], b[1], plinth_h),
                p3=(b[0], b[1], 0.0),
                role="PlinthSurface",
                surface_id=f"{pid}.plinth.{i}",
                material_key="plinth_stone",
            )

    def _emit_hip_roof(self, mesh: BuildingMesh, ring: list[tuple[float, float]]) -> None:
        # Simple pyramid hip over centroid for the church body.
        pid = mesh.parcel_id
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        poly = Polygon(ring)
        minx, miny, maxx, maxy = poly.bounds
        half_min = min(maxx - minx, maxy - miny) / 2.0
        rise = half_min * math.tan(math.radians(ROOF_PITCH_DEG))
        apex_z = BODY_HEIGHT + rise
        apex = mesh.add_vertex(cx, cy, apex_z)
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            ia = mesh.add_vertex(a[0], a[1], BODY_HEIGHT)
            ib = mesh.add_vertex(b[0], b[1], BODY_HEIGHT)
            mesh.add_face([ia, apex, ib], role="RoofSurface",
                          surface_id=f"{pid}.roof.{i}",
                          material_key="tile_terracotta")

    # -- dome ------------------------------------------------------------------
    def _emit_kubbe(self, mesh: BuildingMesh, ring: list[tuple[float, float]]) -> None:
        pid = mesh.parcel_id
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)

        # drum (short cylinder under the dome)
        drum_h = 0.8
        drum_r = DOME_RADIUS * 1.05
        drum_verts: list[int] = []
        for k in range(DOME_SEGMENTS):
            ang = 2 * math.pi * k / DOME_SEGMENTS
            x = cx + drum_r * math.cos(ang)
            y = cy + drum_r * math.sin(ang)
            drum_verts.append(mesh.add_vertex(x, y, DOME_BASE_Z - drum_h))
        top_drum_verts: list[int] = []
        for k in range(DOME_SEGMENTS):
            ang = 2 * math.pi * k / DOME_SEGMENTS
            x = cx + drum_r * math.cos(ang)
            y = cy + drum_r * math.sin(ang)
            top_drum_verts.append(mesh.add_vertex(x, y, DOME_BASE_Z))
        for k in range(DOME_SEGMENTS):
            kp = (k + 1) % DOME_SEGMENTS
            mesh.add_quad(
                p0=(mesh.vertices[drum_verts[k]].x, mesh.vertices[drum_verts[k]].y, DOME_BASE_Z - drum_h),
                p1=(mesh.vertices[top_drum_verts[k]].x, mesh.vertices[top_drum_verts[k]].y, DOME_BASE_Z),
                p2=(mesh.vertices[top_drum_verts[kp]].x, mesh.vertices[top_drum_verts[kp]].y, DOME_BASE_Z),
                p3=(mesh.vertices[drum_verts[kp]].x, mesh.vertices[drum_verts[kp]].y, DOME_BASE_Z - drum_h),
                role="ChurchBody",
                surface_id=f"{pid}.drum.{k}",
                material_key="wall_main",
            )

        # hemisphere strips
        prev_ring: list[int] = top_drum_verts
        for ring_idx in range(1, DOME_RINGS + 1):
            phi = (math.pi / 2) * (ring_idx / DOME_RINGS)
            r = DOME_RADIUS * math.cos(phi)
            z = DOME_BASE_Z + DOME_RADIUS * math.sin(phi)
            curr_ring: list[int] = []
            for k in range(DOME_SEGMENTS):
                ang = 2 * math.pi * k / DOME_SEGMENTS
                curr_ring.append(mesh.add_vertex(cx + r * math.cos(ang),
                                                 cy + r * math.sin(ang), z))
            for k in range(DOME_SEGMENTS):
                kp = (k + 1) % DOME_SEGMENTS
                mesh.add_quad(
                    p0=_vp(mesh, prev_ring[k]),
                    p1=_vp(mesh, curr_ring[k]),
                    p2=_vp(mesh, curr_ring[kp]),
                    p3=_vp(mesh, prev_ring[kp]),
                    role="ChurchDome",
                    surface_id=f"{pid}.dome.{ring_idx}.{k}",
                    material_key="dome_lead",
                )
            prev_ring = curr_ring

    # -- clocher ---------------------------------------------------------------
    def _emit_clocher(self, mesh: BuildingMesh, ring: list[tuple[float, float]]) -> None:
        pid = mesh.parcel_id
        poly = Polygon(ring)
        minx, miny, maxx, maxy = poly.bounds
        # Position the clocher on the south-west side, just outside church footprint
        cx = (minx + maxx) / 2 - 2.0
        cy = miny - CLOCHER_SIDE / 2 - 0.5
        half = CLOCHER_SIDE / 2
        # 4 tower faces
        corners = [
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        ]
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            mesh.add_quad(
                p0=(a[0], a[1], 0.0),
                p1=(a[0], a[1], CLOCHER_HEIGHT),
                p2=(b[0], b[1], CLOCHER_HEIGHT),
                p3=(b[0], b[1], 0.0),
                role="Clocher",
                surface_id=f"{pid}.clocher.side.{i}",
                material_key="wall_main",
            )
        # Pyramidal cap
        apex_z = CLOCHER_HEIGHT + CLOCHER_ROOF_HEIGHT
        apex = mesh.add_vertex(cx, cy, apex_z)
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            ia = mesh.add_vertex(a[0], a[1], CLOCHER_HEIGHT)
            ib = mesh.add_vertex(b[0], b[1], CLOCHER_HEIGHT)
            mesh.add_face([ia, apex, ib], role="RoofSurface",
                          surface_id=f"{pid}.clocher.roof.{i}",
                          material_key="tile_terracotta")


def _vp(mesh: BuildingMesh, idx: int) -> tuple[float, float, float]:
    v = mesh.vertices[idx]
    return (v.x, v.y, v.z)


def _load_church_polygon() -> Polygon | None:
    if not NON_PARCEL_FOOTPRINTS_GEOJSON.exists():
        return None
    fc = json.loads(NON_PARCEL_FOOTPRINTS_GEOJSON.read_text())
    candidates = [f for f in fc["features"]
                  if f["properties"].get("kind") == "church"]
    if not candidates:
        return None
    candidates.sort(key=lambda f: f["properties"].get("area_m2", 0), reverse=True)
    return shape(candidates[0]["geometry"])
