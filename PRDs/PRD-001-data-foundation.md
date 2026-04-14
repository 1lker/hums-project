# PRD-001 — Data Foundation (Excel + Footprints Parsing)

**Status:** In progress
**Iteration:** 1 of N
**Depends on:** —
**Produces artifacts consumed by:** PRD-002 (LOD3 geometry generator)

---

## 1. Goal

Convert every source artifact (Excel BIM register, KML/SHP footprints, georeferenced raster) into a single clean, machine-readable dataset that downstream 3D generation code can consume without touching the original files again.

After this PRD we must be able to answer, from one JSON/GeoJSON lookup:
> "Give me parcel N-44's material, storeys, roof shape, door location, wall thickness, and metric footprint polygon."

## 2. Scope

### In scope
- Parse all 5 sheets of `Block147_Pervititch_BIM_v3_FINAL (1).xlsx`.
- Join sheets on parcel ID (`N-40`, `N-42`, …).
- Parse all KML and Shapefile footprints in the project root.
- Reproject footprints from WGS84 to **UTM Zone 35N (EPSG:32635)** for metric operations.
- Produce a coverage report: which Excel parcels have footprints, which are missing.
- Normalize naming: every output row keyed by `parcel_id` matching Excel.

### Out of scope (later PRDs)
- 3D geometry generation.
- Roof modeling.
- Texture / material assignment.
- Stub footprint generation for missing parcels (deferred to PRD-002).
- Raster (TIFF) reprojection — only noted, not processed here.

## 3. Inputs

| Artifact | Location | Notes |
|---|---|---|
| Excel register v3 | `Block147_Pervititch_BIM_v3_FINAL (1).xlsx` | 5 sheets, 45 parcels |
| KML footprints | `*.kml` (project root) | ~20 files, WGS84 |
| Shapefiles | `*.shp` + .dbf/.prj/.shx | WGS84 per .prj |
| Block outline | `blobk-147-layer.shp` | Block boundary |
| Georef raster | `500_1938_APLPEKADI08.tif` | Reference only for now |

## 4. Outputs

All written to `data/parsed/`:

### `parcels.json`
Array of objects, one per Excel row. Shape:
```json
{
  "parcel_id": "N-44",
  "parcel_number": "(44)",
  "zone": "North",
  "street_facing": "T…L Sokak (N)",
  "material": { "class": "B", "decoded": "Masonry", "map_colour": "PINK" },
  "wall": { "code": "Mg.+VT+2MO", "decoded": "...", "thickness_m": null },
  "vault": { "code": "VT", "decoded": "Voûte Turque" },
  "ground_floor": { "use": "Mg (Shop)", "code": "Mg." },
  "storeys": { "raw": "Δ3", "count": 3, "has_mezzanine": false, "basement": false },
  "condition": "—",
  "roof": { "shape": "...", "material_code": "...", "slope_direction": "...", "has_chimney": true, "has_skylight": false },
  "openings": { "primary_door_face": "North", "door_type": "...", "x_marks": [...], "shared_entrance_with": null },
  "walls": { "gf_line_type": "Solid", "hatch_pattern": "...", "notes": "..." },
  "bim_notes": "...",
  "sources": { "register_row": 4, "roof_row": 4, "doors_row": 4, "walls_row": 4 }
}
```

### `footprints.geojson`
FeatureCollection, EPSG:32635, one Feature per traced polygon:
```json
{
  "type": "Feature",
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "properties": {
    "parcel_id": "N-44",          // matched to Excel where possible
    "source_file": "building-entrence-44.shp",
    "centroid_utm": [x, y],
    "area_m2": 123.4,
    "perimeter_m": 45.6,
    "match_confidence": "high" | "medium" | "inferred"
  }
}
```

### `block.geojson`
Single feature: Block 147 outline in EPSG:32635 (for later stub generation).

### `coverage_report.md`
Human-readable table:
- Parcels in Excel WITH footprints
- Parcels in Excel WITHOUT footprints  (→ need tracing or stubs)
- Footprints WITHOUT Excel match (→ mis-named or extra geometry)
- ID normalization decisions made (e.g., `building-entrence-04` → parcel `04`)

## 5. Parcel ID normalization rules

Excel IDs look like `N-40`, `N-42/(98)`, `S-10`. Filenames look like `building-entrence-44`, `buildingentrence41-43-45-16`. Rules:
1. Strip the `building-entrence-`/`buildingentrence` prefix → raw number(s).
2. Match raw number against the `Parcel` column of Excel (not the ID column).
3. Multi-number filenames (e.g. `41-43-45-16`) → one footprint linked to multiple parcel IDs (record as list, `match_confidence: "shared-footprint"`).
4. Non-parcel footprints (church, çeşme, magazine) → `parcel_id: null`, keep in separate `non_parcel_footprints.geojson`.

## 6. Implementation plan

| Step | File | Action |
|---|---|---|
| 1 | `src/parse_excel.py` | openpyxl read 5 sheets, join by Parcel, write `parcels.json` |
| 2 | `src/parse_footprints.py` | Read KML via lxml + SHP via pyshp, reproject with pyproj, write GeoJSON |
| 3 | `src/build_coverage.py` | Cross-match parcels ↔ footprints, write `coverage_report.md` |
| 4 | `src/__main__.py` | Orchestrator: runs 1→2→3 |

Dependencies to install: `openpyxl`, `pyshp`, `lxml`, `pyproj`, `shapely`.

## 7. Success criteria

- [ ] `parcels.json` contains 45 entries (one per Excel row).
- [ ] Every parcel object has non-null `material.class` (A/B/C or explicit null).
- [ ] `footprints.geojson` validates (each polygon is closed, has area > 0).
- [ ] Every footprint either maps to ≥1 Excel parcel_id OR is flagged as non-parcel.
- [ ] Coverage report clearly lists missing footprints for PRD-002 to address.
- [ ] Re-running the parser is idempotent (same input → same output bytewise).

## 8. Open questions (answered inline when resolved)

- Do `N-40/(98)` style compound IDs represent one building on two parcels, or a main + annexe? → **Assume one building with secondary parcel reference, store both.**
- French vs Turkish vault (VF/VT) affects ceiling geometry — model in PRD-002, just record here. ✅
- Wall thickness `Ep` column often blank — keep null, apply defaults in PRD-002.

## 9. Risks

- **ID mismatch.** Filenames are hand-typed; expect typos. Mitigation: coverage report surfaces every unmatched ID for manual confirmation before PRD-002.
- **Shapefile/KML drift.** Same parcel sometimes has both a SHP and a KML. Prefer SHP when both exist (shapefiles are the authored source, KMLs are exports).

## 10. Sign-off

After execution, user reviews `coverage_report.md` and confirms before we move to PRD-002.
