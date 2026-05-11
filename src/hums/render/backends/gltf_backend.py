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

        # Single Z-up → Y-up rotation at the root; per-building nodes stay in Z-up.
        _set_y_up_root(root)

        for mesh in scene.buildings:
            placement = placements.get(mesh.parcel_id, {
                "translation": [0.0, 0.0, 0.0], "rotation_deg_z": 0.0,
            })
            self._add_building(root, buffer, mesh, placement)

        if scene.ground is not None:
            _add_ground_plane(root, buffer, scene.ground)
        # Sidewalk ring hugging the block outline (added for visual framing).
        block_ring = scene.metadata.get("block_ring_local")
        if block_ring:
            _add_sidewalk_ring(root, buffer, block_ring)
        if scene.camera is not None:
            _add_camera(root, scene.camera)
        if scene.lights:
            _add_lights(root, scene.lights)

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

        # Everything stays in Z-up. The root node (created by _set_y_up_root)
        # rotates the entire scene -90° about X for glTF's Y-up convention.
        tx, ty, tz = placement.get("translation", [0.0, 0.0, 0.0])
        node = gl.Node(
            mesh=mesh_index,
            name=mesh.parcel_id,
            translation=[tx, ty, tz],
            rotation=_quat_rot_z(placement.get("rotation_deg_z", 0.0)),
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
        asset=gl.Asset(version="2.0", generator="hums/PRD-004"),
        scenes=[gl.Scene(nodes=[0], name="Block 147")],
        scene=0,
    )
    root.cameras = []
    return root


def _set_y_up_root(root: gl.GLTF2) -> None:
    """Create root node 0 with a -90° rotation about X to convert our Z-up
    world to glTF's Y-up convention. Child nodes can stay in Z-up locally.
    """
    half = math.radians(-90.0) / 2.0
    root.nodes.append(gl.Node(
        name="block147_root",
        children=[],
        rotation=[math.sin(half), 0.0, 0.0, math.cos(half)],
    ))


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
    rgb = _color_for(palette, material_key)
    # Tint stubs for visual clarity
    alpha = 0.75 if meta.get("footprint_source") == "stub" else 1.0
    if material_key == "window_glass":
        alpha = min(alpha, 0.45)
    cache_key = f"{material_key}|{meta.get('footprint_source')}|{rgb}|{alpha}"
    if cache_key in root._material_cache:  # type: ignore[attr-defined]
        return root._material_cache[cache_key]  # type: ignore[attr-defined]

    metallic = 0.0
    roughness = 0.85
    if material_key == "window_glass":
        roughness = 0.25
    elif material_key in {"sheet_metal_grey", "dome_lead"}:
        metallic = 0.18
        roughness = 0.42
    elif material_key in {"tile_terracotta", "tile_marseille", "vault_roof_masonry"}:
        roughness = 0.92
    elif material_key == "roof_unknown_muted":
        roughness = 0.78

    mat = gl.Material(
        name=material_key,
        pbrMetallicRoughness=gl.PbrMetallicRoughness(
            baseColorFactor=[rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, alpha],
            metallicFactor=metallic,
            roughnessFactor=roughness,
        ),
        alphaMode="BLEND" if alpha < 1.0 or material_key == "window_glass" else "OPAQUE",
        # Walls, roofs, sills, etc. are thin single-sided quads in the current
        # mesh. Marking doubleSided stops the viewer from culling faces that
        # happen to point away from the camera — buildings read as solid
        # objects rather than peeled-open shells.
        doubleSided=True,
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
        "chimney_brick": (146, 72, 55),
        "monument_stone": (220, 205, 180),
        "stub_marker": (200, 200, 80),
        "tile_terracotta": (166, 82, 52),
        "tile_marseille": (185, 88, 48),
        "sheet_metal_grey": (104, 111, 113),
        "vault_roof_masonry": (178, 160, 132),
        "roof_unknown_muted": (126, 112, 94),
        "plinth_stone": (160, 148, 130),
        "cornice_paint": (236, 225, 205),
        "dome_lead": (112, 120, 122),
        "balcony_iron": (45, 40, 38),
        "wood_grain_dark": (96, 61, 34),
        "wood_batten": (118, 76, 42),
        "grass_ground": (126, 150, 88),
        "garden_shrub": (86, 126, 62),
        "tree_canopy": (78, 118, 58),
        "tree_trunk": (96, 65, 42),
    }
    v = mapping.get(material_key, fallback)
    return (int(v[0]), int(v[1]), int(v[2]))


def _quat_rot_z(deg_z: float) -> list[float]:
    """Quaternion for rotation about world Z (our Z-up frame)."""
    half = math.radians(deg_z) / 2.0
    return [0.0, 0.0, math.sin(half), math.cos(half)]


