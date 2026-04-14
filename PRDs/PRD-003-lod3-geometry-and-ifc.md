# PRD-003 — LOD3 Geometry Generator (Blender + IFC 4.3)

**Status:** Draft
**Iteration:** 3 of N
**Depends on:** PRD-002 (`buildings.json`, heritage profile, palette)
**Produces artifacts consumed by:** PRD-004 (church/çeşme/magazines), PRD-005 (photo alignment), PRD-006 (4K renders + CesiumJS)

---

## 1. Goal

Turn every `Building` from `buildings.json` into **real 3D geometry** with CityGML-aligned LOD3 semantic surfaces, exported as:

- **IFC 4.3** (one per building + aggregated `block147.ifc`) — true BIM, opens in BlenderBIM / IfcConvert / Solibri.
- **Blender .blend** (authoring master, Cycles-ready).
- **glTF 2.0 / .glb** (per building + block, georeferenced) — handoff format for PRD-006 web viewer.

After PRD-003 we must be able to answer, from one asset:
> "Open the block. Every building is mass + roof + walls + doors + windows + palette colours, each surface semantically tagged (`WallSurface`, `RoofSurface`, `Window`, `Door`, `GroundSurface`), positioned at real UTM 35N coordinates."

## 2. Scope

### In scope
- Pure-Python **mesh-graph intermediate** (`BuildingMesh`) independent of Blender — unit-testable in plain venv.
- Extrusion of storeys from `footprint_local` using `Storey.height_m` stack from PRD-002.
- Wall thickness realized as two offset surfaces (outer + inner) per `WallSegment`.
- **Opening cutouts** in walls for each `Opening` — doors, shop windows, upper windows — with moulded frames when `frame_profile == "moulded"`.
- **Roof generators** (Strategy pattern) per `RoofDescriptor.shape`:
  - `gable`, `hip`, `flat`, `mansard`, `complex_pitched`, `vault_flat`
- **Semantic surface tagging** on every emitted face (CityGML LOD3 roles stored as custom properties + IFC PredefinedType).
- Backends (Adapter pattern): `BlenderBackend`, `IfcBackend`, `GltfBackend`.
- Scene assembler: offsets each building by `origin_utm - block_centroid_utm` → one aggregated `.blend` + `block147.ifc` + `block147.glb`.
- Chimneys (when `roof.has_chimney`), skylights (`roof.has_skylight`) as mass primitives on roof.
- Facade materials driven by `facade_palette` (Cycles principled BSDF per surface role).
- Street-rotation applied: each building's local frame rotated by `street_rotation_deg` when placed into the scene.
- Stub buildings (`footprint_source == "stub"`) rendered in a **low-opacity / wireframe-tinted** material so they read as provisional.
- Missing buildings (`footprint_source == "missing"`) rendered as a **parcel-number plate at the block centroid gap** so the block reads as incomplete rather than silently missing.

### Out of scope (later PRDs)
- Interior room subdivision, staircases.
- Vault internal ceiling geometry beyond simple curved soffit.
- Church body LOD3 — **PRD-004**.
- Photo-sampled materials / window pane reflections — **PRD-005**.
- 4K Cycles renders + web simulation — **PRD-006**.

## 3. Inputs

| Artifact | Source |
|---|---|
| `data/parsed/buildings.json` | PRD-002 |
| `data/parsed/block.geojson` | PRD-001 |
| `data/parsed/non_parcel_footprints.geojson` | PRD-001 (ground-surface cutout for church) |

## 4. Outputs

In `output/`:

```
output/
├── ifc/
│   ├── N-40.ifc, N-42.ifc, ...    (one per building)
│   └── block147.ifc                (aggregate)
├── blend/
│   └── block147.blend              (authoring master)
├── gltf/
│   ├── N-40.glb, N-42.glb, ...
│   └── block147.glb                (georeferenced, ready for Cesium)
└── reports/
    ├── geometry_manifest.md        (per building: face counts, semantic breakdown, volume)
    └── lod3_coverage.md            (semantic role coverage: which buildings have all 5 roles)
```

## 5. Mesh-graph intermediate schema

Pure Python, no Blender imports. Lives in `hums/render/mesh_graph.py`.

```python
@dataclass
class Vertex: x: float; y: float; z: float
@dataclass
class Face:
    vertices: list[int]                  # indices into BuildingMesh.vertices
    semantic_role: Literal[               # CityGML LOD3 thematic surface
        "GroundSurface", "WallSurface", "RoofSurface",
        "Window", "Door", "ClosureSurface", "OuterCeilingSurface",
        "InteriorWallSurface", "FloorSurface",
    ]
    surface_id: str                      # stable id: "N-44.wall.E.2" / "N-44.roof.main"
    material_key: str                    # "wall_main" | "trim" | "roof" | "shop_window" | "door"
    storey_level: int | None = None

@dataclass
class BuildingMesh:
    parcel_id: str
    vertices: list[Vertex]
    faces: list[Face]
    placement_origin_utm: tuple[float, float]
    placement_rotation_deg: float        # street_rotation_deg
    palette: FacadePalette               # inherited from PRD-002
    metadata: dict                       # storey count, footprint area, etc.
```

