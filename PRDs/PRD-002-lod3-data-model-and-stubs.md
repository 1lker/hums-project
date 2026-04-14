# PRD-002 — LOD3 Data Model + Interior Stub Footprints

**Status:** Draft (revised — full-fidelity track)
**Iteration:** 2 of N
**Depends on:** PRD-001 (parcels.json, footprints.geojson, block.geojson)
**Produces artifacts consumed by:** PRD-003 (Blender IFC generator)

---

## 1. Goal

Close two gaps before any geometry is extruded:

1. **Data-model gap.** PRD-001 produced *attribute* records and *flat* polygons. PRD-003 needs a richer intermediate: a **Building** object that knows its storeys, wall segments, openings, roof descriptor, and local coordinate frame — ready to hand to a 3D engine.
2. **Footprint gap.** 6 **interior church-precinct parcels** (`INT-N1…S2`) have no traced KML and are hardest to reconstruct from the 1923 map. Generate provisional stub footprints so downstream code isn't blocked, and flag them so real traces can replace them later.

The 5 East/West-facing parcels (`E-2…E-8`, `W-32`, `W-39*`) are **NOT stubbed** — user will trace those.

After PRD-002 we must be able to answer from one lookup:
> "Give me Building N-44 as a geometry-ready object: local-frame footprint, wall segment list with thicknesses and openings, roof descriptor, material assignment, source provenance."

## 2. Scope

### In scope
- Define LOD3-aligned intermediate schema (`Building`, `Storey`, `WallSegment`, `Opening`, `RoofDescriptor`, `LocalFrame`).
- Builder that assembles one `Building` per Excel parcel from `parcels.json` + matched footprint.
- **Heritage assumption profile** — default storey heights, wall thicknesses, roof pitches for 1923 Pervititch-era Kadıköy, applied only where data is missing.
- Stub generator for the 6 `INT-*` parcels using block outline + church precinct geometry.
- Semantic surface tagging following CityGML LOD3 conventions: `GroundSurface`, `WallSurface`, `RoofSurface`, `Window`, `Door`. Stored as roles in JSON — geometry added in PRD-003.
- Persist to `data/parsed/buildings.json`.
- Validation report: coverage of required fields, provenance tags per building.

### Out of scope (PRD-003+)
- Actual 3D geometry extrusion / mesh generation.
- IFC export.
- Texture / material appearance.
- East/West-side tracing (user will provide KMLs).
- Church body geometry (kept as raw footprint for now — church LOD3 is PRD-004).

## 3. Inputs

| Artifact | From |
|---|---|
| `parcels.json` | PRD-001 |
| `footprints.geojson` | PRD-001 |
| `block.geojson` | PRD-001 |
| `non_parcel_footprints.geojson` | PRD-001 (for church outline, used as negative space) |

## 4. Heritage Assumption Profile (period defaults)

Applied only when Excel leaves a field blank. Every applied default tagged with `source: "assumption:pervititch_1923"`.

| Field | Default | Rationale |
|---|---|---|
| Ground floor height (Mg/shop) | 3.8 m | Istanbul commercial ground floor, period standard |
| Upper residential storey | 3.2 m | Typical interwar apartment |
| Mezzanine (½) | 2.2 m | Half-storey shop loft |
| Basement (b) | 2.4 m | Partial sub-grade |
| Wall thickness — masonry (A/B) | 0.55 m | 2-wythe brick + render |
| Wall thickness — wooden (C) | 0.20 m | Timber frame with lath infill |
| Parapet height (flat/masonry) | 0.60 m | — |
| Roof pitch — Turkish tile (TR) | 30° | — |
| Roof pitch — sheet metal (T) | 20° | — |
| Roof pitch — French/Turkish vault visible (VF/VT) | Flat-top with 5% slope | Vault is internal ceiling, not roof form |
| Door width × height | 1.0 × 2.2 m | Shop/residential entrance |
| Shop window width × height | 1.8 × 2.4 m (GF) | Storefront (when `Mg.` GF use) |
| Upper-floor window | 1.0 × 1.6 m | Residential |
| Window sill height | 0.9 m (upper), 0.4 m (shop) | — |
| Floor/slab thickness | 0.25 m | — |

All of the above centralized in `hums/common/heritage_profile.py` as a frozen dataclass — overridable by Excel columns (future) without code change.

## 5. Intermediate data model