def _add_ground_plane(root: gl.GLTF2, buffer: bytearray, ground) -> None:
    import struct
    h = ground.half_extent_m
    z = ground.z
    # Two triangles CCW from above (normal +Z)
    positions = [
        (-h, -h, z), (h, -h, z), (h, h, z),
        (-h, -h, z), (h, h, z), (-h, h, z),
    ]
    pos_bytes = b"".join(struct.pack("<fff", *p) for p in positions)
    indices = list(range(6))
    idx_bytes = b"".join(struct.pack("<I", i) for i in indices)

    pos_view = _append_view(root, buffer, pos_bytes, target=gl.ARRAY_BUFFER)
    idx_view = _append_view(root, buffer, idx_bytes, target=gl.ELEMENT_ARRAY_BUFFER)
    pos_acc = _new_accessor(root, pos_view, 6, type_=gl.VEC3, component=gl.FLOAT,
                            mins=[-h, -h, z], maxs=[h, h, z])
    idx_acc = _new_accessor(root, idx_view, 6, type_=gl.SCALAR, component=gl.UNSIGNED_INT)

    mat = gl.Material(
        name="ground_cobble",
        pbrMetallicRoughness=gl.PbrMetallicRoughness(
            baseColorFactor=[ground.color_rgb[0] / 255, ground.color_rgb[1] / 255, ground.color_rgb[2] / 255, 1.0],
            metallicFactor=0.0,
            roughnessFactor=0.95,
        ),
        doubleSided=True,
    )
    root.materials.append(mat)
    prim = gl.Primitive(
        attributes=gl.Attributes(POSITION=pos_acc), indices=idx_acc,
        material=len(root.materials) - 1,
        extras={"semantic_role": "GroundPlane"},
    )
    mesh = gl.Mesh(primitives=[prim], name="ground")
    root.meshes.append(mesh)
    node = gl.Node(name="ground", mesh=len(root.meshes) - 1)
    root.nodes.append(node)
    root.nodes[0].children.append(len(root.nodes) - 1)


def _add_sidewalk_ring(root: gl.GLTF2, buffer: bytearray, block_ring: list[list[float]]) -> None:
    """Raised sidewalk strip hugging the block — visually frames the buildings."""
    import struct
    from shapely.geometry import Polygon
    import numpy as np

    if len(block_ring) < 3:
        return
    inner = Polygon([tuple(p) for p in block_ring])
    outer = inner.buffer(2.0, join_style=2)
    if outer.is_empty or outer.geom_type != "Polygon":
        return
    outer_ring = list(outer.exterior.coords)[:-1]
    inner_ring = [tuple(p) for p in block_ring]

    z_top = 0.15
    positions: list[tuple[float, float, float]] = []
    indices: list[int] = []

    # Build tri strip between outer (lower) and inner (upper) rings.
    n = len(outer_ring)
    # Sample inner ring to match outer length (simple resampling)
    inner_len = len(inner_ring)
    mapping = [int(round(i * inner_len / n)) % inner_len for i in range(n)]

    def add_v(p):
        positions.append(p)
        return len(positions) - 1

    base_outer = [add_v((x, y, 0.0)) for (x, y) in outer_ring]
    top_outer = [add_v((x, y, z_top)) for (x, y) in outer_ring]
    top_inner = [add_v((inner_ring[mapping[i]][0], inner_ring[mapping[i]][1], z_top)) for i in range(n)]
    base_inner = [add_v((inner_ring[mapping[i]][0], inner_ring[mapping[i]][1], 0.0)) for i in range(n)]

    # outer curb face + top + inner curb face
    for i in range(n):
        j = (i + 1) % n
        # outer face (vertical)
        indices.extend([base_outer[i], top_outer[i], top_outer[j]])
        indices.extend([base_outer[i], top_outer[j], base_outer[j]])
        # top surface
        indices.extend([top_outer[i], top_inner[i], top_inner[j]])
        indices.extend([top_outer[i], top_inner[j], top_outer[j]])
        # inner curb face
        indices.extend([top_inner[i], base_inner[i], base_inner[j]])
        indices.extend([top_inner[i], base_inner[j], top_inner[j]])

    pos_bytes = b"".join(struct.pack("<fff", *p) for p in positions)
    idx_bytes = b"".join(struct.pack("<I", i) for i in indices)
    pos_view = _append_view(root, buffer, pos_bytes, target=gl.ARRAY_BUFFER)
    idx_view = _append_view(root, buffer, idx_bytes, target=gl.ELEMENT_ARRAY_BUFFER)
    arr = np.array(positions, dtype=np.float32)
    pos_acc = _new_accessor(root, pos_view, len(positions), type_=gl.VEC3, component=gl.FLOAT,
                            mins=arr.min(axis=0).tolist(), maxs=arr.max(axis=0).tolist())
    idx_acc = _new_accessor(root, idx_view, len(indices), type_=gl.SCALAR, component=gl.UNSIGNED_INT)

    mat = gl.Material(
        name="sidewalk_stone",
        pbrMetallicRoughness=gl.PbrMetallicRoughness(
            baseColorFactor=[0.58, 0.56, 0.52, 1.0],
            metallicFactor=0.0, roughnessFactor=0.90,
        ),
        doubleSided=True,
    )
    root.materials.append(mat)
    prim = gl.Primitive(
        attributes=gl.Attributes(POSITION=pos_acc), indices=idx_acc,
        material=len(root.materials) - 1,
        extras={"semantic_role": "Sidewalk"},
    )
    mesh_g = gl.Mesh(primitives=[prim], name="sidewalk")
    root.meshes.append(mesh_g)
    node = gl.Node(name="sidewalk", mesh=len(root.meshes) - 1)
    root.nodes.append(node)
    root.nodes[0].children.append(len(root.nodes) - 1)


