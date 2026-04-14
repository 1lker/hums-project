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
DRUM_HEIGHT = 4.2
DRUM_RADIUS = 4.0
DOME_RADIUS = 4.2
DOME_SEGMENTS = 36            # bumped for a smoother silhouette
DOME_RINGS = 16
LANTERN_HEIGHT = 2.2
LANTERN_RADIUS = 0.75
LANTERN_SEGMENTS = 8
CLOCHER_BASE_STOREY = 4.5     # lower stone storey
CLOCHER_BELFRY_H = 3.0        # octagonal belfry with arched openings
CLOCHER_PEAK_H = 4.5          # tall pyramidal cap
CLOCHER_FINIAL_H = 1.2


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
        self._emit_clocher_from_w39_1(mesh, c.x, c.y)
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

    def _emit_clocher_from_w39_1(self, mesh: BuildingMesh, church_cx: float, church_cy: float) -> None:
        """Position the clocher using the W-39/1 traced polygon's footprint.

        The `church-entrence-camli-area-(39-1*39-2)-with-clocher.kml` polygon
        contains BOTH the camli vestibule and the bell tower's physical base.
        We find that polygon, take the sub-region closest to the church,
        and place a slender octagonal tower on its centroid so it lands
        exactly where the 1923 Pervititch map shows it.
        """
        clocher_poly = _load_w39_1_polygon()
        if clocher_poly is None:
            # fall back to old behaviour if the data moves
            return
        # The W-39/1 polygon includes camli + clocher; the clocher sits at the
        # portion closest to the church body. Approximate that as a bounding
        # rectangle corner closest to (church_cx, church_cy).
        bx0, by0, bx1, by1 = clocher_poly.bounds
        candidates = [(bx0, by0), (bx0, by1), (bx1, by0), (bx1, by1)]
        nx, ny = min(candidates, key=lambda p: (p[0] - church_cx) ** 2 + (p[1] - church_cy) ** 2)
        # Pull a little back from the corner so the tower sits ON the polygon.
        inset = 1.3
        cx = nx + (clocher_poly.centroid.x - nx) * (inset / max(0.1, math.hypot(clocher_poly.centroid.x - nx,
                                                                                  clocher_poly.centroid.y - ny)))
        cy = ny + (clocher_poly.centroid.y - ny) * (inset / max(0.1, math.hypot(clocher_poly.centroid.x - nx,
                                                                                  clocher_poly.centroid.y - ny)))
        # Local coords around the church centroid (stored in church mesh).
        cx -= church_cx
        cy -= church_cy
        self._emit_tall_clocher(mesh, cx, cy)

    def _emit_tall_clocher(self, mesh: BuildingMesh, cx: float, cy: float) -> None:
        """Three-stage clocher: stone base → octagonal belfry → spire + finial."""
        pid = mesh.parcel_id
        base_side = 3.0
        belfry_radius = 1.7

        # -- Stage 1: square stone base
        half = base_side / 2
        corners = [
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        ]
        top_base_z = CLOCHER_BASE_STOREY + 0.6  # extra height before belfry
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            mesh.add_quad(
                p0=(a[0], a[1], 0.0),
                p1=(a[0], a[1], top_base_z),
                p2=(b[0], b[1], top_base_z),
                p3=(b[0], b[1], 0.0),
                role="Clocher",
                surface_id=f"{pid}.clocher.base.{i}",
                material_key="wall_main",
            )
        # cornice around the base (protruding band)
        band_proj = 0.12
        band_h = 0.35
        band_top = top_base_z
        band_bot = top_base_z - band_h
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            ux = (b[0] - a[0]) / length
            uy = (b[1] - a[1]) / length
            nx_, ny_ = -uy, ux  # outward for CCW square
            mesh.add_quad(
                p0=(a[0] + nx_ * band_proj, a[1] + ny_ * band_proj, band_bot),
                p1=(a[0] + nx_ * band_proj, a[1] + ny_ * band_proj, band_top),
                p2=(b[0] + nx_ * band_proj, b[1] + ny_ * band_proj, band_top),
                p3=(b[0] + nx_ * band_proj, b[1] + ny_ * band_proj, band_bot),
                role="CorniceSurface",
                surface_id=f"{pid}.clocher.cornice.{i}",
                material_key="cornice_paint",
            )

        # -- Stage 2: octagonal belfry with arched openings
        seg = 8
        lower_ring: list[int] = []
        upper_ring: list[int] = []
        belfry_bot = top_base_z
        belfry_top = top_base_z + CLOCHER_BELFRY_H
        for k in range(seg):
            ang = (math.pi / seg) + 2 * math.pi * k / seg  # rotated 22.5° so flats face cardinals
            x = cx + belfry_radius * math.cos(ang)
            y = cy + belfry_radius * math.sin(ang)
            lower_ring.append(mesh.add_vertex(x, y, belfry_bot))
            upper_ring.append(mesh.add_vertex(x, y, belfry_top))
        for k in range(seg):
            kp = (k + 1) % seg
            mesh.add_quad(
                p0=_vp(mesh, lower_ring[k]), p1=_vp(mesh, upper_ring[k]),
                p2=_vp(mesh, upper_ring[kp]), p3=_vp(mesh, lower_ring[kp]),
                role="Clocher",
                surface_id=f"{pid}.clocher.belfry.side.{k}",
                material_key="wall_main",
            )
        # Arched glass openings inset on 4 alternating faces
        for k in range(0, seg, 2):
            kp = (k + 1) % seg
            a = _vp(mesh, lower_ring[k])
            b = _vp(mesh, lower_ring[kp])
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            ux = (b[0] - a[0]) / length
            uy = (b[1] - a[1]) / length
            # inset 0.15 and narrow 20% on each side
            margin = length * 0.2
            ax = a[0] + ux * margin
            ay = a[1] + uy * margin
            bx = a[0] + ux * (length - margin)
            by = a[1] + uy * (length - margin)
            # outward normal (rotate (ux,uy) -90° → (uy,-ux)) for CCW outside
            nx_ = uy
            ny_ = -ux
            ax += nx_ * 0.02; ay += ny_ * 0.02
            bx += nx_ * 0.02; by += ny_ * 0.02
            opening_bot = belfry_bot + 0.3
            opening_top = belfry_top - 0.6
            arch_apex_z = opening_top + 0.5
            mid_x = (ax + bx) / 2
            mid_y = (ay + by) / 2
            # Rectangle part
            mesh.add_quad(
                p0=(ax, ay, opening_bot), p1=(ax, ay, opening_top),
                p2=(bx, by, opening_top), p3=(bx, by, opening_bot),
                role="Window",
                surface_id=f"{pid}.clocher.arch.{k}.rect",
                material_key="window_glass",
            )
            # Arch triangle
            top_l = mesh.add_vertex(ax, ay, opening_top)
            top_r = mesh.add_vertex(bx, by, opening_top)
            apex = mesh.add_vertex(mid_x, mid_y, arch_apex_z)
            mesh.add_face([top_l, apex, top_r], role="Window",
                          surface_id=f"{pid}.clocher.arch.{k}.tri",
                          material_key="window_glass")

        # -- Stage 3: spire + finial
        spire_base_z = belfry_top
        spire_apex_z = spire_base_z + CLOCHER_PEAK_H
        apex = mesh.add_vertex(cx, cy, spire_apex_z)
        for k in range(seg):
            kp = (k + 1) % seg
            mesh.add_face(
                [upper_ring[k], apex, upper_ring[kp]],
                role="RoofSurface",
                surface_id=f"{pid}.clocher.spire.{k}",
                material_key="dome_lead",
            )
        # Finial (cross-shaped): simplified as a small vertical rod + horizontal bar
        fin_base_z = spire_apex_z
        fin_top_z = fin_base_z + CLOCHER_FINIAL_H
        rod_r = 0.06
        # Vertical shaft
        for k in range(4):
            ang0 = 2 * math.pi * k / 4
            ang1 = 2 * math.pi * (k + 1) / 4
            x0 = cx + rod_r * math.cos(ang0); y0 = cy + rod_r * math.sin(ang0)
            x1 = cx + rod_r * math.cos(ang1); y1 = cy + rod_r * math.sin(ang1)
            mesh.add_quad(
                p0=(x0, y0, fin_base_z), p1=(x0, y0, fin_top_z),
                p2=(x1, y1, fin_top_z), p3=(x1, y1, fin_base_z),
                role="RoofSurface",
                surface_id=f"{pid}.clocher.finial.shaft.{k}",
                material_key="dome_lead",
            )
        # Crossbar
        cb_z = fin_base_z + CLOCHER_FINIAL_H * 0.55
        cb_h = 0.08
        cb_w = 0.35
        mesh.add_quad(
            p0=(cx - cb_w, cy - rod_r, cb_z),
            p1=(cx - cb_w, cy - rod_r, cb_z + cb_h),
            p2=(cx + cb_w, cy - rod_r, cb_z + cb_h),
            p3=(cx + cb_w, cy - rod_r, cb_z),
            role="RoofSurface",
            surface_id=f"{pid}.clocher.finial.cross",
            material_key="dome_lead",
        )


def _load_w39_1_polygon() -> Polygon | None:
    """Find the W-39/1 polygon in footprints.geojson."""
    from ...common.paths import FOOTPRINTS_GEOJSON
    if not FOOTPRINTS_GEOJSON.exists():
        return None
    fc = json.loads(FOOTPRINTS_GEOJSON.read_text())
    for f in fc["features"]:
        if "W-39/1" in (f["properties"].get("parcel_ids_matched") or []):
            return shape(f["geometry"])
    return None


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
