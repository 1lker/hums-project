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
]

MaterialKey = Literal[
    "wall_main", "wall_accent", "trim", "shutters", "roof",
    "gf_shopfront", "window_glass", "door_panel", "chimney_brick",
    "monument_stone", "stub_marker",
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
class SceneGraph:
    """Collection of BuildingMeshes + the block centroid used as world origin."""
    buildings: list[BuildingMesh] = field(default_factory=list)
    block_centroid_utm: tuple[float, float] = (0.0, 0.0)
    metadata: dict = field(default_factory=dict)

    def face_count_by_role(self) -> dict[str, int]:
        agg: dict[str, int] = {}
        for b in self.buildings:
            for role, n in b.face_count_by_role().items():
                agg[role] = agg.get(role, 0) + n
        return agg
