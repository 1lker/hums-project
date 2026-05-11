"""Map-derived courtyard/garden surfaces for Block 147."""
from __future__ import annotations
import json
import math

from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import unary_union

from ...common.paths import BLOCK_GEOJSON, FOOTPRINTS_GEOJSON, NON_PARCEL_FOOTPRINTS_GEOJSON
from ...common.prd import prd
from ...modeling.building import FacadePalette
from ..mesh_graph import BuildingMesh


# Manual crop of the light-green open courtyard/garden marked "(147)" on the
# Pervititch raster. The final polygon is clipped by the actual block void, so
# this cannot cover traced KML/SHP buildings.
COURTYARD_147_BOUNDS_UTM = (670347.0, 4539690.0, 670359.0, 4539704.0)
COURTYARD_147_TREE_UTM = (670354.70, 4539697.75)
COURTYARD_147_TREE_SOURCE = (
    "Pervititch raster dark-green vegetation cluster center; "
    "GeoTIFF threshold bbox nudged south toward the S-43 courtyard edge "
    "around 670354.70 / 4539697.75"
)

N50_REAR_LIGHTWELL_UTM = (
    (670362.810, 4539709.266),
    (670361.735, 4539707.284),
    (670361.526, 4539706.910),
    (670360.366, 4539707.561),
    (670362.227, 4539710.874),
    (670363.318, 4539710.262),
)
N50_LIGHTWELL_RIM_Z = 0.28
N50_LIGHTWELL_RIM_WIDTH = 0.26
N50_REAR_LIGHTWELL_SOURCE = (
    "Georeferenced rectangular negative space at parcel 50, bounded by the "
    "N-50 and N-52/54 traced KML/SHP footprints and confirmed in the "
    "building-entrence-50 Pervititch crop. This is a side/rear notch in the "
    "N-50 mass, not a separate grey block."
)

GARDEN_PALETTE = FacadePalette(
    wall_main=(126, 150, 88),
    wall_accent=(86, 126, 62),
    trim=(96, 65, 42),
    roof=(78, 118, 58),
    shutters=None,
    gf_shopfront=None,
    source="pervititch_courtyard_garden",
)


@prd("004", "CourtyardGardenBuilder")
class CourtyardGardenBuilder:
    def build_all(self) -> list[BuildingMesh]:
        meshes: list[BuildingMesh] = []
        garden = self.build()
        if garden is not None:
            meshes.append(garden)
        lightwell = self.build_n50_rear_lightwell()
        if lightwell is not None:
            meshes.append(lightwell)
        return meshes

    def build(self) -> BuildingMesh | None:
        patch = _courtyard_patch()
        if patch is None or patch.area < 5.0:
            return None

        c = patch.centroid
        mesh = BuildingMesh(
            parcel_id="COURTYARD-147-GARDEN",
            placement_origin_utm=(c.x, c.y),
            placement_rotation_deg=0.0,
            palette=GARDEN_PALETTE,
            metadata={
                "material_class": "landscape",
                "structure_type": "courtyard_garden",
                "footprint_source": "map-interpreted",
                "notes": {
                    "map_reading": (
                        "Light green open Block 147 courtyard/garden. The big dark-green "
                        "vegetation mark is treated as one mature tree; remaining lower area "
                        "is grass/low planting."
                    ),
                    "bounds_utm": COURTYARD_147_BOUNDS_UTM,
                    "tree_center_utm": COURTYARD_147_TREE_UTM,
                    "tree_source": COURTYARD_147_TREE_SOURCE,
                },
            },
        )

        local_ring = [(x - c.x, y - c.y) for x, y in list(patch.exterior.coords)[:-1]]
        ground = [mesh.add_vertex(x, y, 0.035) for x, y in reversed(local_ring)]
        mesh.add_face(
            ground,
            role="LandscapeSurface",
            surface_id="COURTYARD-147-GARDEN.grass",
            material_key="grass_ground",
        )

        _emit_grass_texture(mesh, c, patch)
        _emit_map_tree(mesh, c, COURTYARD_147_TREE_UTM)
        return mesh

    def build_n50_rear_lightwell(self) -> BuildingMesh | None:
        patch = _n50_rear_lightwell_patch()
        if patch is None or patch.area < 0.65:
            return None

        c = patch.centroid
        mesh = BuildingMesh(
            parcel_id="COURTYARD-147-N50-LIGHTWELL",
            placement_origin_utm=(c.x, c.y),
            placement_rotation_deg=0.0,
            palette=GARDEN_PALETTE,
            metadata={
                "material_class": "landscape",
                "structure_type": "courtyard_lightwell",
                "footprint_source": "map-interpreted",
                "source_footprint_file": "N-50 / N-52-54 georeferenced KML negative space",
                "notes": {
                    "map_reading": (
                        "Small rectangular open rear area at parcel 50. The "
                        "N-50 mass is cut to an L plan around this void; this "
                        "mesh only marks flush ground paving, with no curb or "
                        "wall around the cut."
                    ),
                    "ring_utm": N50_REAR_LIGHTWELL_UTM,
                    "source": N50_REAR_LIGHTWELL_SOURCE,
                },
            },
        )

        local_ring = [(x - c.x, y - c.y) for x, y in list(patch.exterior.coords)[:-1]]
        ground = [mesh.add_vertex(x, y, 0.012) for x, y in reversed(local_ring)]
        mesh.add_face(
            ground,
            role="LandscapeSurface",
            surface_id="COURTYARD-147-N50-LIGHTWELL.paving",
            material_key="lightwell_paving",
        )
        _emit_lightwell_paving_joints(mesh, c, patch)
        return mesh


