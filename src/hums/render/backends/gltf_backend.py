"""PRD-003 · §8 — glTF 2.0 (.glb) writer.

Each building becomes a glTF node. Within a building, faces are grouped by
``(semantic_role, material_key)`` into separate primitives so viewers can
colour-code LOD3 surface roles. Palette colours come from FacadePalette.

Coordinate convention: block-centred Z-up (as produced by SceneAssembler).
glTF is Y-up by default, so we rotate the root node -90° about X when writing.
"""
from __future__ import annotations
import math
import struct
from pathlib import Path

import numpy as np
import pygltflib as gl

from ...common.prd import prd
from ..mesh_graph import BuildingMesh, Face, SceneGraph
from ._triangulate import fan


@prd("003", "§8 GltfBackend")
class GltfBackend:
    def export_scene(self, scene: SceneGraph, out_path: Path) -> None:
        root = _new_gltf()
        buffer = bytearray()
        placements = {p["parcel_id"]: p for p in scene.metadata.get("placements", [])}

        # Y-up wrapper node (rotates our Z-up world).
        _set_y_up_root(root)

        for mesh in scene.buildings:
            placement = placements.get(mesh.parcel_id, {
                "translation": [0, 0, 0], "rotation_deg_z": 0.0,
            })
            self._add_building(root, buffer, mesh, placement)

        _finalize(root, buffer, out_path)

    def export_building(self, mesh: BuildingMesh, out_path: Path) -> None:
        root = _new_gltf()
        buffer = bytearray()
        _set_y_up_root(root)
        self._add_building(root, buffer, mesh, {"translation": [0, 0, 0], "rotation_deg_z": 0.0})
        _finalize(root, buffer, out_path)

    # -- helpers --------------------------------------------------------------
    def _add_building(self, root: gl.GLTF2, buffer: bytearray, mesh: BuildingMesh, placement: dict) -> None:
        if not mesh.vertices or not mesh.faces:
            return
        palette = mesh.palette

        # Group faces by (role, material_key)
        groups: dict[tuple[str, str], list[Face]] = {}
        for f in mesh.faces:
            groups.setdefault((f.semantic_role, f.material_key), []).append(f)

        primitives: list[gl.Primitive] = []
        for (role, mat_key), faces in groups.items():
            prim = self._build_primitive(root, buffer, mesh, faces, role, mat_key, palette)
            if prim is not None:
                primitives.append(prim)

        if not primitives:
            return

        gltf_mesh = gl.Mesh(primitives=primitives, name=mesh.parcel_id)
        mesh_index = len(root.meshes)
        root.meshes.append(gltf_mesh)

        # Y-up placement: world (ox, oy, 0) → glTF (ox, 0, -oy); rotation around Z → around Y(-)
        tx, ty, tz = placement.get("translation", [0, 0, 0])
        node = gl.Node(
            mesh=mesh_index,
            name=mesh.parcel_id,
            translation=[tx, tz, -ty],
            rotation=_euler_z_to_quat_y_up(placement.get("rotation_deg_z", 0.0)),
            extras={
                "parcel_id": mesh.parcel_id,
                "structure_type": mesh.metadata.get("structure_type"),
                "footprint_source": mesh.metadata.get("footprint_source"),
                "notes": mesh.metadata.get("notes"),
            },
        )
        node_index = len(root.nodes)
        root.nodes.append(node)
        # attach under y-up root (node 0)
        if root.nodes[0].children is None:
            root.nodes[0].children = []
        root.nodes[0].children.append(node_index)

    def _build_primitive(self, root, buffer, mesh, faces, role, mat_key, palette):
        # Collect unique vertices used by these faces
        tri_indices: list[int] = []
        pos_bytes = bytearray()
        local_map: dict[int, int] = {}

        def local(global_idx: int) -> int:
            if global_idx not in local_map:
                local_map[global_idx] = len(local_map)
                v = mesh.vertices[global_idx]
                pos_bytes.extend(struct.pack("<fff", v.x, v.y, v.z))
            return local_map[global_idx]

        for face in faces:
            for tri in fan(face.vertices):
                for gidx in tri:
                    tri_indices.append(local(gidx))

        if not tri_indices:
            return None

        positions = np.frombuffer(pos_bytes, dtype=np.float32).reshape(-1, 3)
        indices = np.array(tri_indices, dtype=np.uint32)

        # Buffer views + accessors
        pos_view = _append_view(root, buffer, pos_bytes, target=gl.ARRAY_BUFFER)
        idx_bytes = indices.tobytes()
        idx_view = _append_view(root, buffer, idx_bytes, target=gl.ELEMENT_ARRAY_BUFFER)

        pos_accessor = _new_accessor(
            root, pos_view, len(positions),
            type_=gl.VEC3, component=gl.FLOAT,
            mins=positions.min(axis=0).tolist(),
            maxs=positions.max(axis=0).tolist(),
        )
        idx_accessor = _new_accessor(
            root, idx_view, len(indices),
            type_=gl.SCALAR, component=gl.UNSIGNED_INT,
        )

        material_idx = _material_for(root, palette, mat_key, mesh.metadata)
        prim = gl.Primitive(
            attributes=gl.Attributes(POSITION=pos_accessor),
            indices=idx_accessor,
            material=material_idx,
            extras={"semantic_role": role, "material_key": mat_key, "face_count": len(faces)},
        )
        return prim


