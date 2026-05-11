"""PRD-003 · §5 — pure-Python mesh-graph intermediate.

No Blender / no ifcopenshell imports here — so this layer runs in the plain
venv and is unit-testable. Backends (glTF, IFC, Blender) consume the same
graph through the Adapter pattern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

from ..common.prd import prd
from ..modeling.building import FacadePalette

SemanticRole = Literal[
    "GroundSurface",
    "WallSurface",
    "RoofSurface",
    "Window",
    "Door",
    "ClosureSurface",
    "OuterCeilingSurface",
    "InteriorWallSurface",
    "FloorSurface",
    "Chimney",
    "Skylight",
    "MonumentBody",
    "LandscapeSurface",
    "Vegetation",
    "TreeTrunk",
]

MaterialKey = Literal[
    "wall_main", "wall_accent", "trim", "shutters", "roof",
    "gf_shopfront", "window_glass", "door_panel", "chimney_brick",
    "monument_stone", "stub_marker",
    "tile_terracotta", "tile_marseille", "sheet_metal_grey",
    "vault_roof_masonry", "roof_unknown_muted", "dome_lead",
    "plinth_stone", "cornice_paint", "balcony_iron",
    "fountain_shadow", "fountain_plaque_green", "fountain_gold",
    "fountain_stone_dark", "fountain_basin_stone", "fountain_metal",
    "fountain_water", "fountain_tile_blue", "fountain_tile_green",
    "fountain_tile_red", "fountain_side_door", "fountain_side_door_shadow",
    "wood_grain_dark", "wood_batten",
    "grass_ground", "grass_light", "grass_dark", "garden_shrub",
    "tree_canopy", "tree_canopy_light", "tree_canopy_dark",
    "tree_trunk", "tree_bark_dark",
    "church_door_white", "church_trim_ochre", "church_iron_dark",
    "church_stone_light", "church_stone_shadow", "church_panel_shadow",
    "church_glass_blue", "church_plaque_blue", "church_lamp_gold",
]


@dataclass
class Vertex:
    x: float
    y: float
    z: float

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class Face:
    vertices: list[int]            # indices into BuildingMesh.vertices
    semantic_role: SemanticRole
    surface_id: str                # stable id, e.g. "N-44.wall.E.2"
    material_key: MaterialKey
    storey_level: int | None = None
    metadata: dict = field(default_factory=dict)


@prd("003", "§5 BuildingMesh")
@dataclass
class BuildingMesh:
    parcel_id: str
    vertices: list[Vertex] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)
    placement_origin_utm: tuple[float, float] = (0.0, 0.0)
    placement_rotation_deg: float = 0.0
    palette: FacadePalette | None = None
    metadata: dict = field(default_factory=dict)

    # -- mutation helpers ----------------------------------------------------
    def add_vertex(self, x: float, y: float, z: float) -> int:
        self.vertices.append(Vertex(x, y, z))
        return len(self.vertices) - 1

    def add_face(
        self,
        v_indices: list[int],
        role: SemanticRole,
        surface_id: str,
        material_key: MaterialKey,
        storey_level: int | None = None,
        **metadata,
    ) -> Face:
        face = Face(
            vertices=list(v_indices),
            semantic_role=role,
            surface_id=surface_id,
            material_key=material_key,
            storey_level=storey_level,
            metadata=metadata,
        )
        self.faces.append(face)
        return face

    def add_quad(
        self,
        p0: tuple[float, float, float],
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        p3: tuple[float, float, float],
        role: SemanticRole,
        surface_id: str,
        material_key: MaterialKey,
        storey_level: int | None = None,
    ) -> Face:
        idx = [self.add_vertex(*p) for p in (p0, p1, p2, p3)]
        return self.add_face(idx, role, surface_id, material_key, storey_level)

    # -- summary helpers -----------------------------------------------------
    def face_count_by_role(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.faces:
            out[f.semantic_role] = out.get(f.semantic_role, 0) + 1
        return out


@dataclass
class GroundPlane:
    half_extent_m: float
    z: float = -0.01
    color_rgb: tuple[int, int, int] = (115, 110, 100)


@dataclass
class CameraPose:
    position: tuple[float, float, float]
    target: tuple[float, float, float] = (0.0, 0.0, 0.0)
    yfov_deg: float = 45.0


@dataclass
class DirectionalLight:
    direction: tuple[float, float, float]   # world-space unit vector (points *from* sun)
    color_rgb: tuple[int, int, int] = (255, 240, 210)
    intensity: float = 3.0                  # lumens/sr (gltf 2.0 convention)


@dataclass
class SceneGraph:
    """Collection of BuildingMeshes + the block centroid used as world origin."""
    buildings: list[BuildingMesh] = field(default_factory=list)
    block_centroid_utm: tuple[float, float] = (0.0, 0.0)
    metadata: dict = field(default_factory=dict)
    ground: GroundPlane | None = None
    camera: CameraPose | None = None
    lights: list[DirectionalLight] = field(default_factory=list)

    def face_count_by_role(self) -> dict[str, int]:
        agg: dict[str, int] = {}
        for b in self.buildings:
            for role, n in b.face_count_by_role().items():
                agg[role] = agg.get(role, 0) + n
        return agg
