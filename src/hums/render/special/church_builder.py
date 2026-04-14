"""PRD-004 · Track C — Ayia Eftimia church + clocher + kubbe.

Orthodox cruciform basilica model:

  1. Nave body — extruded footprint with a *low* (near-flat) hip roof so the
     central dome reads as the dominant mass.
  2. Drum — a tall cylinder sitting on the centre of the body.
  3. Kubbe — UV hemisphere above the drum + a tiny lantern on top.
  4. Plinth band — stone skirting around the body base.
  5. Clocher — tall bell tower at the south-west corner with pyramidal cap.
"""
from __future__ import annotations
import json
import math

from shapely.geometry import Polygon, shape

from ...common.paths import NON_PARCEL_FOOTPRINTS_GEOJSON
from ...common.prd import prd
from ...modeling.building import FacadePalette
from ..mesh_graph import BuildingMesh


BODY_HEIGHT = 8.0
PLINTH_HEIGHT = 0.8
DRUM_BASE_Z = BODY_HEIGHT + 0.4
DRUM_HEIGHT = 4.0
DRUM_RADIUS = 4.0
DOME_RADIUS = 4.2             # slightly wider than drum for a flush cornice
DOME_SEGMENTS = 24
DOME_RINGS = 10
LANTERN_HEIGHT = 1.8
LANTERN_RADIUS = 0.7
CLOCHER_SIDE = 3.2
CLOCHER_HEIGHT = 15.0
CLOCHER_ROOF_HEIGHT = 4.0


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
            },
        )

        self._emit_plinth(mesh, ring_local)
        self._emit_body(mesh, ring_local)
        self._emit_low_roof_apron(mesh, ring_local)
        self._emit_drum(mesh, ring_local)
        self._emit_kubbe(mesh, ring_local)
        self._emit_lantern(mesh, ring_local)
        self._emit_clocher(mesh, ring_local)
        return mesh

    # -------------------------------------------------------------------------
    def _emit_plinth(self, mesh: BuildingMesh, ring) -> None:
        pid = mesh.parcel_id
        # Raised stone plinth: slightly offset outward + taller than parcel walls.
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(a[0], a[1], 0.0),
                p1=(a[0], a[1], PLINTH_HEIGHT),
                p2=(b[0], b[1], PLINTH_HEIGHT),
                p3=(b[0], b[1], 0.0),
                role="PlinthSurface",
                surface_id=f"{pid}.plinth.{i}",
                material_key="plinth_stone",
            )

    def _emit_body(self, mesh: BuildingMesh, ring) -> None:
        pid = mesh.parcel_id
        gidx = [mesh.add_vertex(x, y, 0.0) for (x, y) in reversed(ring)]
        mesh.add_face(gidx, role="GroundSurface",
                      surface_id=f"{pid}.ground", material_key="plinth_stone")
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(a[0], a[1], PLINTH_HEIGHT),
                p1=(a[0], a[1], BODY_HEIGHT),
                p2=(b[0], b[1], BODY_HEIGHT),
                p3=(b[0], b[1], PLINTH_HEIGHT),
                role="ChurchBody",
                surface_id=f"{pid}.body.{i}",
                material_key="wall_main",
            )

    def _emit_low_roof_apron(self, mesh: BuildingMesh, ring) -> None:
        """Almost-flat hip apron so the drum/dome reads as the dominant mass."""
        pid = mesh.parcel_id
        # Minor rise (50 cm) toward the centroid — reads as a low hip, not a pyramid.
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        rise = 0.5
        ridge_z = BODY_HEIGHT + rise
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            # trapezoid from outer edge rising to the midline point
            ia = mesh.add_vertex(a[0], a[1], BODY_HEIGHT)
            ib = mesh.add_vertex(b[0], b[1], BODY_HEIGHT)
            # interior point = 25% from edge to centroid
            midax = a[0] + (cx - a[0]) * 0.25
            miday = a[1] + (cy - a[1]) * 0.25
            midbx = b[0] + (cx - b[0]) * 0.25
            midby = b[1] + (cy - b[1]) * 0.25
            ma = mesh.add_vertex(midax, miday, ridge_z)
            mb = mesh.add_vertex(midbx, midby, ridge_z)
            mesh.add_face([ia, ma, mb, ib], role="RoofSurface",
                          surface_id=f"{pid}.roof.apron.{i}",
                          material_key="tile_terracotta")
        # Top flat ring around the drum base (matches drum footprint radius).
        # Emit a concentric deck between the apron inner edge and the drum base.
        deck_inner: list[int] = []
        for k in range(DOME_SEGMENTS):
            ang = 2 * math.pi * k / DOME_SEGMENTS
            deck_inner.append(mesh.add_vertex(cx + DRUM_RADIUS * math.cos(ang),
                                              cy + DRUM_RADIUS * math.sin(ang),
                                              DRUM_BASE_Z))
        # One triangle fan from deck_inner to a central apex (just below drum base) → fills the gap.
        apex = mesh.add_vertex(cx, cy, DRUM_BASE_Z - 0.05)
        for k in range(DOME_SEGMENTS):
            kp = (k + 1) % DOME_SEGMENTS
            mesh.add_face([apex, deck_inner[k], deck_inner[kp]],
                          role="RoofSurface",
                          surface_id=f"{pid}.roof.deck.{k}",
                          material_key="tile_terracotta")

    def _emit_drum(self, mesh: BuildingMesh, ring) -> None:
        pid = mesh.parcel_id
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        top_z = DRUM_BASE_Z + DRUM_HEIGHT
        verts_lower: list[int] = []
        verts_upper: list[int] = []
        for k in range(DOME_SEGMENTS):
            ang = 2 * math.pi * k / DOME_SEGMENTS
            x = cx + DRUM_RADIUS * math.cos(ang)
            y = cy + DRUM_RADIUS * math.sin(ang)
            verts_lower.append(mesh.add_vertex(x, y, DRUM_BASE_Z))
            verts_upper.append(mesh.add_vertex(x, y, top_z))
        for k in range(DOME_SEGMENTS):
            kp = (k + 1) % DOME_SEGMENTS
            mesh.add_quad(
                p0=_vp(mesh, verts_lower[k]),
                p1=_vp(mesh, verts_upper[k]),
                p2=_vp(mesh, verts_upper[kp]),
                p3=_vp(mesh, verts_lower[kp]),
                role="ChurchBody",
                surface_id=f"{pid}.drum.{k}",
                material_key="wall_main",
            )
        # Narrow arched-window band — flat inset strips on alternating segments.
        band_h = 1.6
        band_bot = DRUM_BASE_Z + (DRUM_HEIGHT - band_h) / 2
        band_top = band_bot + band_h
        for k in range(0, DOME_SEGMENTS, 2):
            kp = (k + 1) % DOME_SEGMENTS
            ang0 = 2 * math.pi * k / DOME_SEGMENTS
            ang1 = 2 * math.pi * kp / DOME_SEGMENTS
            rr = DRUM_RADIUS - 0.1
            x0, y0 = cx + rr * math.cos(ang0), cy + rr * math.sin(ang0)
            x1, y1 = cx + rr * math.cos(ang1), cy + rr * math.sin(ang1)
            mesh.add_quad(
                p0=(x0, y0, band_bot),
                p1=(x0, y0, band_top),
                p2=(x1, y1, band_top),
                p3=(x1, y1, band_bot),
                role="Window",
                surface_id=f"{pid}.drum.window.{k}",
                material_key="window_glass",
            )

    def _emit_kubbe(self, mesh: BuildingMesh, ring) -> None:
        pid = mesh.parcel_id
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        base_z = DRUM_BASE_Z + DRUM_HEIGHT

        prev_ring: list[int] = []
        for k in range(DOME_SEGMENTS):
            ang = 2 * math.pi * k / DOME_SEGMENTS
            prev_ring.append(mesh.add_vertex(
                cx + DOME_RADIUS * math.cos(ang),
                cy + DOME_RADIUS * math.sin(ang),
                base_z,
            ))

        for r_idx in range(1, DOME_RINGS + 1):
            phi = (math.pi / 2) * (r_idx / DOME_RINGS)
            rr = DOME_RADIUS * math.cos(phi)
            z = base_z + DOME_RADIUS * math.sin(phi)
            curr: list[int] = []
            for k in range(DOME_SEGMENTS):
                ang = 2 * math.pi * k / DOME_SEGMENTS
                curr.append(mesh.add_vertex(cx + rr * math.cos(ang),
                                            cy + rr * math.sin(ang),
                                            z))
            for k in range(DOME_SEGMENTS):
                kp = (k + 1) % DOME_SEGMENTS
                mesh.add_quad(
                    p0=_vp(mesh, prev_ring[k]),
                    p1=_vp(mesh, curr[k]),
                    p2=_vp(mesh, curr[kp]),
                    p3=_vp(mesh, prev_ring[kp]),
                    role="ChurchDome",
                    surface_id=f"{pid}.dome.{r_idx}.{k}",
                    material_key="dome_lead",
                )
            prev_ring = curr

    def _emit_lantern(self, mesh: BuildingMesh, ring) -> None:
        pid = mesh.parcel_id
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        base_z = DRUM_BASE_Z + DRUM_HEIGHT + DOME_RADIUS
        top_z = base_z + LANTERN_HEIGHT
        # Octagonal lantern drum
        segs = 8
        lower: list[int] = []
        upper: list[int] = []
        for k in range(segs):
            ang = 2 * math.pi * k / segs
            lower.append(mesh.add_vertex(cx + LANTERN_RADIUS * math.cos(ang),
                                         cy + LANTERN_RADIUS * math.sin(ang), base_z))
            upper.append(mesh.add_vertex(cx + LANTERN_RADIUS * math.cos(ang),
                                         cy + LANTERN_RADIUS * math.sin(ang), top_z))
        for k in range(segs):
            kp = (k + 1) % segs
            mesh.add_quad(
                p0=_vp(mesh, lower[k]), p1=_vp(mesh, upper[k]),
                p2=_vp(mesh, upper[kp]), p3=_vp(mesh, lower[kp]),
                role="ChurchBody",
                surface_id=f"{pid}.lantern.side.{k}",
                material_key="wall_main",
            )
        # Pointed cap (cone)
        apex = mesh.add_vertex(cx, cy, top_z + 0.8)
        for k in range(segs):
            kp = (k + 1) % segs
            mesh.add_face(
                [upper[k], apex, upper[kp]],
                role="RoofSurface",
                surface_id=f"{pid}.lantern.cap.{k}",
                material_key="dome_lead",
            )

    def _emit_clocher(self, mesh: BuildingMesh, ring) -> None:
        pid = mesh.parcel_id
        poly = Polygon(ring)
        minx, miny, maxx, maxy = poly.bounds
        cx = (minx + maxx) / 2 - 2.5
        cy = miny - CLOCHER_SIDE / 2 - 0.5
        half = CLOCHER_SIDE / 2
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
        # Open belfry arches at the top — glass inserts.
        belfry_bot = CLOCHER_HEIGHT - 2.5
        belfry_top = CLOCHER_HEIGHT - 0.5
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            ax = a[0] + (b[0] - a[0]) * 0.2
            ay = a[1] + (b[1] - a[1]) * 0.2
            bx = a[0] + (b[0] - a[0]) * 0.8
            by = a[1] + (b[1] - a[1]) * 0.8
            mesh.add_quad(
                p0=(ax, ay, belfry_bot),
                p1=(ax, ay, belfry_top),
                p2=(bx, by, belfry_top),
                p3=(bx, by, belfry_bot),
                role="Window",
                surface_id=f"{pid}.belfry.{i}",
                material_key="window_glass",
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
