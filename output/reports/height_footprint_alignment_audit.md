# Height + Footprint Alignment Audit

Generated from the actual visible scene. This report checks whether the final 3D ground footprints still cover their source KML/SHP polygons and whether current model heights follow the map/Excel height notes. It does not add visual guesses: ambiguous labels stay flagged.

## Footprint Coverage

| visible group | source KML/SHP | source area m2 | visible area m2 | missing m2 | outside m2 | verdict |
|---|---|---:|---:|---:|---:|---|
| `CHURCH` | `churche-and-its-kubbe.kml` | 320.23 | 320.23 | 0.00 | 0.00 | OK exact/near-exact |
| `E-10` | `building-entrence-10.shp` | 25.93 | 25.93 | 0.00 | 0.00 | OK exact/near-exact |
| `E-12` | `building-entrence-12.shp` | 13.24 | 13.24 | 0.00 | 0.00 | OK exact/near-exact |
| `E-14` | `building-entrence-14.shp` | 37.60 | 37.60 | 0.00 | 0.00 | OK exact/near-exact |
| `E-4` | `building-entrence-04.shp` | 26.64 | 26.64 | 0.00 | 0.00 | OK exact/near-exact |
| `E-4a` | `at-the-green-area-wooden-at-147-block-near-the-church-middle-of-the-block.shp` | 37.28 | 37.28 | 0.00 | 0.00 | OK exact/near-exact |
| `E-6` | `building-entrence-06.shp` | 25.11 | 25.11 | 0.00 | 0.00 | OK exact/near-exact |
| `E-8` | `building-entrence-08.shp` | 22.37 | 22.37 | 0.00 | 0.00 | OK exact/near-exact |
| `N-40-42` | `building-entrence-40-42.shp` | 50.41 | 50.41 | 0.00 | 0.00 | OK exact/near-exact |
| `N-44` | `building-entrence-44.shp` | 55.78 | 55.78 | 0.00 | 0.00 | OK exact/near-exact |
| `N-46` | `building-entrence-46.shp` | 35.64 | 35.64 | 0.00 | 0.00 | OK exact/near-exact |
| `N-48` | `building-entrence-48.shp` | 50.23 | 50.23 | 0.00 | 0.00 | OK exact/near-exact |
| `N-50` | `building-entrence-50.shp` | 39.65 | 39.65 | 0.00 | 0.00 | OK exact/near-exact |
| `N-52-54-E2` | `building-entrence-52-54-02.shp` | 65.80 | 65.80 | 0.00 | 0.00 | OK exact/near-exact |
| `S-41-43-45-E16` | `building-entrence-41-43-45-16.shp` | 90.24 | 90.24 | 0.00 | 0.00 | OK exact/near-exact |
| `W-32#1` | `near-39-open-32-magazine.shp` | 10.33 | 10.33 | 0.00 | 0.00 | OK exact/near-exact |
| `W-32#2` | `near-39-open-32-the last-corner-triangular-magazine.shp` | 3.37 | 3.37 | 0.00 | 0.00 | OK exact/near-exact |
| `W-32#3` | `near-39-open-32-the middle-magazine.kml` | 3.61 | 3.61 | 0.00 | 0.00 | OK exact/near-exact |
| `W-34-36-FIRIN` | `building-entrence-34-36-38.shp` | 97.25 | 97.25 | 0.00 | 0.00 | OK exact/near-exact |
| `W-39/1` | `churche-entrence-camli-area-(39-1,-39-2)-clocher.shp` | 166.11 | 166.11 | 0.00 | 0.00 | OK exact/near-exact |
| `W-39/2` | `cesme-fountain.kml` | 7.64 | 7.64 | 0.00 | 0.00 | OK exact/near-exact |

## Visible Height / Roof Check