def _courtyard_patch() -> Polygon | None:
    if not BLOCK_GEOJSON.exists() or not FOOTPRINTS_GEOJSON.exists():
        return None
    block_feats = json.loads(BLOCK_GEOJSON.read_text()).get("features", [])
    if not block_feats:
        return None
    block = shape(block_feats[0]["geometry"])

    building_polys = []
    for path in (FOOTPRINTS_GEOJSON, NON_PARCEL_FOOTPRINTS_GEOJSON):
        if not path.exists():
            continue
        for feat in json.loads(path.read_text()).get("features", []):
            geom = shape(feat["geometry"])
            if geom.intersects(block):
                building_polys.append(geom)

    occupied = unary_union(building_polys).buffer(0.06) if building_polys else Polygon()
    open_space = block.difference(occupied)
    clipped = open_space.intersection(box(*COURTYARD_147_BOUNDS_UTM))
    if clipped.is_empty:
        return None
    if clipped.geom_type == "Polygon":
        return clipped
    if hasattr(clipped, "geoms"):
        polys = [p for p in clipped.geoms if p.geom_type == "Polygon"]
        return max(polys, key=lambda p: p.area) if polys else None
    return None


def _n50_rear_lightwell_patch() -> Polygon | None:
    patch = Polygon(N50_REAR_LIGHTWELL_UTM).buffer(0)
    if patch.is_empty:
        return None
    if BLOCK_GEOJSON.exists():
        block_feats = json.loads(BLOCK_GEOJSON.read_text()).get("features", [])
        if block_feats:
            clipped = patch.intersection(shape(block_feats[0]["geometry"]))
            if clipped.is_empty:
                return None
            if clipped.geom_type == "Polygon":
                patch = clipped
            elif hasattr(clipped, "geoms"):
                polys = [p for p in clipped.geoms if p.geom_type == "Polygon"]
                if not polys:
                    return None
                patch = max(polys, key=lambda p: p.area)
    return patch


def _emit_lightwell_curb(mesh: BuildingMesh, origin, patch: Polygon) -> None:
    coords = list(patch.exterior.coords)
    for idx, (a, b) in enumerate(zip(coords, coords[1:])):
        _emit_ground_strip(
            mesh,
            origin,
            a,
            b,
            width=0.16,
            z=0.205,
            material_key="lightwell_curb",
            surface_id=f"COURTYARD-147-N50-LIGHTWELL.curb.top.{idx}",
        )
        _emit_curb_face(
            mesh,
            origin,
            a,
            b,
            z0=0.03,
            z1=0.28,
            material_key="lightwell_curb",
            surface_id=f"COURTYARD-147-N50-LIGHTWELL.curb.face.{idx}",
        )


def _emit_lightwell_shaft(mesh: BuildingMesh, origin, patch: Polygon) -> None:
    coords = list(patch.exterior.coords)
    for idx, (a, b) in enumerate(zip(coords, coords[1:])):
        ax, ay = a[0] - origin.x, a[1] - origin.y
        bx, by = b[0] - origin.x, b[1] - origin.y
        mesh.add_quad(
            p0=(ax, ay, 0.12),
            p1=(bx, by, 0.12),
            p2=(bx, by, N50_LIGHTWELL_RIM_Z),
            p3=(ax, ay, N50_LIGHTWELL_RIM_Z),
            role="WallSurface",
            surface_id=f"COURTYARD-147-N50-LIGHTWELL.shaft.wall.{idx}",
            material_key="lightwell_wall",
        )