```python
Building
├── parcel_id: str
├── material_class: "A" | "B" | "C"     # masonry hard / masonry soft / wooden
├── local_frame: LocalFrame             # origin (UTM 35N), north_rotation
├── footprint_local: Polygon            # in local metric coords, oriented CCW
├── footprint_source: "traced" | "inferred" | "stub"
├── storeys: list[Storey]
│     ├── level: 0..N (0 = ground)
│     ├── height_m: float
│     ├── is_mezzanine: bool
│     ├── is_basement: bool
│     └── use: str                      # "shop" | "residential" | "bakery" | ...
├── wall_segments: list[WallSegment]
│     ├── start, end: (x, y) local
│     ├── thickness_m: float
│     ├── face: "N" | "E" | "S" | "W" | "INT"
│     ├── is_street_facing: bool
│     ├── hatch_pattern: str | None
│     └── openings: list[Opening]
│           ├── kind: "door" | "shop_window" | "window"
│           ├── storey_level: int
│           ├── position_along_wall_m: float   # 0 = start
│           ├── width_m, height_m, sill_m: float
│           └── source: "excel" | "assumption:pervititch_1923"
├── roof: RoofDescriptor
│     ├── shape: "gable" | "hip" | "mansard" | "flat" | "complex_pitched" | "vault_flat"
│     ├── material: "tile_TR" | "sheet_metal_T" | "vault_VF" | "vault_VT"
│     ├── pitch_deg: float
│     ├── slope_direction: str          # "N", "NE", multi, ...
│     ├── has_chimney: bool
│     ├── has_skylight: bool
│     └── ridge_axis_hint: "along_street" | "perpendicular" | None
├── provenance
│     ├── attribute_sources: dict[field_name → "excel" | "assumption"]
│     └── footprint_source_file: str | None
└── semantic_surfaces: []               # populated in PRD-003
```

## 6. Local-frame convention

For every building:
- **Origin**: footprint centroid in UTM 35N (easting, northing).
- **North-up** local axes (no per-building rotation yet — street alignment optional refinement later).
- Coordinates inside `footprint_local` are `point_utm - origin` → single-digit metres.
- Height axis: +Z = up, grade level = 0.

This makes Blender import trivial: buildings sit at their local origin, then a scene assembler offsets by `origin_utm - block_centroid_utm` to reassemble the block.

## 7. Interior stub generation

For the 6 `INT-*` parcels:

1. Take the block outline (EPSG:32635).
2. Subtract every *traced* parcel footprint and the *church footprint* (`churche-and-its-kubbe` — the big 320 m² polygon).
3. The remaining interior polygon(s) form the "church precinct courtyard."
4. From Excel, INT-* parcels have rough **zone** labels (`Interior N`, `Interior NE`, `Interior E`, `Interior S`, `Interior SE`). Use the church centroid + zone label to **sector the courtyard into 6 wedges** matching the described spatial story (N1/N2/N3 against north face; E2 against east face; S1/S2 south of clocher).
5. Each stub polygon gets:
   - `footprint_source = "stub"`
   - `match_confidence = "inferred-sector"`
   - Area clamped to plausible range (10–80 m²).
6. Stubs output to **separate file** `stubs.geojson` so they don't contaminate `footprints.geojson`. The building assembler reads both.

When user traces real INT-* polygons later, they're dropped into the project root with `building-entrence-INT-*.shp`; PRD-001 picks them up, coverage report shows them matched, and the stub for that parcel is skipped automatically.

## 8. Outputs

In `data/parsed/`:

- `buildings.json` — list of Building objects (32 entries: 21 traced + 6 stubbed + 5 still-missing placeholders).
- `stubs.geojson` — just the 6 stub polygons, EPSG:32635.
- `assumptions_manifest.md` — every assumption applied, per building, for audit.
- Updated `coverage_report.md` (new "stub" row).

## 9. Package additions

```
hums/
├── common/
│   └── heritage_profile.py            # NEW — frozen assumption table
├── modeling/                          # NEW subpackage
│   ├── __init__.py
│   ├── building.py                    # Building + component dataclasses
│   ├── local_frame.py                 # LocalFrame utilities
│   ├── wall_segmenter.py              # Polygon edges → WallSegment list
│   ├── opening_placer.py              # Strategy: DoorPlacer | WindowPlacer
│   ├── roof_descriptor.py             # Excel roof row → RoofDescriptor
│   ├── assumption_tracker.py          # Records provenance per field
│   └── building_builder.py            # Builder pattern: Parcel + Footprint → Building
├── stubs/                             # NEW subpackage
│   ├── __init__.py
│   ├── interior_sectoriser.py         # block minus traced minus church → sector wedges
│   └── stub_generator.py              # produces stubs.geojson
└── pipelines/
    └── prd002_buildings.py            # NEW orchestrator
```

Design patterns: **Builder** (`BuildingBuilder`), **Strategy** (`OpeningPlacer` variants per GF use), **Decorator / Chain** (`AssumptionTracker` wraps every default lookup), **Composite** (`Building` contains `Storey` which contains `WallSegment`).

## 10. Success criteria

