"""PRD-003 · §6 — assemble a BuildingMesh from a Building.

Composes: ground, walls, openings, roof, plus structure-specific extras
(chimneys, skylights, monument body). Pure-Python — no backend imports.
"""
from __future__ import annotations
import math

from ..common.prd import prd
from ..modeling.building import Building
from .geometry.facade_banding import FacadeBanding
from .geometry.period_detail import PeriodDetail
from .geometry.roof import for_shape as roof_for_shape
from .geometry.roof.base import RoofGenerator
from .geometry.roof.overhang import RoofOverhang
from .geometry.shutters_balconies import ShuttersAndBalconies
from .geometry.wall_extruder import WallExtruder
from .geometry.wall_subdivider import WallSubdivider
from .geometry.wood_cladding import WoodCladding
from .mesh_graph import BuildingMesh


@prd("003", "§6 BuildingGeometryBuilder")
class BuildingGeometryBuilder:
    def __init__(self) -> None:
        self._wall_extruder = WallExtruder()
        self._wall_subdivider = WallSubdivider()
        self._wood_cladding = WoodCladding()
        self._roof_overhang = RoofOverhang()
        self._facade_banding = FacadeBanding()
        self._shutters_balconies = ShuttersAndBalconies()
        self._period_detail = PeriodDetail()

    def build(self, building: Building) -> BuildingMesh | None:
        if not building.footprint_local or not building.local_frame:
            return None
        _prepare_openings_for_render(building)

        mesh = BuildingMesh(
            parcel_id=building.parcel_id,
            placement_origin_utm=building.local_frame.origin_utm,
            placement_rotation_deg=building.local_frame.street_rotation_deg,
            palette=building.facade_palette,
            metadata={
                "material_class": building.material_class,
                "structure_type": building.structure_type,
                "footprint_source": building.footprint_source,
                "notes": building.notes,
                "shared_footprint_group_id": building.shared_footprint_group_id,
                "roof_shape": building.roof.shape if building.roof else None,
                "roof_material": building.roof.material if building.roof else None,
                "roof_pitch_deg": building.roof.pitch_deg if building.roof else None,
                "roof_slope_direction": building.roof.slope_direction if building.roof else None,
                "roof_ridge_axis_hint": building.roof.ridge_axis_hint if building.roof else None,
                "source_footprint_file": building.provenance.footprint_source_file,
                "opening_counts": _opening_counts(building),
                "opening_source_counts": _opening_source_counts(building),
            },
        )

        if building.structure_type == "fountain":
            self._build_monument(mesh, building)
            return mesh

        # Floors + ground slab (walls are emitted by the subdivider so the
        # extruder now only adds floors + ground; skip its wall-face emission).
        self._wall_extruder.extrude_slabs_only(mesh, building)

        # Walls with real punched openings.
        storey_heights = [s.height_m for s in building.storeys if not s.is_basement]
        self._wall_subdivider.emit(mesh, building, storey_heights)
        self._wood_cladding.emit(mesh, building)

        self._facade_banding.emit(mesh, building)
        self._shutters_balconies.emit(mesh, building)
        self._period_detail.emit(mesh, building, RoofGenerator.total_wall_height(building))

        eaves_z = RoofGenerator.total_wall_height(building)

        self._add_roof(mesh, building)
        self._add_roof_extras(mesh, building)
        return mesh

    def _emit_eaves_cap(self, mesh: BuildingMesh, building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        # Normal +Z (CCW from above preserves that since footprint_local is CCW).
        idx = [mesh.add_vertex(x, y, eaves_z) for (x, y) in ring]
        mesh.add_face(
            idx,
            role="RoofSurface",
            surface_id=f"{building.parcel_id}.eaves_cap",
            material_key=RoofGenerator.material_key(building),
        )

    def _add_roof(self, mesh: BuildingMesh, building: Building) -> None:
        generator: RoofGenerator = roof_for_shape(
            building.roof.shape if building.roof else "gable"
        )
        eaves_z = RoofGenerator.total_wall_height(building)
        generator.generate(mesh, building, eaves_z)

    def _add_roof_extras(self, mesh: BuildingMesh, building: Building) -> None:
        if not building.roof:
            return
        eaves_z = RoofGenerator.total_wall_height(building)
        if building.roof.has_chimney:
            self._add_chimney(mesh, building, eaves_z)
        if building.roof.has_skylight:
            self._add_skylight(mesh, building, eaves_z)

    def _add_chimney(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        """Brick shaft with a projecting stone cap (period-correct detail)."""
        ring = building.footprint_local
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        half = 0.22
        h = 2.2
        top = eaves_z + h
        corners = [
            (cx - half, cy - half), (cx + half, cy - half),
            (cx + half, cy + half), (cx - half, cy + half),
        ]
        for i in range(4):
            a = corners[i]; b = corners[(i + 1) % 4]
            mesh.add_quad(
                p0=(a[0], a[1], eaves_z), p1=(a[0], a[1], top),
                p2=(b[0], b[1], top), p3=(b[0], b[1], eaves_z),
                role="Chimney",
                surface_id=f"{building.parcel_id}.chimney.side.{i}",
                material_key="chimney_brick",
            )
        # projecting cap (wider than the shaft, 0.12 m tall)
        cap_half = half + 0.08
        cap_top = top + 0.14
        cap_corners = [
            (cx - cap_half, cy - cap_half), (cx + cap_half, cy - cap_half),
            (cx + cap_half, cy + cap_half), (cx - cap_half, cy + cap_half),
        ]
        for i in range(4):
            a = cap_corners[i]; b = cap_corners[(i + 1) % 4]
            mesh.add_quad(
                p0=(a[0], a[1], top), p1=(a[0], a[1], cap_top),
                p2=(b[0], b[1], cap_top), p3=(b[0], b[1], top),
                role="Chimney",
                surface_id=f"{building.parcel_id}.chimney.cap.side.{i}",
                material_key="plinth_stone",
            )
        top_idx = [mesh.add_vertex(x, y, cap_top) for (x, y) in cap_corners]
        mesh.add_face(top_idx, role="Chimney",
                      surface_id=f"{building.parcel_id}.chimney.cap.top",
                      material_key="plinth_stone")

    def _add_skylight(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ring = building.footprint_local
        if len(ring) < 3:
            return
        axis = _longest_edge_axis(ring)
        perp = (-axis[1], axis[0])
        u_values = [x * axis[0] + y * axis[1] for x, y in ring]
        v_values = [x * perp[0] + y * perp[1] for x, y in ring]
        u_mid = (min(u_values) + max(u_values)) / 2.0
        v_mid = (min(v_values) + max(v_values)) / 2.0
        length = max(u_values) - min(u_values)
        width = max(v_values) - min(v_values)
        if length <= 0.8 or width <= 0.8:
            return
        half_w = min(0.65, max(0.38, length * 0.12))
        half_d = min(0.42, max(0.26, width * 0.12))
        frame_w = min(0.09, half_w * 0.22, half_d * 0.28)
        z = _skylight_top_z(building, eaves_z, width)

        def p(du: float, dv: float, dz: float = 0.0) -> tuple[float, float, float]:
            u = u_mid + du
            v = v_mid + dv
            return (
                axis[0] * u + perp[0] * v,
                axis[1] * u + perp[1] * v,
                z + dz,
            )

        mesh.add_quad(
            p0=p(-half_w + frame_w, -half_d + frame_w),
            p1=p(half_w - frame_w, -half_d + frame_w),
            p2=p(half_w - frame_w, half_d - frame_w),
            p3=p(-half_w + frame_w, half_d - frame_w),
            role="Skylight",
            surface_id=f"{building.parcel_id}.skylight.glass",
            material_key="window_glass",
        )
        frame_z = 0.025
        strips = (
            ("front", -half_w, -half_d, half_w, -half_d + frame_w),
            ("back", -half_w, half_d - frame_w, half_w, half_d),
            ("left", -half_w, -half_d + frame_w, -half_w + frame_w, half_d - frame_w),
            ("right", half_w - frame_w, -half_d + frame_w, half_w, half_d - frame_w),
        )
        for name, u0, v0, u1, v1 in strips:
            mesh.add_quad(
                p0=p(u0, v0, frame_z),
                p1=p(u1, v0, frame_z),
                p2=p(u1, v1, frame_z),
                p3=p(u0, v1, frame_z),
                role="Skylight",
                surface_id=f"{building.parcel_id}.skylight.frame.{name}",
                material_key="trim",
            )

    def _build_monument(self, mesh: BuildingMesh, building: Building) -> None:
        """Çeşme / fountain: carved Ottoman street-fountain facade."""
        ring = building.footprint_local
        if not ring:
            return
        if building.parcel_id == "W-39/2":
            self._build_ottoman_fountain(mesh, building)
            return
        height = building.storeys[0].height_m if building.storeys else 1.8
        # Ground
        base_idx = [mesh.add_vertex(x, y, 0.0) for (x, y) in ring]
        mesh.add_face(base_idx, role="GroundSurface",
                      surface_id=f"{building.parcel_id}.ground",
                      material_key="monument_stone")
        # Side faces
        for i, (x, y) in enumerate(ring):
            nx, ny = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(x, y, 0.0), p1=(nx, ny, 0.0),
                p2=(nx, ny, height), p3=(x, y, height),
                role="MonumentBody",
                surface_id=f"{building.parcel_id}.monument.{i}",
                material_key="monument_stone",
            )
        # Top cap
        top_idx = [mesh.add_vertex(x, y, height) for (x, y) in ring]
        mesh.add_face(top_idx, role="RoofSurface",
                      surface_id=f"{building.parcel_id}.monument.cap",
                      material_key="monument_stone")

    def _build_ottoman_fountain(self, mesh: BuildingMesh, building: Building) -> None:
        """Photo-guided Ottoman fountain: niche, inscription, rosettes, trough."""
        ring = building.footprint_local
        height = min(max(building.storeys[0].height_m if building.storeys else 3.65, 3.35), 3.75)
        pid = building.parcel_id
        plinth_h = 0.38

        # Keep the georeferenced KML footprint, but do not extrude it into a
        # tall solid block. The real asset reads as a low street plinth plus a
        # carved facade slab embedded in the adjacent wall.
        base_idx = [mesh.add_vertex(x, y, 0.0) for (x, y) in ring]
        mesh.add_face(base_idx, role="GroundSurface",
                      surface_id=f"{pid}.ground",
                      material_key="fountain_basin_stone")
        for i, (x, y) in enumerate(ring):
            nx, ny = ring[(i + 1) % len(ring)]
            mesh.add_quad(
                p0=(x, y, 0.0), p1=(nx, ny, 0.0),
                p2=(nx, ny, plinth_h), p3=(x, y, plinth_h),
                role="MonumentBody",
                surface_id=f"{pid}.low_plinth.side.{i}",
                material_key="fountain_basin_stone",
            )
        top_idx = [mesh.add_vertex(x, y, plinth_h) for (x, y) in ring]
        mesh.add_face(top_idx, role="RoofSurface",
                      surface_id=f"{pid}.low_plinth.top",
                      material_key="fountain_basin_stone")

        frame = _fountain_front_frame(building)
        if frame is None:
            return
        cx, cy, ux, uy, nx, ny, edge_len = frame
        facade_w = min(3.55, max(2.75, edge_len * 0.82))

        def p(u: float, z: float, out: float = 0.06) -> tuple[float, float, float]:
            return (cx + ux * u + nx * out, cy + uy * u + ny * out, z)

        # Main dressed-stone wall slab with actual thickness. This replaces the
        # previous full-height footprint extrusion that made the fountain look
        # like a stretched block.
        _facade_box(mesh, pid, p, -facade_w / 2, facade_w / 2, -0.08, 0.16, 0.0, height,
                    "monument_stone", "facade.wall_slab")

        # Layered Ottoman stone profiles: lower plinth, string courses, and
        # the heavy top coping seen in the street photos.
        for z0, z1, key, name, out0, out1 in (
            (0.00, 0.17, "fountain_stone_dark", "threshold", 0.04, 0.24),
            (0.42, 0.56, "plinth_stone", "lower_belt", 0.02, 0.30),
            (0.58, 0.66, "fountain_stone_dark", "lower_shadow_line", 0.18, 0.34),
            (height - 0.54, height - 0.46, "fountain_stone_dark", "cornice_shadow", 0.10, 0.32),
            (height - 0.42, height - 0.20, "plinth_stone", "heavy_cornice", 0.02, 0.45),
            (height - 0.18, height, "fountain_basin_stone", "top_coping", -0.03, 0.52),
        ):
            _facade_box(mesh, pid, p, -facade_w / 2 - 0.10, facade_w / 2 + 0.10,
                        out0, out1, z0, z1, key, f"facade.{name}")

        # Side pilasters and narrow reeded profiles, now modeled as small
        # raised blocks rather than flat colored strips.
        side_w = 0.24
        for side, u0, u1 in (
            ("left", -facade_w / 2 + 0.12, -facade_w / 2 + 0.12 + side_w),
            ("right", facade_w / 2 - 0.12 - side_w, facade_w / 2 - 0.12),
        ):
            _facade_box(mesh, pid, p, u0, u1, 0.12, 0.34, 0.20, height - 0.28,
                        "plinth_stone", f"facade.pilaster.{side}")
            groove_u0 = u1 + (0.06 if side == "left" else -0.10)
            groove_u1 = u1 + (0.10 if side == "left" else -0.06)
            _facade_box(mesh, pid, p, min(groove_u0, groove_u1), max(groove_u0, groove_u1),
                        0.28, 0.39, 0.36, height - 0.48,
                        "fountain_stone_dark", f"facade.reeded_profile.{side}")

        # Pointed arched recessed niche.
        arch_w = min(1.95, facade_w * 0.58)
        spring_z = 1.76
        apex_z = 2.56
        arch = [
            (-arch_w / 2, 0.68), (-arch_w / 2, spring_z),
            (-0.78, 1.98), (-0.42, 2.30), (0.0, apex_z),
            (0.42, 2.30), (0.78, 1.98), (arch_w / 2, spring_z),
            (arch_w / 2, 0.68),
        ]
        _facade_poly(mesh, pid, p, arch, "fountain_shadow", "niche.recess_back", out=0.015)
        _facade_quad(mesh, pid, p, -arch_w / 2 + 0.10, 0.74, arch_w / 2 - 0.10, 1.07,
                     "fountain_shadow", "niche.deep_lower_back", out=0.005)
        _facade_profile_strip(mesh, pid, p, arch[1:-1], 0.22, "plinth_stone",
                              "niche.pointed_arch_voussoir", center=(0.0, 1.78), out=0.38)
        _facade_box(mesh, pid, p, -arch_w / 2 - 0.15, -arch_w / 2 + 0.04,
                    0.18, 0.40, 0.68, spring_z + 0.08, "plinth_stone", "niche.left_jamb")
        _facade_box(mesh, pid, p, arch_w / 2 - 0.04, arch_w / 2 + 0.15,
                    0.18, 0.40, 0.68, spring_z + 0.08, "plinth_stone", "niche.right_jamb")
        _facade_box(mesh, pid, p, -0.11, 0.11, 0.34, 0.50, apex_z - 0.05, apex_z + 0.13,
                    "fountain_basin_stone", "niche.keystone")
        _facade_box(mesh, pid, p, -arch_w / 2 + 0.16, arch_w / 2 - 0.16,
                    0.10, 0.32, 1.00, 1.10, "fountain_stone_dark", "niche.back_shelf")

        # Central spout panel, metal tap, and water line.
        _facade_box(mesh, pid, p, -0.36, 0.36, 0.12, 0.30, 0.58, 1.02,
                    "fountain_basin_stone", "spout.carved_panel")
        _facade_quad(mesh, pid, p, -0.22, 0.77, 0.22, 0.95, "plinth_stone",
                     "spout.panel_relief", out=0.34)
        _facade_box(mesh, pid, p, -0.045, 0.045, 0.31, 0.48, 0.84, 0.91,
                    "fountain_metal", "spout.tap")
        _facade_box(mesh, pid, p, -0.018, 0.018, 0.44, 0.48, 0.46, 0.84,
                    "fountain_water", "spout.water_thread")

        # Front trough / yalak.
        _facade_box(mesh, pid, p, -1.16, 1.16, 0.30, 1.04, 0.00, 0.44,
                    "fountain_basin_stone", "trough.outer")
        _facade_quad_horizontal(mesh, pid, p, -0.92, 0.92, 0.43, 0.88, 0.46,
                                "fountain_water", "trough.water")
        _facade_box(mesh, pid, p, -1.08, 1.08, 0.92, 1.12, 0.18, 0.52,
                    "plinth_stone", "trough.front_lip")

        # Kitabe plaque and abstract gold calligraphic strokes.
        plaque_u0, plaque_u1 = -0.68, 0.68
        plaque_z0, plaque_z1 = height - 0.88, height - 0.48
        _facade_quad(mesh, pid, p, plaque_u0, plaque_z0, plaque_u1, plaque_z1,
                     "fountain_plaque_green", "inscription.green_plaque", out=0.46)
        strokes = [
            (-0.56, plaque_z1 - 0.11, -0.18, plaque_z1 - 0.08),
            (-0.10, plaque_z1 - 0.09, 0.44, plaque_z1 - 0.07),
            (-0.52, plaque_z0 + 0.21, 0.18, plaque_z0 + 0.24),
            (0.26, plaque_z0 + 0.20, 0.56, plaque_z0 + 0.24),
            (-0.40, plaque_z0 + 0.10, 0.03, plaque_z0 + 0.15),
            (0.10, plaque_z0 + 0.12, 0.50, plaque_z0 + 0.16),
            (-0.60, plaque_z0 + 0.15, -0.50, plaque_z1 - 0.12),
            (0.58, plaque_z0 + 0.08, 0.64, plaque_z1 - 0.16),
        ]
        for i, (u0, z0, u1, z1) in enumerate(strokes):
            _facade_line(mesh, pid, p, u0, z0, u1, z1, 0.035, "fountain_gold",
                         f"inscription.gold_stroke.{i}", out=0.49)

        # Rosette medallions flanking the plaque.
        rosette_z = (plaque_z0 + plaque_z1) / 2.0
        _facade_disk(mesh, pid, p, -1.03, rosette_z, 0.24, "plinth_stone", "rosette.left", out=0.45)
        _facade_disk(mesh, pid, p, 1.03, rosette_z, 0.24, "plinth_stone", "rosette.right", out=0.45)
        for side, c_u in (("left", -1.03), ("right", 1.03)):
            for petal in range(8):
                ang = (math.tau * petal) / 8.0
                u0 = c_u + math.cos(ang) * 0.07
                z0 = rosette_z + math.sin(ang) * 0.07
                u1 = c_u + math.cos(ang) * 0.21
                z1 = rosette_z + math.sin(ang) * 0.21
                _facade_line(mesh, pid, p, u0, z0, u1, z1, 0.045, "fountain_stone_dark",
                             f"rosette.{side}.petal.{petal}", out=0.50)

        # Fine stone joints and side weathering strips for carved-stone scale.
        for i, z in enumerate((0.86, 1.32, 1.94, 2.48, height - 1.08)):
            _facade_quad(mesh, pid, p, -facade_w / 2 + 0.32, z, facade_w / 2 - 0.32, z + 0.018,
                         "fountain_stone_dark", f"stone_joint.horizontal.{i}", out=0.405)
        for i, u in enumerate((-facade_w / 2 + 0.56, facade_w / 2 - 0.56)):
            _facade_quad(mesh, pid, p, u, 0.40, u + 0.025, height - 0.42,
                         "fountain_stone_dark", f"stone_joint.vertical.{i}", out=0.405)

        mesh.metadata["photo_guided_detail"] = (
            "Ottoman fountain rebuilt as low plinth + thick carved facade: "
            "recessed pointed niche, kitabe plaque, rosettes, protruding trough"
        )


def _longest_edge_axis(ring: list[tuple[float, float]]) -> tuple[float, float]:
    best_len = 0.0
    axis = (1.0, 0.0)
    for i, (ax, ay) in enumerate(ring):
        bx, by = ring[(i + 1) % len(ring)]
        d = math.hypot(bx - ax, by - ay)
        if d > best_len:
            best_len = d
            axis = ((bx - ax) / d, (by - ay) / d)
    return axis


def _fountain_front_frame(
    building: Building,
) -> tuple[float, float, float, float, float, float, float] | None:
    ring = building.footprint_local
    if len(ring) < 2:
        return None
    cx_poly = sum(x for x, _ in ring) / len(ring)
    cy_poly = sum(y for _, y in ring) / len(ring)
    best = None
    best_len = 0.0
    segment_edges = [
        (s.start[0], s.start[1], s.end[0], s.end[1])
        for s in building.wall_segments
        if s.is_street_facing and not s.is_party_wall
    ]
    ring_edges = [
        (ax, ay, ring[(i + 1) % len(ring)][0], ring[(i + 1) % len(ring)][1])
        for i, (ax, ay) in enumerate(ring)
    ]
    for ax, ay, bx, by in (segment_edges or ring_edges):
        dx = bx - ax
        dy = by - ay
        length = math.hypot(dx, dy)
        if length <= best_len:
            continue
        ux = dx / length
        uy = dy / length
        nx = -uy
        ny = ux
        mx = (ax + bx) / 2.0
        my = (ay + by) / 2.0
        # Choose the normal pointing away from the polygon centroid.
        if ((mx + nx) - cx_poly) ** 2 + ((my + ny) - cy_poly) ** 2 < ((mx - nx) - cx_poly) ** 2 + ((my - ny) - cy_poly) ** 2:
            nx = -nx
            ny = -ny
        best = (mx, my, ux, uy, nx, ny, length)
        best_len = length
    return best


def _facade_quad(
    mesh: BuildingMesh,
    pid: str,
    p,
    u0: float,
    z0: float,
    u1: float,
    z1: float,
    material_key: str,
    name: str,
    out: float = 0.08,
) -> None:
    if u1 <= u0 or z1 <= z0:
        return
    mesh.add_quad(
        p0=p(u0, z0, out),
        p1=p(u0, z1, out),
        p2=p(u1, z1, out),
        p3=p(u1, z0, out),
        role="MonumentBody",
        surface_id=f"{pid}.{name}",
        material_key=material_key,
    )


def _facade_poly(
    mesh: BuildingMesh,
    pid: str,
    p,
    points: list[tuple[float, float]],
    material_key: str,
    name: str,
    out: float = 0.08,
) -> None:
    if len(points) < 3:
        return
    idx = [mesh.add_vertex(*p(u, z, out)) for u, z in points]
    mesh.add_face(
        idx,
        role="MonumentBody",
        surface_id=f"{pid}.{name}",
        material_key=material_key,
    )


def _facade_profile_strip(
    mesh: BuildingMesh,
    pid: str,
    p,
    points: list[tuple[float, float]],
    thickness: float,
    material_key: str,
    name: str,
    center: tuple[float, float],
    out: float = 0.10,
) -> None:
    if len(points) < 2:
        return
    cu, cz = center
    half = thickness / 2.0
    for i, ((u0, z0), (u1, z1)) in enumerate(zip(points, points[1:])):
        du = u1 - u0
        dz = z1 - z0
        length = math.hypot(du, dz)
        if length <= 0.01:
            continue
        pu = -dz / length
        pz = du / length
        mu = (u0 + u1) / 2.0
        mz = (z0 + z1) / 2.0
        if (pu * (mu - cu) + pz * (mz - cz)) < 0:
            pu = -pu
            pz = -pz
        mesh.add_quad(
            p0=p(u0 - pu * half, z0 - pz * half, out),
            p1=p(u0 + pu * half, z0 + pz * half, out),
            p2=p(u1 + pu * half, z1 + pz * half, out),
            p3=p(u1 - pu * half, z1 - pz * half, out),
            role="MonumentBody",
            surface_id=f"{pid}.{name}.{i}",
            material_key=material_key,
        )


def _facade_line(
    mesh: BuildingMesh,
    pid: str,
    p,
    u0: float,
    z0: float,
    u1: float,
    z1: float,
    width: float,
    material_key: str,
    name: str,
    out: float = 0.12,
) -> None:
    du = u1 - u0
    dz = z1 - z0
    length = math.hypot(du, dz)
    if length <= 0.01:
        return
    pu = -dz / length * width / 2.0
    pz = du / length * width / 2.0
    mesh.add_quad(
        p0=p(u0 - pu, z0 - pz, out),
        p1=p(u0 + pu, z0 + pz, out),
        p2=p(u1 + pu, z1 + pz, out),
        p3=p(u1 - pu, z1 - pz, out),
        role="MonumentBody",
        surface_id=f"{pid}.{name}",
        material_key=material_key,
    )


def _facade_disk(
    mesh: BuildingMesh,
    pid: str,
    p,
    u: float,
    z: float,
    radius: float,
    material_key: str,
    name: str,
    out: float = 0.12,
    segments: int = 20,
) -> None:
    points = [
        (u + math.cos(math.tau * i / segments) * radius,
         z + math.sin(math.tau * i / segments) * radius)
        for i in range(segments)
    ]
    _facade_poly(mesh, pid, p, points, material_key, name, out=out)


def _facade_box(
    mesh: BuildingMesh,
    pid: str,
    p,
    u0: float,
    u1: float,
    out0: float,
    out1: float,
    z0: float,
    z1: float,
    material_key: str,
    name: str,
) -> None:
    if u1 <= u0 or out1 <= out0 or z1 <= z0:
        return
    corners = {
        "000": p(u0, z0, out0), "100": p(u1, z0, out0),
        "110": p(u1, z1, out0), "010": p(u0, z1, out0),
        "001": p(u0, z0, out1), "101": p(u1, z0, out1),
        "111": p(u1, z1, out1), "011": p(u0, z1, out1),
    }
    quads = [
        ("back", "000", "010", "110", "100"),
        ("front", "001", "101", "111", "011"),
        ("left", "000", "001", "011", "010"),
        ("right", "100", "110", "111", "101"),
        ("bottom", "000", "100", "101", "001"),
        ("top", "010", "011", "111", "110"),
    ]
    for suffix, a, b, c, d in quads:
        mesh.add_quad(
            p0=corners[a],
            p1=corners[b],
            p2=corners[c],
            p3=corners[d],
            role="MonumentBody",
            surface_id=f"{pid}.{name}.{suffix}",
            material_key=material_key,
        )


def _facade_quad_horizontal(
    mesh: BuildingMesh,
    pid: str,
    p,
    u0: float,
    u1: float,
    out0: float,
    out1: float,
    z: float,
    material_key: str,
    name: str,
) -> None:
    if u1 <= u0 or out1 <= out0:
        return
    mesh.add_quad(
        p0=p(u0, z, out0),
        p1=p(u1, z, out0),
        p2=p(u1, z, out1),
        p3=p(u0, z, out1),
        role="MonumentBody",
        surface_id=f"{pid}.{name}",
        material_key=material_key,
    )


def _skylight_top_z(building: Building, eaves_z: float, roof_span_m: float) -> float:
    if not building.roof:
        return eaves_z + 0.35
    shape = building.roof.shape
    pitch_rad = math.radians(building.roof.pitch_deg)
    if shape in {"flat"}:
        return eaves_z + 0.18
    if shape == "vault_flat":
        return eaves_z + max(0.35, min(roof_span_m * 0.16, 1.15)) + 0.06
    if shape in {"gable", "hip", "complex_pitched", "mansard"}:
        return eaves_z + max(0.35, min((roof_span_m / 2.0) * math.tan(pitch_rad), 3.0)) + 0.06
    return eaves_z + 0.35


def _opening_counts(building: Building) -> dict[str, int]:
    counts = {"door": 0, "shop_window": 0, "window": 0}
    for seg in building.wall_segments:
        for op in seg.openings:
            if op.kind in counts:
                counts[op.kind] += 1
    return counts


def _opening_source_counts(building: Building) -> dict[str, int]:
    counts: dict[str, int] = {}
    for seg in building.wall_segments:
        for op in seg.openings:
            source = op.color_source or "unknown"
            counts[source] = counts.get(source, 0) + 1
    return counts


def _prepare_openings_for_render(building: Building) -> None:
    if not _is_magasin_like(building):
        return
    for seg in building.wall_segments:
        length = seg.length_m
        if length <= 1.0:
            continue
        doors = [
            op for op in seg.openings
            if op.kind == "door" and op.storey_level == 0
        ]
        if not doors:
            continue
        gap = 0.22
        max_per_door = max(0.9, (length - 0.36 - gap * max(0, len(doors) - 1)) / len(doors))
        desired = 1.9 if len(doors) == 1 else 1.55
        for op in doors:
            if op.kind != "door" or op.storey_level != 0:
                continue
            target_w = min(max(op.width_m, desired), max_per_door)
            center = op.position_along_wall_m + op.width_m / 2.0
            op.width_m = round(target_w, 3)
            op.height_m = round(max(op.height_m, 2.65), 3)
            op.position_along_wall_m = round(
                max(0.18, min(length - target_w - 0.18, center - target_w / 2.0)),
                3,
            )
            if "magasin-entry" not in op.color_source:
                op.color_source = f"{op.color_source}:magasin-entry"


def _is_magasin_like(building: Building) -> bool:
    texts: list[str] = []
    for storey in building.storeys:
        if storey.level == 0 and storey.use:
            texts.append(storey.use)
    snap = building.excel_snapshot or {}
    texts.extend([
        str(snap.get("wall_code") or ""),
        str(snap.get("bim_notes") or ""),
    ])
    gf = snap.get("ground_floor") or {}
    if isinstance(gf, dict):
        texts.extend(str(v) for v in gf.values() if v)
    texts.append(str(building.notes or {}))
    text = " ".join(texts).lower()
    return any(token in text for token in ("mg", "magasin", "magazine", "shop", "bakery", "fırın", "firin"))