# ---------- glTF plumbing ------------------------------------------------------

def _new_gltf() -> gl.GLTF2:
    root = gl.GLTF2(
        asset=gl.Asset(version="2.0", generator="hums/PRD-003"),
        scenes=[gl.Scene(nodes=[0], name="Block 147")],
        scene=0,
    )
    return root


def _set_y_up_root(root: gl.GLTF2) -> None:
    # Add identity root node 0 — children appended later.
    root.nodes.append(gl.Node(name="block147_root", children=[]))


def _append_view(root: gl.GLTF2, buffer: bytearray, data: bytes, target: int) -> int:
    # align to 4 bytes
    while len(buffer) % 4 != 0:
        buffer.append(0)
    offset = len(buffer)
    buffer.extend(data)
    view = gl.BufferView(buffer=0, byteOffset=offset, byteLength=len(data), target=target)
    root.bufferViews.append(view)
    return len(root.bufferViews) - 1


def _new_accessor(root, view_idx, count, type_, component, mins=None, maxs=None) -> int:
    acc = gl.Accessor(
        bufferView=view_idx, componentType=component, count=count, type=type_,
    )
    if mins is not None:
        acc.min = mins
    if maxs is not None:
        acc.max = maxs
    root.accessors.append(acc)
    return len(root.accessors) - 1


def _material_for(root: gl.GLTF2, palette, material_key: str, meta: dict) -> int:
    if not hasattr(root, "_material_cache"):
        root._material_cache = {}  # type: ignore[attr-defined]
    cache_key = f"{material_key}|{meta.get('footprint_source')}"
    if cache_key in root._material_cache:  # type: ignore[attr-defined]
        return root._material_cache[cache_key]  # type: ignore[attr-defined]

    rgb = _color_for(palette, material_key)
    # Tint stubs for visual clarity
    alpha = 0.75 if meta.get("footprint_source") == "stub" else 1.0
    mat = gl.Material(
        name=material_key,
        pbrMetallicRoughness=gl.PbrMetallicRoughness(
            baseColorFactor=[rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, alpha],
            metallicFactor=0.0,
            roughnessFactor=0.85 if material_key != "window_glass" else 0.25,
        ),
        alphaMode="BLEND" if alpha < 1.0 or material_key == "window_glass" else "OPAQUE",
    )
    idx = len(root.materials)
    root.materials.append(mat)
    root._material_cache[cache_key] = idx  # type: ignore[attr-defined]
    return idx


def _color_for(palette, material_key: str) -> tuple[int, int, int]:
    # Fallback stone-ish when no palette set
    fallback = (180, 170, 150)
    if palette is None:
        return fallback
    p = palette if isinstance(palette, dict) else palette.__dict__
    mapping = {
        "wall_main": p.get("wall_main") or fallback,
        "wall_accent": p.get("wall_accent") or p.get("wall_main") or fallback,
        "trim": p.get("trim") or (80, 60, 40),
        "shutters": p.get("shutters") or (40, 30, 20),
        "roof": p.get("roof") or (142, 74, 50),
        "gf_shopfront": p.get("gf_shopfront") or p.get("wall_main") or fallback,
        "window_glass": (130, 170, 200),
        "door_panel": (70, 45, 30),
        "chimney_brick": (120, 60, 45),
        "monument_stone": (220, 205, 180),
        "stub_marker": (200, 200, 80),
    }
    v = mapping.get(material_key, fallback)
    return (int(v[0]), int(v[1]), int(v[2]))


def _euler_z_to_quat_y_up(deg_z: float) -> list[float]:
    # Rotation around world Z in our frame becomes rotation around glTF -Y.
    theta = math.radians(-deg_z)
    half = theta / 2.0
    return [0.0, math.sin(half), 0.0, math.cos(half)]


def _finalize(root: gl.GLTF2, buffer: bytearray, out_path: Path) -> None:
    # Pad to 4 bytes
    while len(buffer) % 4 != 0:
        buffer.append(0)
    root.buffers.append(gl.Buffer(byteLength=len(buffer)))
    root.set_binary_blob(bytes(buffer))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    root.save_binary(str(out_path))
