# KML + Pervititch Map Audit

Date: 2026-05-11

Source of truth used here:
- `map.png` visual reading
- every file in `data/raw/kml/`
- parsed parcel/building output in `data/parsed/`
- rendered opening/material audit in `output/reports/opening_audit.md`

Important rule: Pervititch maps usually show parcel footprint, material color, use/storey/roof shorthand, arrows/gates, and special marks. They do **not** show exact facade window counts. The current visible model therefore keeps doors/shopfronts/vitrines tied to map/manual evidence, while upper-floor windows are added only on geometry-detected exposed street/courtyard faces or on party walls exposed above a lower neighbor.

## Main Findings

1. **KML geometry is mostly clean.** Every KML contains one closed polygon. No malformed coordinate tokens found.
2. **`TF` was incorrectly rendered as sheet metal.** Fixed in code: `TF` is now `tile_TF` / terracotta-style roof, while plain `T` remains sheet metal.
3. **`N-40/N-42` was the biggest map mismatch and is now corrected in the full block scene.** The map reads `(40)(42)` as one long yellow wooden zoned mass. The black internal division lines are now treated as real area/height boundaries: 2-storey north frontage, 4-storey middle bay, and 3-storey south/vitrine bay.
4. **`buildingentrence41-43-45-16` is now treated as four joined units under one common roof/mass.** The 41, 43, 45, and 16 labels are modeled as entrances/sub-units on a connected building; the south facade now has vertical unit seams, but the roof remains shared.
5. **The north-east `52-54-02` corner is now treated as one single building.** The 52, 54, and 02 labels are interpreted as frontage/entrance references on the same masonry corner mass, not as separate visible buildings or a high/low split.
6. **W-32 magazine polygons are now low one-storey volumes.** The three KMLs are the only accepted small triangular/corner magazine geometry; each receives a west door only, low flat/unknown roof, and no invented upper windows.
7. **Numbered entrance parcels now receive at least one conservative door.** Rows whose source is `building-entrence*` and carry a visible parcel/entry number no longer stay blank just because the arrow was parsed as ambiguous.

## One-By-One KML Check

