# Building-by-Building Map/KML Review

Date: 2026-05-11

This is the active one-by-one control sheet for Block 147. It compares each visible 3D mesh against the KML/SHP footprint, the Pervititch raster labels, roof notes, height notes, and entrance evidence. The rule for the current model is strict: doors/shopfronts/vitrines require map/manual evidence; upper windows are allowed only on geometry-detected exposed street/courtyard faces or party walls exposed above a lower neighbor.

## Corrected Composite Buildings

| area | source KML/SHP | current 3D interpretation | height / roof check | entrances / openings | status |
|---|---|---|---|---|---|
| `N-40-42` | `building-entrence-40-42.shp` | One long wooden building beside the Fırın. The black division lines are now treated as building-area boundaries, not decorative roof marks. | Three rectangular stepped zones: 2-storey north frontage, 4-storey middle bay, 3-storey south/vitrine bay; all use wooden class C material. | Two north doors for 40/42 frontage; south vitrine/service opening remains only where mapped. | Corrected after user review; old six-zone tiny split removed. |
| `N-52-54-E2` | `building-entrence-52-54-02.shp` | One single NE corner building. The 52, 54, and 02 labels are frontage/entrance references on the same building. | One continuous 3-storey masonry mass with one hip roof; no high/low split and no triangular N-54 corner mass. | Two north doors for 52/54 and one east door for 02. No shopfront glass. | Corrected after user review; old two-zone interpretation removed. |
| `S-41-43-45-E16` | `building-entrence-41-43-45-16.shp` | Four joined building/entrance units under one connected south/east corner mass. The visible model keeps one mass but adds facade seams so 41/43/45/16 read as four combined units. | One shared sheet-metal/`T` hip roof; no separate cut roofs. | Three south doors for 41/43/45, one east door for 16, and subtle vertical facade seams between the south units. Detected upper windows only on exposed faces. | Corrected as 4-unit combination under one roof. |
| `W-34-36-FIRIN` | `building-entrence-34-36-38.shp` | One connected Fırın masonry mass. The map text reads Firin/VF/MB/2½/TR.4/3+, not Mg.; source override keeps 38 with W-32, not this bakery. | Single coherent gable/TR tile roof across the bakery mass; the previous grey cut-roof patch is removed. | One Firin street/service entrance on the short diagonal/kinked west corner for 34; W-36 is internal-only. No magazine shutter row. Detected upper windows only on exposed faces. | Corrected after user review; no separate W-36 roof shard remains. |

## Single / Smaller Buildings

