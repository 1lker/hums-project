"""Map-derived courtyard/garden surfaces for Block 147."""
from __future__ import annotations
import json
import math

from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

from ...common.paths import BLOCK_GEOJSON, FOOTPRINTS_GEOJSON, NON_PARCEL_FOOTPRINTS_GEOJSON
from ...common.prd import prd
from ...modeling.building import FacadePalette
from ..mesh_graph import BuildingMesh


# Manual crop of the light-green open courtyard/garden marked "(147)" on the
# Pervititch raster. The final polygon is clipped by the actual block void, so
# this cannot cover traced KML/SHP buildings.
COURTYARD_147_BOUNDS_UTM = (670347.0, 4539690.0, 670359.0, 4539704.0)

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
                    "map_reading": "Light green open Block 147 courtyard/garden: grass/low planting with a small tree/shrub mark.",
                    "bounds_utm": COURTYARD_147_BOUNDS_UTM,
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

        # The map shows a few green brush marks rather than a formal garden
        # plan. Add restrained tufts and one small tree/shrub, clipped visually
        # to the known green courtyard area.
        _emit_grass_tuft(mesh, c, (670350.2, 4539702.1), 0.85, 0.55, "upper_west")
        _emit_grass_tuft(mesh, c, (670354.7, 4539696.2), 1.15, 0.7, "center")
        _emit_grass_tuft(mesh, c, (670356.4, 4539692.4), 1.35, 0.9, "south_east")
        _emit_small_tree(mesh, c, (670356.2, 4539694.3))
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


def _emit_small_tree(mesh: BuildingMesh, origin, utm: tuple[float, float]) -> None:
    cx = utm[0] - origin.x
    cy = utm[1] - origin.y
    trunk_h = 1.35
    trunk_r = 0.08
    crown_z = trunk_h + 0.45
    crown_r = 0.75

    # Simple square trunk.
    for idx, (nx, ny) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):
        if nx:
            p0 = (cx + nx * trunk_r, cy - trunk_r, 0.05)
            p1 = (cx + nx * trunk_r, cy - trunk_r, trunk_h)
            p2 = (cx + nx * trunk_r, cy + trunk_r, trunk_h)
            p3 = (cx + nx * trunk_r, cy + trunk_r, 0.05)
        else:
            p0 = (cx - trunk_r, cy + ny * trunk_r, 0.05)
            p1 = (cx - trunk_r, cy + ny * trunk_r, trunk_h)
            p2 = (cx + trunk_r, cy + ny * trunk_r, trunk_h)
            p3 = (cx + trunk_r, cy + ny * trunk_r, 0.05)
        mesh.add_quad(
            p0=p0,
            p1=p1,
            p2=p2,
            p3=p3,
            role="TreeTrunk",
            surface_id=f"COURTYARD-147-GARDEN.tree.trunk.{idx}",
            material_key="tree_trunk",
        )

    # Crossed billboard canopy reads as a small map-indicated tree/shrub.
    for idx, ang in enumerate((0.0, 90.0, 45.0, -45.0)):
        rad = math.radians(ang)
        dx = math.cos(rad) * crown_r
        dy = math.sin(rad) * crown_r
        mesh.add_quad(
            p0=(cx - dx, cy - dy, crown_z - 0.55),
            p1=(cx - dx * 0.35, cy - dy * 0.35, crown_z + 0.55),
            p2=(cx + dx * 0.35, cy + dy * 0.35, crown_z + 0.55),
            p3=(cx + dx, cy + dy, crown_z - 0.55),
            role="Vegetation",
            surface_id=f"COURTYARD-147-GARDEN.tree.canopy.{idx}",
            material_key="tree_canopy",
        )