| KML | Map / KML Target | Current Rendering | Verdict |
|---|---|---|---|
| `at-the-green-area-wooden-at-147-block-near-the-church-middle-of-the-block.kml` | Small yellow interior/church-edge wooden annex, mapped to `E-4a`. | `E-4a`: class C, 1 storey, `tile_TF` after fix, 1 courtyard/internal door. | **Mostly OK.** Door is map/Excel driven; no facade window certainty. |
| `blobk147layer-main.kml` | Whole Block 147 outline. | Used only as block outline / scene frame. | **OK.** No doors/windows/heights/roof expected. |
| `building-entrence-40-42.kml` | The `(40)(42)` yellow strip visible on the north side; map reads one zoned wooden building. The black division lines are building-area boundaries. | Full block now renders manual `N-40-42` as three rectangular wooden height zones: 2 storeys north, 4 storeys middle, 3 storeys south/vitrine. | **Corrected in full block scene.** 40/42 north entrances are kept; vitrine remains map-evidence only. |
| `buildingentrence-14.kml` | East-side `(14)`, masonry shop, `TF` roof marker and clear entrance arrow. | `E-14`: class B, 1 storey, `tile_TF`, east door, no generic shopfront glass. Checked for two-height split; no confirmed internal height boundary. | **OK with caution.** Split only if a sharper source confirms two heights. |
| `buildingentrence04.kml` | East-side `(4)`, yellow wooden one-storey shop, `T` roof. | `E-4`: class C, 1 storey, sheet metal roof, east door. | **OK.** |
| `buildingentrence06.kml` | East-side `(6)`, masonry, `VF/TF` notation. | `E-6`: class B, 1 storey, `tile_TF`, east door. | **OK after TF fix.** |
| `buildingentrence08.kml` | East-side `(8)`, masonry, `VF/TF`; map note says dash is not an entrance arrow. | `E-8`: class B, 1 storey, `tile_TF`, one conservative east door from numbered entrance fallback. | **Corrected.** Numbered `building-entrence` area now gets a door even when the dash/arrow is ambiguous. |
| `buildingentrence10.kml` | East-side `(10)`, masonry, `VF/TF`, arrow/direction marker. | `E-10`: class B, 1 storey, `tile_TF`, east door; direction marker retained as roof-review note, not a height split. | **Rechecked.** |
| `buildingentrence12.kml` | East-side `(12)`, map reread favors `1p.Mg`/`VF` over the old parsed `2p`. | `E-12`: class B, 1 storey, shallow barrel/vault roof form with `tile_TF` material, one east door, no upper windows and no generic shopfront glass. | **Corrected.** |
| `buildingentrence41-43-45-16.kml` | Combined south/east-south row covering `S-41`, `S-43`, `S-45`, `E-16`. | Replaced by manual `S-41-43-45-E16.merged_mass`: one connected mass, one shared roof, four entrance hints, south facade division seams, detected upper windows on exposed faces, no shopfronts. | **Corrected.** Matches user reading: four joined building/entrance units under one roof. |
| `buildingentrence44.kml` | North `(44)`: `Mg`, `VT`, 3 storeys, `×` possible tabatiere/skylight. | `N-44`: class B, 3 storeys, roof unknown/gable, one north door, small framed roof tabatiere, and detected upper windows on exposed faces. | **Corrected conservative.** `×` is modeled as roof tabatiere/skylight, not as a facade door/window. |
| `buildingentrence46.kml` | North `(46)`: `Mg`, `VF`, 2 storeys, shared `×` with `(48)`. | `N-46`: class B, 2 storeys, roof unknown/gable, one conservative north door from numbered entrance fallback, detected upper windows on exposed faces. | **Corrected.** Door added for the numbered entrance; shared `×` is still not modeled as an extra gate/window. |
| `buildingentrence48.kml` | North `(48)`: `Mg`, `VF`, `TF`, 2 storeys; shared/nearby `×` evidence with `(46)`. | `N-48`: class B, 2 storeys, `tile_TF`, one conservative north door from numbered entrance fallback, small framed roof tabatiere, detected upper windows on exposed faces, no shopfront. | **Corrected after TF fix.** Door added for the numbered entrance; `×` is treated as roof evidence only. |
| `buildingentrence50.kml` | North `(50)`: masonry / multi-storey note, roof unreadable. | `N-50`: class B, 3 storeys, roof unknown/gable, detected upper windows on street/courtyard and height-break exposed faces. | **Caution.** Mixed frontage remains map-readable; exact facade count remains inferred from exposed geometry. |
| `buildingentrence54-54-02.kml` | Typo duplicate of `52-54-02`; same geometry as SHP. | Replaced in final scene by manual `N-52-54-E2.corner_mass`: one masonry corner building with 52/54 north entrances and 02 east entrance. | **Corrected as one building.** Duplicate/old triangular/high-low split is not rendered. |
| `cesme-fountain.kml` | `Çeşme` fountain near south-west/south street edge. | `W-39/2`: non-building fountain, no doors/windows. | **OK.** |
| `church-entrence-camli-area-(39-1*39-2)-with-clocher.kml` | Duplicate KML for church/clocher porch area. | Rendered from SHP twin as manual `W-39-1`: glass `camli_vitre_passage` + opaque `masonry_side_narthex`; duplicate KML itself is not rendered twice. | **Corrected.** No all-glass flat block; roof follows dashed/diagonal roof evidence. |
| `churche-and-its-kubbe.kml` | Ayia Eftimia church footprint / kubbe. | Special church mesh with continuous low kiremit roof, lead/zinc dome collar, high drum/kubbe, lantern, clocher, and arched nave body windows on long exposed faces. Kubbe/drum center is now pinned to UTM `(670342.95, 4539707.85)` from the georeferenced Pervititch raster, not the polygon centroid. | **Roof/clocher/windows corrected.** Clocher is placed from the W-39/1 church-edge clocher/camlı footprint; the formerly blank church body walls behind W-32 now have church-style arched panes. |
| `near-39-open-32-magazine.kml` | One small W-32 magazine polygon. | One of `W-32#1/#2/#3`; one-storey, low flat/unknown roof, west door only. | **Corrected conservative.** Door is map-arrow driven; old 2-storey/gable interpretation suppressed. |
| `near-39-open-32-the last-corner-triangular-magazine..kml` | Small triangular W-32 magazine polygon. | One of `W-32#1/#2/#3`; one-storey, low flat/unknown roof, west door only. | **Corrected conservative.** This is the accepted triangular/corner magazine, not an invented taller building. |
| `near-39-open-32-the middle-magazine.kml` | Small middle W-32 magazine polygon. | One of `W-32#1/#2/#3`; one-storey, low flat/unknown roof, west door only. | **Corrected conservative.** Door is map-arrow driven; old 2-storey/gable interpretation suppressed. |

## Corrections Already Applied During This Audit

