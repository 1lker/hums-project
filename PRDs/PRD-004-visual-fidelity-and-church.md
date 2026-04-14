# PRD-004 — Visual Fidelity + Church + Scene Context

**Status:** Draft
**Iteration:** 4 of N
**Depends on:** PRD-003 (mesh graph, roof Strategies, backends)
**Produces artifacts consumed by:** PRD-005 (photo alignment), PRD-006 (4K renders / web viewer)

---

## 1. Goal

Turn the current "abstract blocks with pasted windows" into **recognizable 1923-Kadıköy buildings**, add the **Ayia Eftimia church** as a proper LOD3 mass, and give the glTF viewer **a sensible default framing** (ground, camera, directional sun light).

A viewer opening `block147.glb` should see: a block that reads as a city block from street level, with punched windows, pitched overhanging roofs, the church as a distinct monumental volume with its dome and clocher, surrounded by a ground plane and lit by a low afternoon sun.

## 2. Scope — three tracks, one PRD

### Track A · Scene context (ground plane + camera + sun)
- Emit a **ground plane** 40 m beyond block extents, flat tinted cobble-grey.
- Emit a **KHR_lights_punctual directional light** at 45° elevation, warm 4500 K — gives instant shading.
- Emit a **glTF camera** at a photogenic 35 m distance, 15° above horizon, looking at the block centroid; declare it in the default scene.
- Extend `SceneAssembler` to carry `ground`, `camera`, `lights` alongside `buildings`.

### Track B · Visual fidelity of buildings
- **Real window cutouts.** Replace the inset glazing panels with proper wall-hole geometry using an axis-aligned subdivision strategy (no CSG library needed):
  - Sort openings along each wall left→right.
  - Emit wall as strips: below-sill (spandrel), between-openings (piers), above-header (transom strip), lintel band, split into quads at each opening boundary.
  - Opening hole → jambs (sides), sill (bottom, 0.08 m projection), head (top) + recessed glazing plane 0.15 m inside the wall.
  - Pane subdivision: vertical + horizontal mullions on window panes ≥ 1 m wide (trim material).
- **Roof overhang + eaves + soffit.** Buffer footprint outward by 0.4 m at eaves height; emit:
  - Extended roof plane (so tiles overhang).
  - Downward-facing soffit strip (underside of the overhang).
  - Horizontal **cornice band** 0.15 m tall just below the soffit on street-facing walls.
- **Plinth.** All masonry buildings (class A / B) get a 0.5 m raised stone plinth around the base; `plinth_stone` material key.
- **Stringcourses.** Horizontal decorative band at each storey floor on street-facing walls, 0.06 m proud, `trim` material.
- **Corner quoins** on class-A masonry buildings with exposed street corners (optional; cosmetic). Low priority, include only if straightforward.
- **Shutters** as flat side panels (flanking windows) when `Opening.has_shutters == True`.
- **Balcony** rectangular slab + railing when `Opening.has_balcony == True`.
- **Door detail**: panel door = recessed rectangle + raised frame + transom glazing pane above when door height < full storey.

### Track C · Church / clocher / kubbe
- New `ChurchBuilder` in `hums/render/special/church_builder.py`.
- Inputs: `churche-and-its-kubbe.shp` (main body polygon, already in `non_parcel_footprints.geojson`).
- Model as three composite volumes:
  1. **Main body** (nave) — extrude footprint to 7 m eaves + hip roof at 25°, stone material palette.
  2. **Central dome (kubbe)** — hemisphere ~6 m diameter centered on body centroid, crowned at 12 m; 16-segment UV sphere, `roof` material (lead grey).
  3. **Clocher (bell tower)** — small square footprint (≈3 × 3 m) ~12 m tall with louvred belfry on top three sides + pyramidal cap. Positioned via a separate small polygon if one exists, else offset from body centroid toward south.
- Church added to `SceneGraph.buildings` with `metadata.kind = "church"`, `structure_type = "church"` (new literal).
- Skip interior, altar, iconography — pure exterior LOD3.

### Bug fix · Degenerate hip roof
Current hip roof emits triangles that extend below ground when the inset collapses (tight footprints like N-48). Result: those "floating stilts" in the screenshots. Fix: clamp inset distance, ensure all emitted triangle apexes sit on the inset ring never outside the footprint bbox, and skip emission when inset distance < 0.1 m (fall back to flat roof with parapet).

## 3. Out of scope (later PRDs)
- Photo-sourced textures (PRD-005).
- Full-block PBR render with Cycles 4K (PRD-006).
- UV unwrap, image-based lighting (HDRI) (PRD-005/006).
- Terrain topography (block 147 is nearly level — a flat plane is fine).
- Interior geometry.

## 4. Package additions