## 6. Geometry algorithms

### 6.1 Wall extrusion (with thickness)
For each `WallSegment`:
- Outer face = segment from z=0 to top of highest non-basement storey.
- Inner face = outer offset inward by `thickness_m`.
- Caps at each storey line emit a `FloorSurface` (interior).
- Openings subtract rectangles from outer+inner at `(position_along_wall_m, sill_m, width_m, height_m)`.
- Opening produces a `Door` or `Window` surface (the glazing plane, inset by 0.05 m) + sill/header/jamb `WallSurface` facets, plus a `ClosureSurface` strip at the reveal.
- If `frame_profile == "moulded"`, an extruded frame ring (rectangular cross-section 6 cm × 3 cm) is placed around the opening, tagged `Window` with `material_key == "trim"`.

### 6.2 Roof generation (Strategy)
Each shape has its own generator:

| shape | algorithm |
|---|---|
| `flat` | cap at eaves height + parapet (`parapet_m`); top tagged `RoofSurface` |
| `gable` | ridge along longest street edge unless `ridge_axis_hint == "perpendicular"`; two pitched planes at `pitch_deg`; gable-end walls extended to apex as `WallSurface` |
| `hip` | pyramidal apex via straight-skeleton approximation on footprint |
| `mansard` | lower steep 70° + upper 15° deck; two `RoofSurface` bands |
| `complex_pitched` | partition footprint into convex sub-polygons via shapely; each sub gets a hip roof; unions on shared ridges |
| `vault_flat` | nearly-flat top with `pitch_deg` (~2.86°), single `RoofSurface`; if vault code `VT` (Turkish brick arch), interior ceiling gets a shallow cylindrical segment tagged `OuterCeilingSurface` (visible from below in section cuts but invisible from outside — acceptable compromise for LOD3) |

Chimneys: 0.4 × 0.4 × 1.8 m mass on the roof ridge midpoint when `has_chimney == True`, `material_key == "chimney_brick"` (added to palette).
Skylights: 0.8 × 1.2 m glazed dormer-less insert when `has_skylight == True`.

### 6.3 Shared-footprint buildings
Already split into strips by PRD-002 — no special handling; each strip extrudes independently.

### 6.4 Placement
Final world placement (Blender, IFC, glTF):

```
M = T(origin_utm - block_centroid_utm) · R_z(street_rotation_deg)
```

Stored as IFC `IfcLocalPlacement` and Blender object transform. glTF bakes it into the root node's matrix. UTM 35N translation component rounded to mm.

## 7. CityGML ↔ IFC 4.3 semantic mapping

| CityGML LOD3 role | IFC 4.3 target | PredefinedType |
|---|---|---|
| GroundSurface | IfcSlab | BASESLAB |
| WallSurface | IfcWall | SOLIDWALL |
| RoofSurface | IfcRoof / IfcSlab | ROOF |
| Window | IfcWindow | WINDOW |
| Door | IfcDoor | DOOR |
| OuterCeilingSurface | IfcCovering | CEILING |
| FloorSurface | IfcSlab | FLOOR |
| ClosureSurface | IfcVirtualElement | — |

Each IFC entity carries `Tag` = `surface_id` and Pset `Pervititch_Attrs` with `material_class`, `footprint_source`, `storey_level`, plus photo reference ids when present.

## 8. Package additions

```
hums/render/
├── __init__.py
├── mesh_graph.py                  # Vertex/Face/BuildingMesh dataclasses
├── geometry/
│   ├── __init__.py
│   ├── footprint_ops.py           # offset, inset, cap (shapely + numpy)
│   ├── wall_extruder.py           # Wall + Storey → faces
│   ├── opening_cutter.py          # subtract opening quads, emit reveals
│   ├── opening_frame.py           # moulded trim ring
│   └── roof/                      # Strategy subpackage
│       ├── __init__.py
│       ├── base.py                # RoofGenerator ABC
│       ├── flat.py
│       ├── gable.py
│       ├── hip.py
│       ├── mansard.py
│       ├── complex_pitched.py
│       └── vault_flat.py
├── materials.py                   # FacadePalette → named Material assets
├── building_geometry_builder.py   # Building → BuildingMesh (pure Python)
├── scene_assembler.py             # list[BuildingMesh] → SceneGraph with world placements
├── backends/
│   ├── __init__.py
│   ├── blender_backend.py         # SceneGraph → .blend (Blender ≥ 4.2)
│   ├── ifc_backend.py             # SceneGraph → .ifc (ifcopenshell)
│   └── gltf_backend.py            # SceneGraph → .glb (pygltflib)
└── reports/
    ├── geometry_manifest.py
    └── lod3_coverage.py

hums/pipelines/
└── prd003_geometry.py             # orchestrator: buildings.json → output/*
```

Design patterns: **Strategy** (roofs), **Adapter** (backends), **Builder** (geometry builder), **Composite** (scene graph), **Pipeline** (orchestrator), **Template Method** (`RoofGenerator.generate()` with hook methods `ridge_axis()`, `pitched_planes()`).

