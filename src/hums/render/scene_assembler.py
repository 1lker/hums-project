"""PRD-003 · §6.4 — place each BuildingMesh into world coordinates.

World frame = UTM 35N translated so the block centroid is the origin, and
each building is rotated by its ``street_rotation_deg`` before translation.
This keeps the block centred near (0,0) so backends don't need to deal with
million-metre UTM offsets (numerical noise, precision loss in glTF float32).
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from ..common.prd import prd
from .mesh_graph import (
    BuildingMesh, CameraPose, DirectionalLight, GroundPlane, SceneGraph,
)


@dataclass
class PlacedMesh:
    mesh: BuildingMesh
    world_matrix: tuple[tuple[float, ...], ...]  # 4x4 row-major


@prd("003", "§6.4 SceneAssembler")
class SceneAssembler:
    def assemble(self, meshes: list[BuildingMesh], block_centroid_utm: tuple[float, float]) -> SceneGraph:
        scene = SceneGraph(buildings=meshes, block_centroid_utm=block_centroid_utm)
        scene.metadata["placements"] = [
            self._compute_placement(m, block_centroid_utm) for m in meshes
        ]

        # Scene context — ground + camera + sun.
        extent = self._scene_extent(meshes)
        scene.ground = GroundPlane(half_extent_m=extent + 25.0)
        scene.camera = CameraPose(
            position=(-extent * 0.9, -extent * 0.7, extent * 0.55),
            target=(0.0, 0.0, extent * 0.2),
        )
        scene.lights = [
            DirectionalLight(direction=(0.35, 0.45, -0.82)),   # SE afternoon sun
        ]
        return scene

    @staticmethod
    def _scene_extent(meshes: list[BuildingMesh]) -> float:
        placements = []
        for m in meshes:
            placements.append(abs(m.placement_origin_utm[0]))
            placements.append(abs(m.placement_origin_utm[1]))
        # very rough half-extent in local block frame
        return max(25.0, max((abs(v.x) for m in meshes for v in m.vertices), default=25.0))

    @staticmethod
    def _compute_placement(mesh: BuildingMesh, block_centroid_utm: tuple[float, float]) -> dict:
        ox = mesh.placement_origin_utm[0] - block_centroid_utm[0]
        oy = mesh.placement_origin_utm[1] - block_centroid_utm[1]
        theta = math.radians(mesh.placement_rotation_deg)
        c = math.cos(theta)
        s = math.sin(theta)
        return {
            "parcel_id": mesh.parcel_id,
            "translation": [round(ox, 3), round(oy, 3), 0.0],
            "rotation_deg_z": round(mesh.placement_rotation_deg, 3),
            "matrix_4x4": [
                [c, -s, 0.0, ox],
                [s, c, 0.0, oy],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        }