```
hums/render/
├── geometry/
│   ├── wall_subdivider.py        # NEW: left-right pier/sill/transom strips
│   ├── opening_frame.py          # NEW: jambs + sill + head + mullions + shutters
│   ├── facade_banding.py         # NEW: cornice / stringcourse / plinth
│   ├── balcony.py                # NEW
│   └── roof/
│       └── overhang.py           # NEW: eaves + soffit strip
├── special/
│   ├── __init__.py
│   └── church_builder.py         # NEW: church body + dome + clocher
├── scene/
│   ├── ground_plane.py           # NEW
│   ├── camera.py                 # NEW
│   └── sun_light.py              # NEW: KHR_lights_punctual direction light
└── mesh_graph.py                 # add Camera, Light, GroundPlane types + SceneGraph fields
```

Design patterns: **Strategy** (WallSubdivider variants for street / interior walls), **Decorator** (facade bands wrapping a building), **Template Method** (ChurchBuilder composing three sub-volumes via hook methods), **Facade** (upgraded `BuildingGeometryBuilder` orchestrates all tracks).

## 5. Data-model additions

- `mesh_graph.SceneGraph` gains `ground: GroundPlane | None`, `camera: Camera | None`, `lights: list[DirectionalLight]`.
- New semantic roles: `PlinthSurface`, `CorniceSurface`, `StringcourseSurface`, `SoffitSurface`, `JambSurface`, `SillSurface`, `HeaderSurface`, `Mullion`, `Shutter`, `Balcony`, `ChurchBody`, `ChurchDome`, `Clocher`.
- New material keys: `plinth_stone`, `cornice_paint`, `tile_terracotta`, `sheet_metal_grey`, `dome_lead`, `balcony_iron`.

## 6. Palette tweaks (period-appropriate for 1923 Kadıköy)

| material_key | RGB | Note |
|---|---|---|
| `tile_terracotta` | 162, 78, 52 | warmer than current `roof`, replaces roof for class A/B pitched |
| `sheet_metal_grey` | 86, 92, 98 | keep for T roofs |
| `plinth_stone` | 160, 148, 130 | neutral warm stone |
| `cornice_paint` | 236, 225, 205 | off-white, brighter than wall_main |
| `dome_lead` | 98, 104, 110 | desaturated blue-grey |
| `balcony_iron` | 45, 40, 38 | dark wrought iron |
| `chimney_brick` | 146, 72, 55 | slightly brighter, matches tile |

Replace `roof` default with `tile_terracotta` for class A/B, keep `sheet_metal_grey` for explicit `T` codes.

## 7. glTF camera + light strategy

- One `KHR_lights_punctual` directional light, direction ≈ `(-0.3, -0.4, -0.85)` (sun from SE, 45° above).
- One perspective camera (yfov ~45°) placed at `(x=-30, y=-25, z=12)` in block-centred Z-up, looking at origin. The root node's -90°X rotation converts this to Y-up so viewers like gltf-viewer.donmccurdy.com pick it up correctly.
- Scene default: `nodes=[root]` — root children = `[block_root, ground_node, camera_node, light_node]`.

## 8. Success criteria

- [ ] block147.glb opens in gltf-viewer.donmccurdy.com with a framed oblique view (not dead-on black).
- [ ] Each traced building shows **through-holes** for windows (you can see behind a window when orbiting).
- [ ] Every pitched roof has a visible overhang (roof plane extends ~30–40 cm past walls).
- [ ] Church appears as a distinct block-central volume with dome + clocher.
- [ ] Ground plane visible under + around block.
- [ ] Sun direction creates visible shadows-of-lighting (bright/dark facades).
- [ ] Degenerate-hip-roof "stilts" gone (face count for small buildings like N-48 stays finite, no sub-zero verts).
- [ ] Face count per building grows (more detail) but stays under 500 to keep the scene workable.

## 9. Implementation slices (commit after each)

1. **Slice 1** — bug fix: degenerate hip roof floor-clamp + min-inset guard. Commit.
2. **Slice 2** — Track A: ground plane + camera + sun. Commit (visible improvement: viewer defaults).
3. **Slice 3** — Track B.1: real window/door cutouts with jambs/sill/head. Commit.
4. **Slice 4** — Track B.2: roof overhang + cornice + soffit. Commit.
5. **Slice 5** — Track B.3: plinth + stringcourses + shutters + balcony + door detail. Commit.
6. **Slice 6** — Track C: church/dome/clocher. Commit.

Each slice re-runs the pipeline; the glTF snapshot in `output/gltf/block147.glb` gets progressively more photorealistic.

## 10. Risks

- **Face count explosion.** Every detail adds quads. Mitigation: the face-count ceiling in §8 + decimation of short edges.
- **Wall subdivision overlaps.** Off-by-one between pier strips and opening frames will show as seams. Mitigation: strict left→right sort + epsilon-based joins.
- **Dome tesselation.** 16-segment UV sphere at ~200 faces. Keep resolution fixed; don't add LOD switching yet.
- **Non-axis-aligned street walls.** Openings are positioned along local rotated frame so subdivision works in local 2D regardless of street angle. No new risk.

## 11. Sign-off

User opens the glb in the viewer after slice 6. Spot-check: N-44 corner shop shows shop-front with mullions, upper windows with shutters, pitched red-tile roof with eaves. Church reads as the block centerpiece with its dome. Scene frames nicely without manual orbit.