| visible mesh | source height note | current wall height m | roof | height verdict |
|---|---|---:|---|---|
| `CHURCH` | church special mass + clocher | 17.1 clocher top | low tile roof + kubbe | OK special, visually check roof only |
| `E-10` | `1–2` + map direction marker | 3.8 | `gable/tile_TF` | OK after recheck: direction marker noted, but no confirmed height split |
| `E-12` | map reread: `1p.Mg`/`VF` more likely than old parsed `2p` | 3.8 | `vault_flat/tile_TF` | Corrected: one-storey shop, barrel/vault roof, no upper windows |
| `E-14` | `1–2` + entrance arrow | 3.8 | `gable/tile_TF` | Checked for two heights; no confirmed internal height boundary |
| `E-4` | `1 above grade` | 3.8 | `gable/sheet_metal_T` | OK |
| `E-4a` | `1` | 3.8 | `gable/tile_TF` | OK |
| `E-6` | `1–2` | 3.8 | `gable/tile_TF` | AMBIGUOUS 1-2 on map/Excel; current model uses parsed count |
| `E-8` | `1–2` | 3.8 | `gable/tile_TF` | AMBIGUOUS 1-2 on map/Excel; current model uses parsed count |
| `N-40-42.north_two_storey` | `40, 42, M, 2 b` | 7.0 | `gable/sheet_metal_T` | OK user-corrected: north rectangular 2-storey zone with 40/42 frontage entrances |
| `N-40-42.middle_four_storey` | `V.T., 4 b` | 13.0 | `gable/sheet_metal_T` | OK user-corrected: middle rectangular 4-storey zone |
| `N-40-42.south_three_storey_vitrine` | `Vx., 3.T., Vitr.` | 10.2 | `gable/sheet_metal_T` | OK user-corrected: south rectangular 3-storey/vitrine zone |
| `N-44` | `Δ3` | 10.2 | `gable/unknown` | OK; roof material unreadable |
| `N-46` | `Δ2` | 7.0 | `gable/unknown` | OK; roof material unreadable |
| `N-48` | `Δ2` | 7.0 | `gable/tile_TF` | OK |
| `N-50` | `3MO (3 upper)` | 10.2 | `gable/unknown` | OK; roof material unreadable |
| `N-52-54-E2.corner_mass` | `52, 54, 02, 3E, VF, Mg., 1-2` | 10.2 | `hip/unknown` | OK user-corrected: one corner building, numbers treated as entrances/labels |
| `S-41-43-45-E16.merged_mass` | `41, 43, 45, 16, Mg., T` | 7.0 | `hip/sheet_metal_T` | OK user-corrected: four joined units under one common roof |
| `W-32#1` | `2` in old Excel row, corrected by map/user reading | 3.0 | `flat/unknown` | OK user-corrected: one-storey tiny magazine; no speculative gable |
| `W-32#2` | `2` in old Excel row, corrected by map/user reading | 3.0 | `flat/unknown` | OK user-corrected: one-storey tiny magazine; no speculative gable |
| `W-32#3` | `2` in old Excel row, corrected by map/user reading | 3.0 | `flat/unknown` | OK user-corrected: one-storey tiny magazine; no speculative gable |
| `W-34-36-FIRIN.bakery_mass` | `Firin, VF, MB, 2 1/2, TR.4, 3+, 34, 36` | 10.2 | `gable/tile_TR` | OK user-corrected: single coherent bakery mass; one Firin service/street door, no Mg. shutter row |
| `W-39-1.camli_vitre_passage` | `Camli/Vitre`, dashed/diagonal roof lines | 3.8 | `complex_pitched/glass_roof` | OK manual zoned: only this part is glass |
| `W-39-1.masonry_side_narthex` | side mass, `2p`, `T`, Clocher edge | 6.0 | `hip/sheet_metal_T` | OK manual zoned: opaque side mass, not glass |
| `W-39/2` | `1 (low monumental)` | 1.8 | `gable/unknown` | OK; roof material unreadable |