| area | source KML/SHP | height / roof reading | entrance decision | status |
|---|---|---|---|---|
| `N-44` | `building-entrence-44.shp` | 3 storeys, VT/vault note, roof material unreadable. `×` mark is now treated as roof tabatiere/skylight. | Keeps one north door from mapped arrow. Detected upper windows on exposed faces; no shopfront glass. | Corrected conservative; `×` did not create a facade opening. |
| `N-46` | `building-entrence-46.shp` | 2 storeys, VF/vault note, unknown roof. Shared `×` with N-48 is ambiguous. | One conservative north door from numbered entrance fallback. Detected upper windows on exposed faces. | Corrected; shared `×` still does not create an extra gate/window. |
| `N-48` | `building-entrence-48.shp` | 2 storeys, VF + TF tile roof. Shared/nearby `×` is now treated only as roof tabatiere/skylight evidence. | One conservative north door from numbered entrance fallback. Detected upper windows on exposed faces; no shopfront glass. | Corrected; no added facade glass beyond the numbered door. |
| `N-50` | `building-entrence-50.shp` | 3 storeys, roof material unreadable. | Keeps one north door from mapped arrow. Detected upper windows on exposed/height-break faces; no shopfront glass. | Good working model; roof material unknown. |
| `E-4` | `building-entrence-04.shp` | 1-storey yellow wooden shop, sheet-metal `T` roof. | One east door. | Good working model. |
| `E-4a` | `at-the-green-area-wooden-at-147-block-near-the-church-middle-of-the-block.shp` | 1-storey yellow wooden annex near church edge, TF/tile note. | Courtyard/internal access only. | Good working model. |
| `E-6` | `building-entrence-06.shp` | 1-storey masonry, VF + TF tile roof. Raw register says `1–2`, but enlarged crop does not prove a second-storey break. | One east door. | Good working model; keep one storey until sharper evidence. |
| `E-8` | `building-entrence-08.shp` | 1-storey masonry, VF + TF tile roof. Raw register says `1–2`, but enlarged crop does not prove a second-storey break. | One conservative east door from numbered entrance fallback; map dash is still not treated as a second opening. | Corrected conservative; keep one storey until sharper evidence. |
| `E-10` | `building-entrence-10.shp` | 1-storey masonry, VF/YF + TF tile roof. Direction marker near the 10 entry is kept as roof-review evidence, not as a height split. | One east door. | Rechecked; keep one storey and no extra shopfront/window invention. |
| `E-12` | `building-entrence-12.shp` | Re-read as one-storey `1p.Mg`/`VF` shop, not the old `2p` full second-storey interpretation. Roof is now shallow barrel/vault form with TF tile material. | One east door only; upper windows removed. | Corrected after map review. |
| `E-14` | `building-entrence-14.shp` | 1-storey masonry, TF tile roof; entrance arrow is clearest on east row. Checked for two-height split, but the visible crop does not prove a real internal height boundary. | One east door. | Keep one mass until sharper map/photo evidence confirms a split. |
| `W-32#1` | `near-39-open-32-magazine.shp` | One-storey tiny massive-stone magazine, 3.0 m wall height, low flat/unknown roof. | West door only. | Corrected from old 2-storey Excel interpretation; no speculative gable or upper window. |
| `W-32#2` | `near-39-open-32-the last-corner-triangular-magazine.shp` | One-storey tiny triangular/corner magazine, 3.0 m wall height, low flat/unknown roof. | West door only. | Corrected; this is the only accepted triangular corner shop geometry, not an invented taller building. |
| `W-32#3` | `near-39-open-32-the middle-magazine.kml` | One-storey tiny massive-stone magazine, 3.0 m wall height, low flat/unknown roof. | West door only. | Corrected from old 2-storey Excel interpretation; no speculative gable or upper window. |
| `W-39-1` | `churche-entrence-camli-area-(39-1,-39-2)-clocher.shp` | Manual split: west `camli_vitre_passage` is the only glass zone, with complex pitched glass roof; east `masonry_side_narthex` is opaque masonry with hip sheet-metal roof. Clocher remains pinned to the map's lower-right square. | West camli/vitre door + glass bay only; east narthex door only, no shopfront glass. | Corrected: no longer one all-glass flat-roof block; follows the dashed/diagonal roof reading. |
| `W-39/2` | `cesme-fountain.kml` | Fountain, non-building. | No doors/windows. | OK. |
| `CHURCH` | `churche-and-its-kubbe.kml` | Continuous low kiremit roof, lead/zinc dome collar, kubbe/drum centered at georeferenced UTM `(670342.95, 4539707.85)`, lantern, clocher, and arched nave body windows on the long exposed faces. | Special church mesh; body windows are church-typology arched panes, not parcel shopfront openings. | Corrected for previously blank church body walls behind W-32 and for centroid-based kubbe placement. |

## Next Focus

1. Inspect the 3D roof look for `N-52-54-E2` and `W-34-36-FIRIN` after the new height zones.
2. Decide whether the remaining shared `×` between `N-46/N-48` also represents a gate/opening; do not add it without clearer map/photo evidence.
3. Fine-tune exact internal split lines only where the map crop is clear enough; avoid creating extra standalone buildings from interior labels.
