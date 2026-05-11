"""PRD-004 · Track C — Ayia Eftimia church + clocher + kubbe.

Orthodox cruciform basilica model:

  1. Nave body — extruded footprint with a *low* (near-flat) hip roof so the
     central dome reads as the dominant mass.
  2. Low kubbe curb — a shallow drum/collar sitting on the roof.
  3. Kubbe — low lead/zinc cap with three small glazed marks from the map.
  4. Plinth band — stone skirting around the body base.
  5. Clocher — tall bell tower on the map-marked lower-right church corner.
"""
from __future__ import annotations
import json
import math

from shapely.geometry import Point, Polygon, shape
from shapely.ops import nearest_points

from ...common.paths import NON_PARCEL_FOOTPRINTS_GEOJSON
from ...common.prd import prd
from ...modeling.building import FacadePalette
from ..mesh_graph import BuildingMesh


BODY_HEIGHT = 8.0
PLINTH_HEIGHT = 0.8
BODY_WINDOW_SILL = 2.35
BODY_WINDOW_RECT_H = 2.15
BODY_WINDOW_W = 1.15
BODY_WINDOW_ARCH_RISE = 0.58
BODY_WINDOW_ARCH_SEGMENTS = 8
DRUM_BASE_Z = BODY_HEIGHT + 0.28
DRUM_HEIGHT = 0.68
DRUM_RADIUS = 3.55
DOME_RADIUS = 3.65
DOME_RISE = 1.08
DOME_SEGMENTS = 36            # bumped for a smoother silhouette
DOME_RINGS = 10
LANTERN_HEIGHT = 2.2
LANTERN_RADIUS = 0.75
LANTERN_SEGMENTS = 8
DOME_MAP_CENTER_UTM = (670342.95, 4539707.85)
CLOCHER_BASE_STOREY = 7.0     # lower stone storey
CLOCHER_BELFRY_H = 5.2        # tall belfry with arched openings
CLOCHER_PEAK_H = 3.0          # dark faceted lead cap
CLOCHER_FINIAL_H = 1.1
CLOCHER_MAP_CENTER_UTM = (670344.747, 4539694.161)
CLOCHER_MAP_ROTATION_DEG = -18.4