- [ ] `buildings.json` contains 32 Building entries.
- [ ] 21 with `footprint_source = "traced"`, 6 with `"stub"`, 5 with `"missing"` (no polygon, metadata only).
- [ ] Every Building has ≥ 1 Storey, ≥ 3 WallSegments, ≥ 1 door Opening.
- [ ] Every assumption-sourced field appears in `assumptions_manifest.md`.
- [ ] Stub polygons don't self-intersect and don't overlap traced parcels (validated via shapely).
- [ ] `Prd002Pipeline` runs idempotently; re-running produces identical JSON.
- [ ] Every class file carries its `@prd("002", …)` decorator.

## 11. Resolved decisions (user-confirmed 2026-04-14)

1. **Street-rotated local frames.** Every `LocalFrame` stores a `street_rotation_deg` derived from the longest street-facing edge. Facades emerge orthogonal to local X/Y — clean for IFC and for later photo-to-facade mapping.
2. **Shared-footprint parcels.** Split along long axis; `shared_footprint_group_id` preserved.
3. **Church body** remains LOD3 in PRD-004; used here only as obstacle geometry for stub sectoring.

## 11b. Full-fidelity extensions (added this revision)

Project target is LOD3 with full facade fidelity. Most Block 147 buildings still stand, so modern photographs + Google Street View imagery will supplement the 1923 Pervititch data.

Added to the Building data model:

```python
Building
├── ...
├── facade_palette: FacadePalette
│     ├── wall_main: RGB                    # main plaster/render color
│     ├── wall_accent: RGB | None           # string courses, quoins
│     ├── trim: RGB                         # window/door frame
│     ├── shutters: RGB | None
│     ├── roof: RGB
│     └── source: "photo:{image_id}" | "period_default" | "user_override"
├── reference_imagery: list[ReferenceImage]
│     ├── image_id: str
│     ├── path: str                         # data/imagery/<parcel_id>/<file>
│     ├── source_url: str | None
│     ├── captured_date: str | None
│     ├── facade: "N" | "E" | "S" | "W" | "aerial" | "interior"
│     ├── aligned: bool                     # photo-to-facade homography computed
│     └── notes: str | None
└── openings (extended)
      Opening
      ├── ...
      ├── style: "rectangular" | "arched" | "ogee" | "bay" | "oriel"
      ├── pane_layout: "2x2" | "2x3" | "3x3" | "single" | None
      ├── has_shutters: bool
      ├── has_balcony: bool
      ├── frame_profile: "flat" | "moulded" | "cornice" | None
      ├── color_source: "photo:{image_id}" | "assumption"
```

Added module:
- `hums/modeling/facade_palette.py` — period defaults + photo-sampled overrides.
- `hums/imagery/` — new subpackage:
  - `reference_manifest.py` — reads `data/imagery/<parcel_id>/manifest.json`.
  - `image_ingest.py` — CLI helper: drop a photo into a parcel folder, generate a stub manifest entry, flag `aligned=false`.

Period default palette (applied until a photo overrides):

| Material class | Wall main | Trim | Roof |
|---|---|---|---|
| Masonry A (stone/high quality) | warm stone #C9B79C | #6E5A3E | tile red-brown #8E4A32 |
| Masonry B (plastered brick) | cream/pink #E0C9AE | #5A4A3A | tile red-brown #8E4A32 |
| Masonry B (shop GF) | same + GF color #B5533C (common Kadıköy shop red) | painted #2E2E2E | — |
| Wooden C | light ochre #D2B877 | dark brown #3D2A1A | sheet metal grey #4E5256 or tile |
| Church (stone) | light limestone #D8CCB3 | — | lead grey #5B6068 |

All palette entries flagged `source: "period_default"` until replaced.

**Workflow for photos (out of band, but PRD-002 defines the slots):**
1. User drops photos into `data/imagery/<parcel_id>/`.
2. `python -m hums imagery-ingest <parcel_id>` scaffolds manifest entries.
3. User fills in `facade` and `source_url`.
4. In a later PRD we add homography-based photo-to-facade alignment + color sampling.

### Scope clarifications

- Still **out of scope for PRD-002**: photo-to-facade homography, color sampling from images, automated pane-layout detection. Those are PRD-005.
- **In scope for PRD-002**: the schema slots, period-default palette, manifest ingest CLI, and the facade_palette field populated on every building.

## 12. Risks

- **Sectoring heuristic noise.** The 6 stubs will look geometrically plausible but be positionally approximate. Mitigation: explicit `footprint_source: "stub"` propagates all the way to IFC so renders can tint them differently.
- **Assumption drift.** As real survey data lands, assumptions may silently diverge from reality. Mitigation: `assumptions_manifest.md` rebuilt every run.

## 13. Sign-off

After execution, user reviews `buildings.json` spot-checks (e.g. N-40 bakery: multi-pitch roof, chimney, 2½ storeys, shop GF, wooden frontage + masonry body) and `assumptions_manifest.md` before we move to PRD-003.