def _add_camera(root: gl.GLTF2, cam) -> None:
    root.cameras.append(gl.Camera(
        type="perspective",
        perspective=gl.Perspective(
            yfov=math.radians(cam.yfov_deg),
            znear=0.1, zfar=500.0, aspectRatio=16 / 9,
        ),
        name="hero_camera",
    ))
    # Position the camera node. Target-aware look-at is not in the glTF spec —
    # simplest: place camera + compute a rotation from (+X forward) to (target - position).
    import math as _m
    px, py, pz = cam.position
    tx, ty, tz = cam.target
    dx, dy, dz = tx - px, ty - py, tz - pz
    # we'll hand-compute a look-at-y-up quaternion AFTER the root -90°X rotates
    # the scene. In glTF Y-up space, our world Z maps to glTF Y; world Y maps
    # to glTF -Z. So camera position in glTF Y-up:
    cam_pos_glu = (px, pz, -py)
    cam_target_glu = (tx, tz, -ty)
    rot = _look_at_quat(cam_pos_glu, cam_target_glu)

    cam_node = gl.Node(
        name="hero_camera",
        camera=len(root.cameras) - 1,
        translation=list(cam_pos_glu),
        rotation=list(rot),
    )
    # camera is not under the Z-up root node — attach at scene root level.
    root.nodes.append(cam_node)
    cam_idx = len(root.nodes) - 1
    # Ensure the scene includes it
    if cam_idx not in root.scenes[0].nodes:
        root.scenes[0].nodes.append(cam_idx)


def _add_lights(root: gl.GLTF2, lights) -> None:
    if root.extensionsUsed is None:
        root.extensionsUsed = []
    if "KHR_lights_punctual" not in root.extensionsUsed:
        root.extensionsUsed.append("KHR_lights_punctual")

    entries = []
    for L in lights:
        entries.append({
            "type": "directional",
            "color": [L.color_rgb[0] / 255, L.color_rgb[1] / 255, L.color_rgb[2] / 255],
            "intensity": L.intensity,
            "name": "sun",
        })
    root.extensions = root.extensions or {}
    root.extensions["KHR_lights_punctual"] = {"lights": entries}

    # Attach one light node per light; default glTF directional light points -Y
    # in node-local frame, so rotate the node to align -Y with our world direction.
    for i, L in enumerate(lights):
        # Convert world Z-up direction to glTF Y-up
        dx, dy, dz = L.direction
        glu_dir = (dx, dz, -dy)
        rot = _dir_to_minus_y(glu_dir)
        node = gl.Node(
            name=f"light_{i}",
            extensions={"KHR_lights_punctual": {"light": i}},
            rotation=list(rot),
        )
        root.nodes.append(node)
        root.scenes[0].nodes.append(len(root.nodes) - 1)


def _look_at_quat(pos, target):
    """Return a quaternion that rotates -Z (glTF camera forward) to (target-pos),
    keeping +Y world-up as close to local up as possible. Y-up glTF space."""
    import numpy as np
    forward = np.array([target[0] - pos[0], target[1] - pos[1], target[2] - pos[2]], dtype=float)
    forward /= np.linalg.norm(forward) or 1.0
    world_up = np.array([0.0, 1.0, 0.0])
    right = np.cross(world_up, -forward)
    right_norm = np.linalg.norm(right)
    if right_norm < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    else:
        right /= right_norm
    up = np.cross(-forward, right)
    # build rotation matrix [right, up, -forward] and convert to quaternion
    m = np.stack([right, up, -forward], axis=1)
    return _matrix_to_quat(m)


def _dir_to_minus_y(direction):
    """Quaternion that rotates the default -Y direction to `direction`."""
    import numpy as np
    target = np.array(direction, dtype=float)
    target /= np.linalg.norm(target) or 1.0
    default = np.array([0.0, -1.0, 0.0])
    v = np.cross(default, target)
    s = float(np.linalg.norm(v))
    c = float(np.dot(default, target))
    if s < 1e-8:
        return [0.0, 0.0, 0.0, 1.0] if c > 0 else [1.0, 0.0, 0.0, 0.0]
    axis = v / s
    angle = math.atan2(s, c)
    half = angle / 2.0
    sh = math.sin(half)
    return [float(axis[0] * sh), float(axis[1] * sh), float(axis[2] * sh), float(math.cos(half))]


def _matrix_to_quat(m):
    import numpy as np
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    return [float(x), float(y), float(z), float(w)]


def _finalize(root: gl.GLTF2, buffer: bytearray, out_path: Path) -> None:
    # Pad to 4 bytes
    while len(buffer) % 4 != 0:
        buffer.append(0)
    root.buffers.append(gl.Buffer(byteLength=len(buffer)))
    root.set_binary_blob(bytes(buffer))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    root.save_binary(str(out_path))