STONE_PALETTE = FacadePalette(
    wall_main=(216, 204, 179),
    wall_accent=(196, 182, 156),
    trim=(120, 100, 80),
    roof=(84, 88, 88),
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
        dome_center_utm, dome_source = _dome_center_utm(poly)
        dome_center_local = (dome_center_utm[0] - c.x, dome_center_utm[1] - c.y)

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
                "dome_center_source": dome_source,
                "dome_center_utm": tuple(round(v, 3) for v in dome_center_utm),
                "dome_center_shift_m": (
                    round(dome_center_utm[0] - c.x, 3),
                    round(dome_center_utm[1] - c.y, 3),
                ),
                "dome_form": (
                    "low shallow kubbe cap with three small glazed openings; "
                    "map reread does not support a high raised drum/lantern"
                ),
            },
        )

        self._emit_plinth(mesh, ring_local)
        self._emit_body(mesh, ring_local)
        self._emit_body_windows(mesh, ring_local)
        self._emit_low_tile_roof(mesh, ring_local, dome_center_local)
        self._emit_drum(mesh, dome_center_local)
        self._emit_kubbe(mesh, dome_center_local)
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

    def _emit_body_windows(self, mesh: BuildingMesh, ring) -> None:
        """Tall arched nave windows on the exposed long church body faces.

        The Pervititch footprint does not enumerate individual panes, but the
        church body is not a blank masonry block. We keep this conservative:
        only long exterior runs receive narrow arched church windows. The
        lower-left run touching the W-39/1 wooden church-edge annex is an
        internal/service side and is rendered as interior doors instead.
        """
        pid = mesh.parcel_id
        if len(ring) < 3:
            return
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        z0 = BODY_WINDOW_SILL
        spring_z = BODY_WINDOW_SILL + BODY_WINDOW_RECT_H
        trim_w = 0.10

        for idx in range(len(ring)):
            a = ring[idx]
            b = ring[(idx + 1) % len(ring)]
            dx = b[0] - a[0]
            dy = b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 6.0:
                continue

            ux = dx / length
            uy = dy / length
            mx = (a[0] + b[0]) / 2
            my = (a[1] + b[1]) / 2
            count = _church_body_opening_count(idx, mid=(mx, my), length=length)
            nx, ny = -uy, ux
            if (mx - cx) * nx + (my - cy) * ny < 0:
                nx, ny = -nx, -ny

            wood_annex_side = _is_wooden_annex_side(mid=(mx, my), length=length)
            for win_idx in range(count):
                center_u = length * (win_idx + 1) / (count + 1)
                u0 = max(0.35, center_u - BODY_WINDOW_W / 2)
                u1 = min(length - 0.35, center_u + BODY_WINDOW_W / 2)
                if u1 - u0 < BODY_WINDOW_W * 0.65:
                    continue
                if wood_annex_side:
                    self._emit_internal_annex_door(
                        mesh, pid, idx, win_idx, a, ux, uy, nx, ny, u0, u1
                    )
                    continue
                self._emit_arched_body_window(
                    mesh, pid, idx, win_idx, a, ux, uy, nx, ny, u0, u1, z0, spring_z, trim_w
                )
        mesh.metadata["church_body_windows"] = (
            "arched windows on exposed nave faces; left church side corrected "
            "to 2 far-left street panes + 3 panes above W-32 mini magazines; "
            "W-39/1 wooden-annex side uses interior/service doors instead of "
            "glass windows"
        )

    def _emit_internal_annex_door(
        self,
        mesh: BuildingMesh,
        pid: str,
        seg_idx: int,
        door_idx: int,
        start: tuple[float, float],
        ux: float,
        uy: float,
        nx: float,
        ny: float,
        u0: float,
        u1: float,
    ) -> None:
        z0 = PLINTH_HEIGHT + 0.10
        z1 = 2.58
        trim_w = 0.12

        def p(u: float, z: float, out: float = 0.058) -> tuple[float, float, float]:
            return (
                start[0] + ux * u + nx * out,
                start[1] + uy * u + ny * out,
                z,
            )

        sid = f"{pid}.internal_annex_door.{seg_idx}.{door_idx}"
        mesh.add_quad(
            p0=p(u0, z0),
            p1=p(u0, z1),
            p2=p(u1, z1),
            p3=p(u1, z0),
            role="Door",
            surface_id=f"{sid}.panel",
            material_key="church_panel_shadow",
        )
        mesh.add_quad(
            p0=p(u0 + 0.04, z0 + 0.10, 0.065),
            p1=p(u0 + 0.04, z1 - 0.14, 0.065),
            p2=p(u0 + 0.09, z1 - 0.14, 0.065),
            p3=p(u0 + 0.09, z0 + 0.10, 0.065),
            role="Mullion",
            surface_id=f"{sid}.left_raised_panel",
            material_key="church_stone_shadow",
        )
        mesh.add_quad(
            p0=p(u1 - 0.09, z0 + 0.10, 0.065),
            p1=p(u1 - 0.09, z1 - 0.14, 0.065),
            p2=p(u1 - 0.04, z1 - 0.14, 0.065),
            p3=p(u1 - 0.04, z0 + 0.10, 0.065),
            role="Mullion",
            surface_id=f"{sid}.right_raised_panel",
            material_key="church_stone_shadow",
        )
        mesh.add_quad(
            p0=p((u0 + u1) / 2 - 0.018, z0 + 0.10, 0.068),
            p1=p((u0 + u1) / 2 - 0.018, z1 - 0.10, 0.068),
            p2=p((u0 + u1) / 2 + 0.018, z1 - 0.10, 0.068),
            p3=p((u0 + u1) / 2 + 0.018, z0 + 0.10, 0.068),
            role="Mullion",
            surface_id=f"{sid}.center_seam",
            material_key="church_stone_shadow",
        )
        for side, a0, a1 in (
            ("L", u0 - trim_w, u0),
            ("R", u1, u1 + trim_w),
        ):
            mesh.add_quad(
                p0=p(a0, z0 - 0.02, 0.075),
                p1=p(a0, z1 + 0.05, 0.075),
                p2=p(a1, z1 + 0.05, 0.075),
                p3=p(a1, z0 - 0.02, 0.075),
                role="JambSurface",
                surface_id=f"{sid}.jamb.{side}",
                material_key="church_stone_light",
            )
        mesh.add_quad(
            p0=p(u0 - trim_w, z1, 0.075),
            p1=p(u0 - trim_w, z1 + 0.16, 0.075),
            p2=p(u1 + trim_w, z1 + 0.16, 0.075),
            p3=p(u1 + trim_w, z1, 0.075),
            role="HeaderSurface",
            surface_id=f"{sid}.lintel",
            material_key="church_stone_light",
        )

    def _emit_arched_body_window(
        self,
        mesh: BuildingMesh,
        pid: str,
        seg_idx: int,
        win_idx: int,
        start: tuple[float, float],
        ux: float,
        uy: float,
        nx: float,
        ny: float,
        u0: float,
        u1: float,
        z0: float,
        spring_z: float,
        trim_w: float,
    ) -> None:
        def p(u: float, z: float, out: float = 0.035) -> tuple[float, float, float]:
            return (
                start[0] + ux * u + nx * out,
                start[1] + uy * u + ny * out,
                z,
            )

        sid = f"{pid}.body_window.{seg_idx}.{win_idx}"
        trim_out = 0.065
        mesh.add_quad(
            p0=p(u0, z0),
            p1=p(u0, spring_z),
            p2=p(u1, spring_z),
            p3=p(u1, z0),
            role="Window",
            surface_id=f"{sid}.glass.rect",
            material_key="window_glass",
        )
        # Semicircular arched glass above the spring line.
        for s in range(BODY_WINDOW_ARCH_SEGMENTS):
            t0 = s / BODY_WINDOW_ARCH_SEGMENTS
            t1 = (s + 1) / BODY_WINDOW_ARCH_SEGMENTS
            ua = u0 + (u1 - u0) * t0
            ub = u0 + (u1 - u0) * t1
            za = spring_z + BODY_WINDOW_ARCH_RISE * math.sin(math.pi * t0)
            zb = spring_z + BODY_WINDOW_ARCH_RISE * math.sin(math.pi * t1)
            mesh.add_quad(
                p0=p(ua, spring_z),
                p1=p(ua, za),
                p2=p(ub, zb),
                p3=p(ub, spring_z),
                role="Window",
                surface_id=f"{sid}.glass.arch.{s}",
                material_key="window_glass",
            )

        # Stone surround: sill, side jambs, and a simple spring-course header.
        mesh.add_quad(
            p0=p(u0 - trim_w, z0 - 0.12, trim_out),
            p1=p(u0 - trim_w, z0, trim_out),
            p2=p(u1 + trim_w, z0, trim_out),
            p3=p(u1 + trim_w, z0 - 0.12, trim_out),
            role="SillSurface",
            surface_id=f"{sid}.sill",
            material_key="trim",
        )
        mesh.add_quad(
            p0=p(u0 - trim_w, z0, trim_out),
            p1=p(u0 - trim_w, spring_z, trim_out),
            p2=p(u0, spring_z, trim_out),
            p3=p(u0, z0, trim_out),
            role="JambSurface",
            surface_id=f"{sid}.jamb.L",
            material_key="trim",
        )
        mesh.add_quad(
            p0=p(u1, z0, trim_out),
            p1=p(u1, spring_z, trim_out),
            p2=p(u1 + trim_w, spring_z, trim_out),
            p3=p(u1 + trim_w, z0, trim_out),
            role="JambSurface",
            surface_id=f"{sid}.jamb.R",
            material_key="trim",
        )
        mesh.add_quad(
            p0=p(u0 - trim_w, spring_z, trim_out),
            p1=p(u0 - trim_w, spring_z + 0.12, trim_out),
            p2=p(u1 + trim_w, spring_z + 0.12, trim_out),
            p3=p(u1 + trim_w, spring_z, trim_out),
            role="HeaderSurface",
            surface_id=f"{sid}.spring_course",
            material_key="trim",
        )
        mid = (u0 + u1) / 2
        mesh.add_quad(
            p0=p(mid - 0.025, z0 + 0.15, trim_out + 0.002),
            p1=p(mid - 0.025, spring_z - 0.05, trim_out + 0.002),
            p2=p(mid + 0.025, spring_z - 0.05, trim_out + 0.002),
            p3=p(mid + 0.025, z0 + 0.15, trim_out + 0.002),
            role="Mullion",
            surface_id=f"{sid}.mullion",
            material_key="trim",
        )

    def _emit_low_tile_roof(self, mesh: BuildingMesh, ring, dome_center) -> None:
        """Continuous low kiremit roof with a lead flashing collar.

        The Pervititch sheet and historical descriptions both read as a tiled
        masonry church roof with the central kubbe as the dominant element.
        Keep the body roof low, but make it continuous so no gaps appear around
        the drum in glTF viewers.
        """
        pid = mesh.parcel_id
        cx, cy = dome_center
        roof_peak_z = BODY_HEIGHT + 0.32
        center = mesh.add_vertex(cx, cy, roof_peak_z)
        for i in range(len(ring)):
            a = ring[i]
            b = ring[(i + 1) % len(ring)]
            ia = mesh.add_vertex(a[0], a[1], BODY_HEIGHT)
            ib = mesh.add_vertex(b[0], b[1], BODY_HEIGHT)
            mesh.add_face([ia, center, ib], role="RoofSurface",
                          surface_id=f"{pid}.roof.tile.{i}",
                          material_key="tile_terracotta")

        # Lead/zinc flashing collar where the low kubbe curb meets the roof.
        outer: list[int] = []
        inner: list[int] = []
        collar_outer_r = DRUM_RADIUS * 1.08
        for k in range(DOME_SEGMENTS):
            ang = 2 * math.pi * k / DOME_SEGMENTS
            outer.append(mesh.add_vertex(cx + collar_outer_r * math.cos(ang),
                                         cy + collar_outer_r * math.sin(ang),
                                         roof_peak_z + 0.03))
            inner.append(mesh.add_vertex(cx + DRUM_RADIUS * math.cos(ang),
                                         cy + DRUM_RADIUS * math.sin(ang),
                                         DRUM_BASE_Z))
        for k in range(DOME_SEGMENTS):
            kp = (k + 1) % DOME_SEGMENTS
            mesh.add_face([outer[k], inner[k], inner[kp], outer[kp]],
                          role="RoofSurface",
                          surface_id=f"{pid}.roof.flashing.{k}",
                          material_key="dome_lead")

    def _emit_drum(self, mesh: BuildingMesh, dome_center) -> None:
        pid = mesh.parcel_id
        cx, cy = dome_center
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
        # Map reread: only three small glazed marks around the low kubbe,
        # not a full elevated clerestory band.
        band_bot = DRUM_BASE_Z + 0.14
        band_top = min(top_z - 0.08, band_bot + 0.36)
        for win_idx, center_deg in enumerate((18.0, 138.0, 258.0)):
            span_deg = 18.0
            ang0 = math.radians(center_deg - span_deg / 2.0)
            ang1 = math.radians(center_deg + span_deg / 2.0)
            rr = DRUM_RADIUS - 0.06
            x0, y0 = cx + rr * math.cos(ang0), cy + rr * math.sin(ang0)
            x1, y1 = cx + rr * math.cos(ang1), cy + rr * math.sin(ang1)
            mesh.add_quad(
                p0=(x0, y0, band_bot),
                p1=(x0, y0, band_top),
                p2=(x1, y1, band_top),
                p3=(x1, y1, band_bot),
                role="Window",
                surface_id=f"{pid}.kubbe.low_glazed_mark.{win_idx}",
                material_key="window_glass",
            )

    def _emit_kubbe(self, mesh: BuildingMesh, dome_center) -> None:
        pid = mesh.parcel_id
        cx, cy = dome_center
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
            z = base_z + DOME_RISE * math.sin(phi)
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

    def _emit_lantern(self, mesh: BuildingMesh, dome_center) -> None:
        pid = mesh.parcel_id
        cx, cy = dome_center
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
        We find that polygon, take the traced edge that touches the church,
        and place a slender octagonal tower just inside that edge so it lands
        where the 1923 Pervititch map labels "Clocher".
        """
        clocher_poly = _load_w39_1_polygon()
        if clocher_poly is None:
            # fall back to old behaviour if the data moves
            return
        church_poly = _load_church_polygon()
        if church_poly is None:
            return

        # The map shows a distinct small square with the "Clocher" label at
        # the south-east / lower-right edge of the church complex. The W-39/1
        # footprint covers the whole camli/clocher porch, so the tower center
        # must be pinned to that visible square, not to W-39/1's centroid or
        # nearest boundary point.
        map_center = Point(*CLOCHER_MAP_CENTER_UTM)
        if clocher_poly.buffer(0.2).contains(map_center):
            cx, cy = CLOCHER_MAP_CENTER_UTM
            anchor_utm = CLOCHER_MAP_CENTER_UTM
            source = "Pervititch raster clocher square within W-39/1"
        else:
            # Fallback if the source footprint is retraced later.
            _, anchor = nearest_points(church_poly.boundary, clocher_poly.boundary)
            nx, ny = anchor.x, anchor.y
            inset = 1.3
            center_target = clocher_poly.centroid
            anchor_to_center = math.hypot(center_target.x - nx, center_target.y - ny)
            cx = nx + (center_target.x - nx) * (inset / max(0.1, anchor_to_center))
            cy = ny + (center_target.y - ny) * (inset / max(0.1, anchor_to_center))
            anchor_utm = (nx, ny)
            source = "fallback W-39/1 nearest church-edge clocher/camli footprint"

        mesh.metadata["clocher_source"] = source
        mesh.metadata["clocher_anchor_utm"] = tuple(round(v, 3) for v in anchor_utm)
        mesh.metadata["clocher_center_utm"] = (round(cx, 3), round(cy, 3))
        mesh.metadata["clocher_rotation_deg"] = CLOCHER_MAP_ROTATION_DEG
        mesh.metadata["clocher_top_m"] = round(
            CLOCHER_BASE_STOREY + 0.6 + CLOCHER_BELFRY_H + CLOCHER_PEAK_H + CLOCHER_FINIAL_H,
            2,
        )
        # Local coords around the church centroid (stored in church mesh).
        cx -= church_cx
        cy -= church_cy
        self._emit_tall_clocher(mesh, cx, cy)

    def _emit_tall_clocher(self, mesh: BuildingMesh, cx: float, cy: float) -> None:
        """Photo-informed clocher: stone shaft -> arched belfry -> dark lead cap."""
        pid = mesh.parcel_id
        base_side = 3.15
        belfry_radius = 1.72
        rotation = math.radians(CLOCHER_MAP_ROTATION_DEG)
        ux = math.cos(rotation)
        uy = math.sin(rotation)
        vx = -math.sin(rotation)
        vy = math.cos(rotation)

        half = base_side / 2
        corners = [
            (cx - ux * half - vx * half, cy - uy * half - vy * half),
            (cx + ux * half - vx * half, cy + uy * half - vy * half),
            (cx + ux * half + vx * half, cy + uy * half + vy * half),
            (cx - ux * half + vx * half, cy - uy * half + vy * half),
        ]
        top_base_z = CLOCHER_BASE_STOREY + 0.6
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            ex = (b[0] - a[0]) / length
            ey = (b[1] - a[1]) / length
            nx_, ny_ = -ey, ex
            mesh.add_quad(
                p0=(a[0], a[1], 0.0),
                p1=(a[0], a[1], top_base_z),
                p2=(b[0], b[1], top_base_z),
                p3=(b[0], b[1], 0.0),
                role="Clocher",
                surface_id=f"{pid}.clocher.base.{i}",
                material_key="wall_main",
            )
            for edge_name, t0, t1 in (("left", 0.06, 0.18), ("right", 0.82, 0.94)):
                p0 = (a[0] + ex * length * t0 + nx_ * 0.035, a[1] + ey * length * t0 + ny_ * 0.035)
                p1 = (a[0] + ex * length * t1 + nx_ * 0.035, a[1] + ey * length * t1 + ny_ * 0.035)
                mesh.add_quad(
                    p0=(p0[0], p0[1], 1.0),
                    p1=(p0[0], p0[1], top_base_z - 0.55),
                    p2=(p1[0], p1[1], top_base_z - 0.55),
                    p3=(p1[0], p1[1], 1.0),
                    role="JambSurface",
                    surface_id=f"{pid}.clocher.base.pilaster.{i}.{edge_name}",
                    material_key="church_stone_light",
                )
            mesh.add_quad(
                p0=(a[0] + nx_ * 0.025, a[1] + ny_ * 0.025, 1.15),
                p1=(a[0] + nx_ * 0.025, a[1] + ny_ * 0.025, 1.35),
                p2=(b[0] + nx_ * 0.025, b[1] + ny_ * 0.025, 1.35),
                p3=(b[0] + nx_ * 0.025, b[1] + ny_ * 0.025, 1.15),
                role="StringcourseSurface",
                surface_id=f"{pid}.clocher.base.lower_band.{i}",
                material_key="church_stone_shadow",
            )

        band_proj = 0.18
        band_h = 0.42
        band_top = top_base_z
        band_bot = top_base_z - band_h
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            ex = (b[0] - a[0]) / length
            ey = (b[1] - a[1]) / length
            nx_, ny_ = -ey, ex
            mesh.add_quad(
                p0=(a[0] + nx_ * band_proj, a[1] + ny_ * band_proj, band_bot),
                p1=(a[0] + nx_ * band_proj, a[1] + ny_ * band_proj, band_top),
                p2=(b[0] + nx_ * band_proj, b[1] + ny_ * band_proj, band_top),
                p3=(b[0] + nx_ * band_proj, b[1] + ny_ * band_proj, band_bot),
                role="CorniceSurface",
                surface_id=f"{pid}.clocher.cornice.{i}",
                material_key="cornice_paint",
            )
            mesh.add_quad(
                p0=(a[0] + nx_ * (band_proj + 0.02), a[1] + ny_ * (band_proj + 0.02), band_bot - 0.12),
                p1=(a[0] + nx_ * (band_proj + 0.02), a[1] + ny_ * (band_proj + 0.02), band_bot),
                p2=(b[0] + nx_ * (band_proj + 0.02), b[1] + ny_ * (band_proj + 0.02), band_bot),
                p3=(b[0] + nx_ * (band_proj + 0.02), b[1] + ny_ * (band_proj + 0.02), band_bot - 0.12),
                role="CorniceSurface",
                surface_id=f"{pid}.clocher.cornice.dark_underside.{i}",
                material_key="church_iron_dark",
            )

        seg = 8
        lower_ring: list[int] = []
        upper_ring: list[int] = []
        belfry_bot = top_base_z
        belfry_top = top_base_z + CLOCHER_BELFRY_H
        for k in range(seg):
            ang = rotation + (math.pi / seg) + 2 * math.pi * k / seg
            lower_ring.append(mesh.add_vertex(
                cx + belfry_radius * math.cos(ang),
                cy + belfry_radius * math.sin(ang),
                belfry_bot,
            ))
            upper_ring.append(mesh.add_vertex(
                cx + belfry_radius * math.cos(ang),
                cy + belfry_radius * math.sin(ang),
                belfry_top,
            ))
        for k in range(seg):
            kp = (k + 1) % seg
            mesh.add_quad(
                p0=_vp(mesh, lower_ring[k]), p1=_vp(mesh, upper_ring[k]),
                p2=_vp(mesh, upper_ring[kp]), p3=_vp(mesh, lower_ring[kp]),
                role="Clocher",
                surface_id=f"{pid}.clocher.belfry.side.{k}",
                material_key="church_stone_light" if k % 2 else "wall_main",
            )

        for k in range(0, seg, 2):
            kp = (k + 1) % seg
            a = _vp(mesh, lower_ring[k])
            b = _vp(mesh, lower_ring[kp])
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            ex = (b[0] - a[0]) / length
            ey = (b[1] - a[1]) / length
            margin = length * 0.23
            ax = a[0] + ex * margin
            ay = a[1] + ey * margin
            bx = a[0] + ex * (length - margin)
            by = a[1] + ey * (length - margin)
            nx_, ny_ = ey, -ex
            ax += nx_ * 0.03
            ay += ny_ * 0.03
            bx += nx_ * 0.03
            by += ny_ * 0.03
            opening_bot = belfry_bot + 0.75
            opening_top = belfry_top - 1.18
            arch_apex_z = opening_top + 0.72
            mid_x = (ax + bx) / 2
            mid_y = (ay + by) / 2
            mesh.add_quad(
                p0=(ax, ay, opening_bot),
                p1=(ax, ay, opening_top),
                p2=(bx, by, opening_top),
                p3=(bx, by, opening_bot),
                role="Window",
                surface_id=f"{pid}.clocher.arch.{k}.rect",
                material_key="church_iron_dark",
            )
            top_l = mesh.add_vertex(ax, ay, opening_top)
            top_r = mesh.add_vertex(bx, by, opening_top)
            apex = mesh.add_vertex(mid_x, mid_y, arch_apex_z)
            mesh.add_face(
                [top_l, apex, top_r],
                role="Window",
                surface_id=f"{pid}.clocher.arch.{k}.tri",
                material_key="church_iron_dark",
            )
            trim_w = min(0.16, length * 0.08)
            for name, q0, q1 in (("left", -trim_w, 0.0), ("right", length - margin * 2, length - margin * 2 + trim_w)):
                x0 = ax + ex * q0
                y0 = ay + ey * q0
                x1 = ax + ex * q1
                y1 = ay + ey * q1
                mesh.add_quad(
                    p0=(x0, y0, opening_bot - 0.18),
                    p1=(x0, y0, opening_top + 0.12),
                    p2=(x1, y1, opening_top + 0.12),
                    p3=(x1, y1, opening_bot - 0.18),
                    role="JambSurface",
                    surface_id=f"{pid}.clocher.arch.{k}.jamb.{name}",
                    material_key="church_stone_shadow",
                )
            mesh.add_quad(
                p0=(ax - ex * trim_w, ay - ey * trim_w, opening_bot - 0.18),
                p1=(ax - ex * trim_w, ay - ey * trim_w, opening_bot + 0.02),
                p2=(bx + ex * trim_w, by + ey * trim_w, opening_bot + 0.02),
                p3=(bx + ex * trim_w, by + ey * trim_w, opening_bot - 0.18),
                role="SillSurface",
                surface_id=f"{pid}.clocher.arch.{k}.sill",
                material_key="church_stone_shadow",
            )
            self._emit_clocher_bell(mesh, pid, k, mid_x, mid_y, ex, ey, nx_, ny_, opening_bot + 0.82)

        rail_bot = belfry_top - 0.22
        rail_top = belfry_top + 0.28
        for k in range(seg):
            kp = (k + 1) % seg
            a = _vp(mesh, upper_ring[k])
            b = _vp(mesh, upper_ring[kp])
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            ex = (b[0] - a[0]) / length
            ey = (b[1] - a[1]) / length
            nx_, ny_ = ey, -ex
            mesh.add_quad(
                p0=(a[0] + nx_ * 0.20, a[1] + ny_ * 0.20, rail_bot),
                p1=(a[0] + nx_ * 0.20, a[1] + ny_ * 0.20, rail_top),
                p2=(b[0] + nx_ * 0.20, b[1] + ny_ * 0.20, rail_top),
                p3=(b[0] + nx_ * 0.20, b[1] + ny_ * 0.20, rail_bot),
                role="CorniceSurface",
                surface_id=f"{pid}.clocher.belfry.eave.{k}",
                material_key="church_iron_dark",
            )
            for n in (0.24, 0.50, 0.76):
                px = a[0] + (b[0] - a[0]) * n + nx_ * 0.30
                py = a[1] + (b[1] - a[1]) * n + ny_ * 0.30
                mesh.add_quad(
                    p0=(px - ex * 0.025, py - ey * 0.025, rail_bot),
                    p1=(px - ex * 0.025, py - ey * 0.025, rail_top + 0.16),
                    p2=(px + ex * 0.025, py + ey * 0.025, rail_top + 0.16),
                    p3=(px + ex * 0.025, py + ey * 0.025, rail_bot),
                    role="Mullion",
                    surface_id=f"{pid}.clocher.belfry.rail.{k}.{n}",
                    material_key="church_stone_light",
                )

        cap_base_z = belfry_top + 0.18
        cap_mid_z = cap_base_z + CLOCHER_PEAK_H * 0.58
        cap_apex_z = cap_base_z + CLOCHER_PEAK_H
        cap_base_ring = []
        cap_mid_ring = []
        for k in range(seg):
            ang = rotation + (math.pi / seg) + 2 * math.pi * k / seg
            cap_base_ring.append(mesh.add_vertex(
                cx + (belfry_radius + 0.22) * math.cos(ang),
                cy + (belfry_radius + 0.22) * math.sin(ang),
                cap_base_z,
            ))
            cap_mid_ring.append(mesh.add_vertex(
                cx + (belfry_radius * 0.72) * math.cos(ang),
                cy + (belfry_radius * 0.72) * math.sin(ang),
                cap_mid_z,
            ))
        cap_apex = mesh.add_vertex(cx, cy, cap_apex_z)
        for k in range(seg):
            kp = (k + 1) % seg
            mesh.add_quad(
                p0=_vp(mesh, cap_base_ring[k]),
                p1=_vp(mesh, cap_mid_ring[k]),
                p2=_vp(mesh, cap_mid_ring[kp]),
                p3=_vp(mesh, cap_base_ring[kp]),
                role="RoofSurface",
                surface_id=f"{pid}.clocher.lead_cap.lower.{k}",
                material_key="dome_lead",
            )
            mesh.add_face(
                [cap_mid_ring[k], cap_apex, cap_mid_ring[kp]],
                role="RoofSurface",
                surface_id=f"{pid}.clocher.lead_cap.upper.{k}",
                material_key="dome_lead_dark",
            )
            a = _vp(mesh, cap_base_ring[k])
            m = _vp(mesh, cap_mid_ring[k])
            mesh.add_quad(
                p0=(a[0], a[1], a[2] + 0.01),
                p1=(m[0], m[1], m[2] + 0.02),
                p2=(m[0] * 0.985 + cx * 0.015, m[1] * 0.985 + cy * 0.015, m[2] + 0.04),
                p3=(a[0] * 0.985 + cx * 0.015, a[1] * 0.985 + cy * 0.015, a[2] + 0.03),
                role="RoofSurface",
                surface_id=f"{pid}.clocher.lead_cap.rib.{k}",
                material_key="dome_lead_dark",
            )

        fin_base_z = cap_apex_z
        fin_top_z = fin_base_z + CLOCHER_FINIAL_H
        rod_r = 0.06
        for k in range(4):
            ang0 = 2 * math.pi * k / 4
            ang1 = 2 * math.pi * (k + 1) / 4
            x0 = cx + rod_r * math.cos(ang0)
            y0 = cy + rod_r * math.sin(ang0)
            x1 = cx + rod_r * math.cos(ang1)
            y1 = cy + rod_r * math.sin(ang1)
            mesh.add_quad(
                p0=(x0, y0, fin_base_z),
                p1=(x0, y0, fin_top_z),
                p2=(x1, y1, fin_top_z),
                p3=(x1, y1, fin_base_z),
                role="RoofSurface",
                surface_id=f"{pid}.clocher.finial.shaft.{k}",
                material_key="dome_lead_dark",
            )
        cb_z = fin_base_z + CLOCHER_FINIAL_H * 0.55
        cb_h = 0.08
        cb_w = 0.42
        mesh.add_quad(
            p0=(cx - cb_w, cy - rod_r, cb_z),
            p1=(cx - cb_w, cy - rod_r, cb_z + cb_h),
            p2=(cx + cb_w, cy - rod_r, cb_z + cb_h),
            p3=(cx + cb_w, cy - rod_r, cb_z),
            role="RoofSurface",
            surface_id=f"{pid}.clocher.finial.cross",
            material_key="dome_lead_dark",
        )

    def _emit_clocher_bell(
        self,
        mesh: BuildingMesh,
        pid: str,
        opening_idx: int,
        mid_x: float,
        mid_y: float,
        ux: float,
        uy: float,
        nx: float,
        ny: float,
        z: float,
    ) -> None:
        w_bot = 0.48
        w_top = 0.28
        h = 0.72
        cx = mid_x + nx * 0.035
        cy = mid_y + ny * 0.035
        mesh.add_quad(
            p0=(cx - ux * w_bot / 2, cy - uy * w_bot / 2, z),
            p1=(cx - ux * w_top / 2, cy - uy * w_top / 2, z + h),
            p2=(cx + ux * w_top / 2, cy + uy * w_top / 2, z + h),
            p3=(cx + ux * w_bot / 2, cy + uy * w_bot / 2, z),
            role="Clocher",
            surface_id=f"{pid}.clocher.bell.{opening_idx}.body",
            material_key="church_bell_bronze",
        )
        mesh.add_quad(
            p0=(cx - ux * 0.10, cy - uy * 0.10, z + h),
            p1=(cx - ux * 0.07, cy - uy * 0.07, z + h + 0.28),
            p2=(cx + ux * 0.07, cy + uy * 0.07, z + h + 0.28),
            p3=(cx + ux * 0.10, cy + uy * 0.10, z + h),
            role="Clocher",
            surface_id=f"{pid}.clocher.bell.{opening_idx}.crown",
            material_key="church_bell_bronze",
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


def _is_wooden_annex_side(mid: tuple[float, float], length: float) -> bool:
    # The church ring is local to the church centroid. The W-39/1 wooden annex
    # touches the lower-left church edge; the map/photo correction says this
    # side has internal/service doors, not exterior stained-glass windows.
    return length > 8.0 and mid[0] < 1.5 and mid[1] < -4.5


def _church_body_opening_count(
    seg_idx: int,
    *,
    mid: tuple[float, float],
    length: float,
) -> int:
    """Return map-corrected church body opening count for each exterior run."""
    # The left/west church side has two short exposed runs on the Pervititch map:
    # one flat street-facing edge with two panes, and one edge directly above
    # the three W-32 mini-magazines with three panes.
    if seg_idx == 0 or _is_w32_shop_overlook_side(mid, length):
        return 3
    if seg_idx == 1 or _is_far_left_flat_street_side(mid, length):
        return 2
    return max(1, min(3, int(length // 5.5)))


def _is_w32_shop_overlook_side(mid: tuple[float, float], length: float) -> bool:
    return 6.0 <= length <= 8.5 and mid[0] < -8.0 and -1.0 <= mid[1] <= 2.5


def _is_far_left_flat_street_side(mid: tuple[float, float], length: float) -> bool:
    return 6.0 <= length <= 8.5 and mid[0] < -6.0 and mid[1] > 6.0


def _vp(mesh: BuildingMesh, idx: int) -> tuple[float, float, float]:
    v = mesh.vertices[idx]
    return (v.x, v.y, v.z)


def _dome_center_utm(church_poly: Polygon) -> tuple[tuple[float, float], str]:
    """Use the georeferenced Pervititch kubbe mark, with a geometry fallback."""
    p = Point(*DOME_MAP_CENTER_UTM)
    if church_poly.contains(p):
        return DOME_MAP_CENTER_UTM, "Pervititch GeoTIFF kubbe mark"
    c = church_poly.centroid
    return (c.x, c.y), "fallback church footprint centroid"


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