- `TF` roof codes now become `tile_TF`, not `sheet_metal_T`.
- `T` still means sheet metal.
- Full `block147.glb` now substitutes manual `N-40-42` zones for the old split `N-40`/`N-42` meshes. The yellow strip is now rectangularized from the map footprint and divided into the three black-line height zones: 2 / 4 / 3 storeys.
- Full `block147.glb` now substitutes manual `S-41-43-45-E16` for the old split `S-41`/`S-43`/`S-45`/`E-16` meshes.
- Full `block147.glb` now substitutes manual `W-34-36-FIRIN` for the old split `W-34`/`W-36` meshes. The visible model keeps it one connected Firin complex with one coherent TR/tile roof, removing the previous small grey cut-roof patch.
- Full `block147.glb` now substitutes manual `N-52-54-E2` for the old split `N-52`/`N-54`/`E-2` meshes. The visible model is now one `corner_mass`, with the numbers handled as entrances/labels on the same building.
- Manual `N-40-42` doors are restricted to explicit map/manual hints; internal fallback doors were removed.
- Church roof checked against the map and reference descriptions: body roof is now continuous low kiremit/tile, with lead/zinc flashing under the central kubbe.
- Church kubbe/drum/lantern center is now georeferenced from the Pervititch raster mark at UTM `(670342.95, 4539707.85)`, shifted about `+2.15 m E / +1.47 m N` from the church footprint centroid.
- All visible roof generators received a presentation-quality pass: gable roofs now have real pitched planes/ridge caps, hip roofs resolve to ridges/hips instead of broad flat decks, VF/VT zones render as shallow barrel/vault roofs, and Camlı/Vitre roof areas render as glass.
- Building colors were muted toward realistic historic masonry/wood/shopfront tones while preserving the Pervititch material logic: masonry classes read as warm stone/plaster, wooden class C as ochre timber, `T` as aged sheet metal, `TF` as French/Marseille clay tile.
- Follow-up correction: bbox-style roofs were removed. Gable/hip roofs now stay clipped to their KML/SHP footprint; the ugly synthetic roof overhang/eaves strips were disabled.
- Verified the visible 3D scene has no independent `INT-*`, stub, or missing-source buildings. `INT-*` rows remain metadata only and are not rendered as separate blocks.
- Checked rendered footprint overlap in the northwest/FIRIN area and full scene: no visible ground-footprint overlaps above 0.25 m².
- W-32's three magazine polygons now render as one-storey tiny shops with low flat/unknown roofs and conservative west-entrance doors only. The doors are map-arrow driven; no upper windows are added.
- The church body now has arched nave windows on long exposed faces, including the west side behind W-32, while the drum and clocher keep their existing arched/glass openings.
- W-39/1 now uses a manual material/roof split: the Camlı/Vitre part is glass with a complex pitched glass roof, while the adjacent narthex mass is opaque masonry with a sheet-metal hip roof.
- Opening placement is now strict but no longer blank: same-height party walls get no windows; upper windows are added only on geometry-detected exposed street/courtyard faces or party walls exposed above a lower neighbor; doors/shopfronts/vitrines still require map/manual evidence.
- Close-but-not-touching KML/SHP edges are now treated as bitişik party walls when they are parallel, overlapping, and within 1.2 m. This suppresses windows in the tiny georeferencing gaps between adjacent same-height buildings instead of waiting for the KML lines to be perfectly snapped.
- Street-facing classification now requires an edge to run parallel/overlap with the block outline. A side wall that merely touches the street at one corner is no longer misread as a street facade.
- N-44 and N-48 now receive small framed roof tabatiere/skylight elements from the map `×` marks; no facade doors/windows were added from those marks.
- Numbered `building-entrence*` parcels that were blank because of ambiguous arrow parsing now get one conservative numbered-entrance door (`N-46`, `N-48`, `E-8`). The W-34-36 Firin manual model also now gives W-36 one numbered-unit entrance while keeping the shared mass/roof.
- Manual tight-frontage entries now allow narrow historic door widths when the mapped frontage is very short. This restores the `N-52` high-bay entrance and keeps the `N-40-42` south `Vitrine` as door + glass panel instead of only a door.
- Fixed PRD-003 rehydration so `is_party_wall` and neighbor height metadata survive from `buildings.json` into the final render.
- Rebuilt `data/parsed/buildings.json`.
- Rebuilt `output/gltf/block147.glb`.
- Rebuilt `output/ifc/block147.ifc`.
- Rebuilt `output/gltf/block147.glb` and `output/ifc/block147.ifc` after the Fırın/N-40-42/N-52-54-E2 corrections.
- Re-rendered manual `output/buildings/N-40-42/N-40-42.glb`.
- Added `output/reports/roof_visual_audit.md`.
- Added `output/reports/scene_source_audit.md`.
- Added `output/reports/adjacency_opening_audit.md`.

## Recommended Next Fixes

1. Manually interpret the remaining shared `×` evidence between `N-46/N-48` before adding any gate or facade opening there.
2. Use facade photos or a sharper map crop before changing exact upper-window spacing/counts or adding repeated shopfront/display glass.
3. Continue the same one-by-one section-line audit on remaining ambiguous rows; do not split a building unless the map line clearly marks a physical area/height boundary.