## Manual Replacement Height Cross-Check

| manual model | replaced original parcels | original parsed heights | current zones | risk |
|---|---|---|---|---|
| `N-40-42` | N-40, N-42 | N-40: 9.2m (2½, complex_pitched/vault_VF)<br>N-42: 13.4m (4b, flat/sheet_metal_T) | north_two_storey: 7.0m (['40', '42', 'M', '2 b'], gable/sheet_metal_T)<br>middle_four_storey: 13.0m (['V.T.', '4 b'], gable/sheet_metal_T)<br>south_three_storey_vitrine: 10.2m (['Vx.', '3.T.', 'Vitr.'], gable/sheet_metal_T) | OK user-corrected: three rectangular height zones from the black division lines |
| `N-52-54-E2` | E-2, N-52, N-54 | E-2: 3.8m (1–2, gable/unknown)<br>N-52: 10.2m (3E (3 étage), gable/unknown)<br>N-54: 3.8m (1–2, hip/unknown) | corner_mass: 10.2m (['52', '54', '02', '3E', 'VF', 'Mg.', '1-2'], hip/unknown) | OK user-corrected: one building; mixed notes retained as provenance, not separate visible masses |
| `S-41-43-45-E16` | E-16, S-41, S-43, S-45 | E-16: 7.0m (2p, gable/unknown)<br>S-41: 7.0m (2p, flat/sheet_metal_T)<br>S-43: 3.8m (1–2, gable/unknown)<br>S-45: 3.8m (1–2, gable/unknown) | merged_mass: 7.0m (['41', '43', '45', '16', 'Mg.', 'T'], hip/sheet_metal_T) | OK user-corrected: keep as one shared-roof row; mark frontage units with facade seams rather than separate masses |
| `W-34-36-FIRIN` | W-34, W-36 | W-34: 10.2m (3+, gable/tile_TR)<br>W-36: 9.2m (2½, vault_flat/vault_VF) | bakery_mass: 10.2m (['Firin', 'VF', 'MB', '2 1/2', 'TR.4', '3+', '34', '36'], gable/tile_TR) | OK user-corrected: W-34 has one Firin street/service door; W-36 is internal-only |

## Current Findings

- All visible group unions are aligned to their source KML/SHP footprints within tolerance. Shape errors are therefore likely internal zone/split issues rather than the outer KML placement drifting.
- Height/roof ambiguity remains on: `E-14`, `E-6`, `E-8`.
- Manual rectangular/axis splits still require visual hand-check where the map only gives labels. `N-40-42` was corrected from the black division lines into 2/4/3-storey rectangular zones; `N-52-54-E2` was corrected to one corner building.

## Visual Follow-Up Notes

- `E-6`, `E-8`, and `E-14`: the automated warning comes from `1–2` style raw height text in the parsed register. On the enlarged map crop (`output/reports/detail_crops/east_row_E4_E14_x3.png`) these do not read as clear multi-height buildings. Current one-storey masses are therefore kept until a sharper source confirms a second-storey/partial-height break.
- `E-10`: the map direction marker near the numbered entry is preserved as a roof-review note, but it is not read as a height split.
- `E-12`: corrected from the old parsed `2p` interpretation to a one-storey `1p.Mg`/`VF` reading with a shallow barrel/vault roof and no upper windows.
- `S-41-43-45-E16`: the old parsed split has mixed heights (`2p` for E-16/S-41, lower/ambiguous for S-43/S-45). The current model follows the user/map interpretation that 41/43/45/16 are four joined entrance/building units under one connected roof. The south frontage now has subtle vertical division seams, but the roof and mass remain shared.
- `N-52-54-E2`: user clarified 52/54/02 is one building. The visible model is now one corner mass with three entrance references.
- `W-34-36-FIRIN`: current model keeps one connected bakery complex and one coherent tile roof. The previous separate W-36 grey/cut roof shard was removed after user review.