## 9. Dependencies (additions)

Add to `requirements.txt` (venv, pure-Python):
- `numpy` (already present via shapely)
- `pygltflib` — glTF writer
- `ifcopenshell` — IFC 4.3 writer *(installed from wheel, see Dockerfile stage 2)*
- `scikit-geometry` *(optional — straight skeleton for hip roofs; if unavailable, fall back to medial-axis approximation)*

Blender is **not** a pip dependency. The `blender_backend` runs via:
```
blender --background --python src/hums/render/backends/blender_entry.py -- --input buildings.json --out output/blend/block147.blend
```
Docker stage 2 (already stubbed in Dockerfile) adds Blender + ifcopenshell so the full pipeline runs in a container.

## 10. Pipeline wiring

New command: `make prd003` → runs `hums.pipelines.prd003_geometry`:

1. Load `buildings.json`.
2. For each building: `BuildingGeometryBuilder.build(b)` → `BuildingMesh`.
3. `SceneAssembler.assemble(meshes, block_centroid_utm)` → `SceneGraph`.
4. Emit per backend:
   - IfcBackend (always)
   - GltfBackend (always)
   - BlenderBackend (only if `blender` on PATH — else warn and skip with clear message)
5. Write reports (`geometry_manifest.md`, `lod3_coverage.md`).

Idempotent: re-running with unchanged `buildings.json` produces byte-identical IFC / glTF (sort all outputs deterministically).

## 11. Success criteria

- [ ] `output/ifc/block147.ifc` validates with `ifcopenshell` `ifcvalidate`.
- [ ] Every traced building exports all 5 CityGML LOD3 roles: GroundSurface, WallSurface (≥ 4), RoofSurface, Window (≥ 1), Door (≥ 1).
- [ ] Stub buildings export with the same schema but carry Pset `Pervititch_Attrs.footprint_source = "stub"`.
- [ ] Missing buildings export as a 0.3-m flat plate at centroid with Pset `footprint_source = "missing"` and a text annotation.
- [ ] `output/gltf/block147.glb` opens in https://gltf-viewer.donmccurdy.com without warnings.
- [ ] `geometry_manifest.md` lists face count + volume + surface role counts for each building.
- [ ] `lod3_coverage.md` lists every building whose role coverage is incomplete (for the user to prioritize tracing).
- [ ] Pipeline is idempotent.
- [ ] Every new module carries `@prd("003", …)` tags.

## 12. Open questions

1. **Blender required for IFC export?** No — `ifcopenshell` writes IFC directly from the mesh graph. Blender is only needed for authoring `.blend` + eventual Cycles renders. Proposal: make Blender **optional** in PRD-003; required only in PRD-006.
2. **Hip roof algorithm.** Straight-skeleton (via `scikit-geometry`) is the clean solution but adds a C++ dep. Proposal: attempt straight-skeleton; fall back to "inset footprint by pitch-derived distance and raise" approximation if unavailable. Acceptable for LOD3 at 1923-block scale.
3. **Interior vault geometry.** For `VT` (Turkish brick arch) and `VF` (French concrete vault), do we model the underside? Proposal: **no for now** — exterior reads as flat-ish with slight pitch; add interior in PRD-005 if/when interior imagery arrives.
4. **Texture coordinates.** Do we emit UVs in PRD-003, or leave materials flat-shaded and add UV unwrap in PRD-005 when photo textures are sampled? Proposal: **leave flat-shaded** — save UV work for when photos exist.
5. **Street-facing gable orientation.** For buildings with `street_rotation_deg`, default gable ridge runs parallel to street unless Excel `ridge_axis_hint` overrides. Proposal: confirm with N-40 (corner bakery, complex multi-pitch) as first test case.

## 13. Risks

- **Complex pitched roofs** on irregular footprints (N-40 corner bakery, shared-footprint strips) are the hardest geometry. Mitigation: partition via shapely.ops.triangulate or convex decomposition before applying per-sub-region hip roofs.
- **IFC 4.3 validator quirks.** Some viewers are strict about `IfcLocalPlacement` hierarchies. Mitigation: author a single `IfcSite` (the block) → `IfcBuilding` per parcel → `IfcBuildingStorey` per storey → elements. Standard heritage-BIM layout.
- **Docker image size.** Blender pushes image past 2 GB. Mitigation: Docker stage 2 is opt-in (`--target bim`); base stage stays slim.

## 14. Test plan

Two sample buildings as golden tests:
- **N-44** (masonry corner shop, 3 street-facing walls, shop+upper, gable roof) — every geometry class exercised.
- **N-40** (bakery, wooden frontage + masonry body, complex_pitched, chimney) — edge cases.

Golden: vertex count, face count per semantic role, total volume. Tolerance ±2 faces, ±1% volume.

## 15. Sign-off

User opens `block147.glb` in a web viewer, spot-checks that N-44's shop windows are on the street frontage, N-40's chimney is present, stubs look translucent, missing plates are labelled. Then we move to PRD-004 (church) or PRD-005 (imagery) depending on priority.