def _emit_lightwell_roof_opening(mesh: BuildingMesh, origin, patch: Polygon) -> None:
    coords = list(patch.exterior.coords)[:-1]
    local_ring = [(x - origin.x, y - origin.y) for x, y in coords]
    shadow = [
        mesh.add_vertex(x, y, N50_LIGHTWELL_RIM_Z + 0.018)
        for x, y in reversed(local_ring)
    ]
    mesh.add_face(
        shadow,
        role="LandscapeSurface",
        surface_id="COURTYARD-147-N50-LIGHTWELL.open_void_shadow",
        material_key="lightwell_shadow",
    )
    for idx, (a, b) in enumerate(zip(list(patch.exterior.coords), list(patch.exterior.coords)[1:])):
        _emit_ground_strip(
            mesh,
            origin,
            a,
            b,
            width=N50_LIGHTWELL_RIM_WIDTH,
            z=N50_LIGHTWELL_RIM_Z + 0.055,
            material_key="lightwell_curb",
            surface_id=f"COURTYARD-147-N50-LIGHTWELL.roof_rim.{idx}",
        )


def _emit_lightwell_paving_joints(mesh: BuildingMesh, origin, patch: Polygon) -> None:
    c = patch.centroid
    marks = [
        ((c.x - 0.55, c.y - 0.15), (c.x + 0.48, c.y + 0.08), "joint.a"),
        ((c.x - 0.18, c.y - 0.78), (c.x + 0.12, c.y + 0.70), "joint.b"),
        ((c.x - 1.05, c.y + 0.28), (c.x + 0.88, c.y + 0.38), "joint.c"),
    ]
    for a, b, name in marks:
        line = Polygon([
            (a[0], a[1]), (b[0], b[1]), (b[0] + 0.01, b[1] + 0.01), (a[0] + 0.01, a[1] + 0.01),
        ])
        if not patch.buffer(0.04).intersects(line):
            continue
        _emit_ground_strip(
            mesh,
            origin,
            a,
            b,
            width=0.025,
            z=0.018,
            material_key="lightwell_paving",
            surface_id=f"COURTYARD-147-N50-LIGHTWELL.paving.{name}",
        )


def _emit_curb_face(
    mesh: BuildingMesh,
    origin,
    a: tuple[float, float],
    b: tuple[float, float],
    z0: float,
    z1: float,
    material_key: str,
    surface_id: str,
) -> None:
    ax, ay = a[0] - origin.x, a[1] - origin.y
    bx, by = b[0] - origin.x, b[1] - origin.y
    mesh.add_quad(
        p0=(ax, ay, z0),
        p1=(bx, by, z0),
        p2=(bx, by, z1),
        p3=(ax, ay, z1),
        role="LandscapeSurface",
        surface_id=surface_id,
        material_key=material_key,
    )


def _emit_ground_strip(
    mesh: BuildingMesh,
    origin,
    a: tuple[float, float],
    b: tuple[float, float],
    width: float,
    z: float,
    material_key: str,
    surface_id: str,
) -> None:
    ax, ay = a[0] - origin.x, a[1] - origin.y
    bx, by = b[0] - origin.x, b[1] - origin.y
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length <= 0.001:
        return
    nx, ny = -dy / length * width * 0.5, dx / length * width * 0.5
    mesh.add_quad(
        p0=(ax - nx, ay - ny, z),
        p1=(bx - nx, by - ny, z),
        p2=(bx + nx, by + ny, z),
        p3=(ax + nx, ay + ny, z),
        role="LandscapeSurface",
        surface_id=surface_id,
        material_key=material_key,
    )


def _emit_grass_tuft(
    mesh: BuildingMesh,
    origin,
    utm: tuple[float, float],
    width: float,
    height: float,
    name: str,
) -> None:
    cx = utm[0] - origin.x
    cy = utm[1] - origin.y
    z0 = 0.05
    for idx, ang in enumerate((-25.0, 0.0, 24.0)):
        rad = math.radians(ang)
        dx = math.cos(rad) * width * 0.5
        dy = math.sin(rad) * width * 0.5
        mesh.add_quad(
            p0=(cx - dx, cy - dy, z0),
            p1=(cx - dx * 0.25, cy - dy * 0.25, z0 + height),
            p2=(cx + dx * 0.25, cy + dy * 0.25, z0 + height),
            p3=(cx + dx, cy + dy, z0),
            role="Vegetation",
            surface_id=f"COURTYARD-147-GARDEN.tuft.{name}.{idx}",
            material_key="garden_shrub",
        )


