# `data/manual/parcels/<parcel_id>.json` schema

One JSON file per Block-147 parcel. Written from map reading, not Excel.
When present, this file is the **sole source of truth** for that parcel.

## Top-level fields

| field | type | required | notes |
|---|---|---|---|
| `parcel_id` | string | ✓ | e.g. `N-40`, `W-39/1`, `INT-N2` |
| `verified` | bool | ✓ | `true` = user has approved the 3D render |
| `map_notes` | string | ✓ | human description of what the map shows |
| `footprint_ref` | string |   | filename of the KML/SHP used as outline |
| `structure_type` | enum |   | `building` (default) / `fountain` / `bell_tower` / `monument` |
| `zones` | array[Zone] | ✓ | 1+ sub-volumes within the footprint |
| `facades` | Facades | ✓ | street/courtyard + opening hints |
| `palette_override` | object |   | per-parcel RGB palette when period defaults are wrong |
| `excel_notes_legacy` | string |   | copy of old Excel's wall_code / bim_notes for reference only |

## `Zone`

| field | type | notes |
|---|---|---|
| `id` | string | unique within this parcel |
| `description` | string | human description |
| `material_class` | enum | `A` (hard stone) / `B` (plastered masonry) / `C` (wooden frame) |
| `map_colour` | enum | `yellow` (C) / `pink` (A/B) |
| `storeys_above_grade` | number | e.g. 2.5 means ground + mezzanine + one upper |
| `has_mezzanine` | bool | |
| `has_basement` | bool | |
| `storey_heights_m` | array[number] | one entry per storey, ground → top |
| `ground_floor_use` | string | `bakery` / `shop` / `residential` / `magazine` / `passage` / `none` |
| `roof` | Roof | see below |
| `footprint_fraction` | [number, number] | `[0, 1]` = whole footprint; `[0, 0.55]` = first 55% along long axis |
| `clip_ranges` | array | optional sequential clips like `{axis, fraction}` for rectangular sub-areas that need two-axis map splits |

## `Roof`

| field | type | notes |
|---|---|---|
| `shape` | enum | `flat` / `gable` / `hip` / `mansard` / `complex_pitched` / `vault_flat` |
| `material` | enum | `tile_TR` / `sheet_metal_T` / `vault_VF` / `vault_VT` / `lead` |
| `pitch_deg` | number |   |
| `has_chimney` | bool |   |
| `has_skylight` | bool |   |

## `Facades`

| field | type | notes |
|---|---|---|
| `street_facing_faces` | array[N/E/S/W] | manually assigned |
| `primary_door` | `{face, zone}` | door on this face, belongs to this zone |
| `secondary_door` | `{face, zone}` or null |  |
| `shop_windows` | bool | if true, ground floor of relevant zone gets shop glazing |
| `balconies` | array[`{face, storey}`] |  |
| `shutters_on_upper` | bool |  |

## Example

See `N-40.json` for the first worked example.