def _emit_grass_texture(mesh: BuildingMesh, origin, patch: Polygon) -> None:
    """Low, map-constrained grass strokes inside the open courtyard polygon."""
    grass_marks = [
        ((670349.1, 4539702.0), 0.62, 0.28, "grass_light", "north_west_1"),
        ((670350.5, 4539701.3), 0.74, 0.30, "grass_dark", "north_west_2"),
        ((670352.2, 4539699.6), 0.82, 0.34, "grass_light", "under_tree_west"),
        ((670353.4, 4539697.8), 0.92, 0.38, "grass_dark", "center_low"),
        ((670354.2, 4539694.6), 0.72, 0.30, "grass_light", "south_center"),
        ((670356.2, 4539693.6), 0.74, 0.34, "grass_dark", "south_east"),
        ((670351.8, 4539695.2), 0.64, 0.28, "grass_light", "south_west"),
    ]
    for utm, width, height, material, name in grass_marks:
        if _inside_patch(patch, utm):
            _emit_grass_blades(mesh, origin, utm, width, height, material, name)


def _emit_grass_blades(
    mesh: BuildingMesh,
    origin,
    utm: tuple[float, float],
    width: float,
    height: float,
    material_key: str,
    name: str,
) -> None:
    cx = utm[0] - origin.x
    cy = utm[1] - origin.y
    z0 = 0.055
    for idx, ang in enumerate((-38.0, -16.0, 8.0, 31.0)):
        rad = math.radians(ang)
        dx = math.cos(rad) * width * 0.5
        dy = math.sin(rad) * width * 0.5
        mesh.add_quad(
            p0=(cx - dx, cy - dy, z0),
            p1=(cx - dx * 0.12, cy - dy * 0.12, z0 + height),
            p2=(cx + dx * 0.12, cy + dy * 0.12, z0 + height * 0.92),
            p3=(cx + dx, cy + dy, z0),
            role="Vegetation",
            surface_id=f"COURTYARD-147-GARDEN.grass_blades.{name}.{idx}",
            material_key=material_key,
        )


def _inside_patch(patch: Polygon, utm: tuple[float, float]) -> bool:
    return patch.buffer(0.05).contains(Point(*utm))


def _emit_map_tree(mesh: BuildingMesh, origin, utm: tuple[float, float]) -> None:
    """Mature courtyard tree from the Pervititch green symbol."""
    cx = utm[0] - origin.x
    cy = utm[1] - origin.y
    base = (cx, cy, 0.05)
    fork = (cx + 0.12, cy - 0.05, 3.65)
    _emit_cylinder(mesh, base, fork, 0.42, 0.26, 16, "tree_trunk", "tree.trunk.main")

    branches = [
        ((cx + 0.12, cy - 0.05, 2.55), (cx - 1.36, cy + 0.70, 4.95), 0.22, 0.11, "west"),
        ((cx + 0.10, cy - 0.04, 2.82), (cx + 1.42, cy + 0.62, 5.08), 0.21, 0.105, "east"),
        ((cx + 0.12, cy - 0.05, 3.10), (cx - 0.34, cy - 1.48, 5.02), 0.19, 0.095, "south"),
        ((cx + 0.12, cy - 0.05, 3.24), (cx + 0.42, cy + 1.48, 5.32), 0.19, 0.095, "north"),
        ((cx + 0.08, cy - 0.03, 3.48), (cx + 0.18, cy + 0.06, 6.12), 0.17, 0.085, "leader"),
    ]
    for start, end, r0, r1, name in branches:
        _emit_cylinder(mesh, start, end, r0, r1, 10, "tree_bark_dark", f"tree.branch.{name}")

    # Overlapping ellipsoid leaf masses make the tree read as a real mature
    # courtyard tree in orbit view, while staying light enough for the GLB.
    leaf_blobs = [
        ((cx, cy + 0.05, 5.72), (2.05, 1.72, 1.38), "tree_canopy"),
        ((cx - 1.14, cy + 0.50, 5.34), (1.55, 1.18, 1.00), "tree_canopy_dark"),
        ((cx + 1.12, cy + 0.42, 5.48), (1.52, 1.08, 0.98), "tree_canopy_light"),
        ((cx - 0.26, cy - 1.20, 5.22), (1.35, 1.12, 0.96), "tree_canopy_dark"),
        ((cx + 0.36, cy + 1.28, 5.65), (1.42, 1.05, 0.96), "tree_canopy_light"),
        ((cx + 0.16, cy + 0.08, 6.78), (1.34, 1.18, 1.05), "tree_canopy"),
        ((cx - 0.66, cy - 0.18, 6.16), (1.15, 0.95, 0.78), "tree_canopy_dark"),
        ((cx + 0.62, cy - 0.58, 5.96), (1.12, 0.88, 0.74), "tree_canopy_light"),
    ]
    for idx, (center, radii, material) in enumerate(leaf_blobs):
        _emit_leaf_ellipsoid(mesh, center, radii, material, f"tree.crown.{idx}")

    # Dappled ground shadow under the canopy gives scale and anchors the trunk.
    for idx, (rx, ry, mat, z) in enumerate((
        (2.25, 1.58, "grass_dark", 0.046),
        (1.62, 1.05, "garden_shrub", 0.049),
    )):
        _emit_ground_ellipse(mesh, (cx, cy, z), rx, ry, mat, f"tree.shadow_grass.{idx}")


def _emit_cylinder(
    mesh: BuildingMesh,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    r0: float,
    r1: float,
    segments: int,
    material_key: str,
    name: str,
) -> None:
    sx, sy, sz = start
    ex, ey, ez = end
    ax, ay, az = ex - sx, ey - sy, ez - sz
    length = math.sqrt(ax * ax + ay * ay + az * az)
    if length <= 0.01:
        return
    ux, uy, uz = ax / length, ay / length, az / length
    ref = (0.0, 0.0, 1.0) if abs(uz) < 0.92 else (1.0, 0.0, 0.0)
    vx, vy, vz = _cross((ux, uy, uz), ref)
    v_len = math.sqrt(vx * vx + vy * vy + vz * vz)
    vx, vy, vz = vx / v_len, vy / v_len, vz / v_len
    wx, wy, wz = _cross((ux, uy, uz), (vx, vy, vz))
    for i in range(segments):
        a0 = math.tau * i / segments
        a1 = math.tau * (i + 1) / segments
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        p0 = (sx + (vx * c0 + wx * s0) * r0, sy + (vy * c0 + wy * s0) * r0, sz + (vz * c0 + wz * s0) * r0)
        p1 = (sx + (vx * c1 + wx * s1) * r0, sy + (vy * c1 + wy * s1) * r0, sz + (vz * c1 + wz * s1) * r0)
        p2 = (ex + (vx * c1 + wx * s1) * r1, ey + (vy * c1 + wy * s1) * r1, ez + (vz * c1 + wz * s1) * r1)
        p3 = (ex + (vx * c0 + wx * s0) * r1, ey + (vy * c0 + wy * s0) * r1, ez + (vz * c0 + wz * s0) * r1)
        mesh.add_quad(p0, p1, p2, p3, role="TreeTrunk",
                      surface_id=f"COURTYARD-147-GARDEN.{name}.{i}",
                      material_key=material_key)


def _emit_leaf_ellipsoid(
    mesh: BuildingMesh,
    center: tuple[float, float, float],
    radii: tuple[float, float, float],
    material_key: str,
    name: str,
    rings: int = 7,
    segments: int = 12,
) -> None:
    cx, cy, cz = center
    rx, ry, rz = radii
    verts: list[list[int]] = []
    for j in range(rings + 1):
        phi = -math.pi / 2.0 + math.pi * j / rings
        row = []
        for i in range(segments):
            theta = math.tau * i / segments
            # Slightly uneven canopy silhouette; deterministic and subtle.
            wobble = 1.0 + 0.07 * math.sin(theta * 3.0 + j * 0.8)
            x = cx + math.cos(phi) * math.cos(theta) * rx * wobble
            y = cy + math.cos(phi) * math.sin(theta) * ry * (1.0 + 0.04 * math.cos(theta * 2.0))
            z = cz + math.sin(phi) * rz
            row.append(mesh.add_vertex(x, y, z))
        verts.append(row)
    for j in range(rings):
        for i in range(segments):
            mesh.add_face(
                [
                    verts[j][i],
                    verts[j][(i + 1) % segments],
                    verts[j + 1][(i + 1) % segments],
                    verts[j + 1][i],
                ],
                role="Vegetation",
                surface_id=f"COURTYARD-147-GARDEN.{name}.{j}.{i}",
                material_key=material_key,
            )


def _emit_ground_ellipse(
    mesh: BuildingMesh,
    center: tuple[float, float, float],
    rx: float,
    ry: float,
    material_key: str,
    name: str,
    segments: int = 24,
) -> None:
    cx, cy, cz = center
    idx = [
        mesh.add_vertex(
            cx + math.cos(math.tau * i / segments) * rx,
            cy + math.sin(math.tau * i / segments) * ry,
            cz,
        )
        for i in range(segments)
    ]
    mesh.add_face(idx, role="LandscapeSurface",
                  surface_id=f"COURTYARD-147-GARDEN.{name}",
                  material_key=material_key)


def _cross(a, b) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )
