# N-40-42 — Manual Rendering Profile

- parcel_ids: **N-40, N-42**
- verified: **False**
- structure_type: building
- primary_zone_axis: **north_to_south**
- zones rendered: **6** / 6
- total faces: **384**

## Map notes

Long thin wooden building on the NW side of block 147, fronting T…L Sokak at its north/street end and extending south into the block toward the church courtyard. Registered cadastrally under two parcel numbers (40) and (42) but architecturally it is ONE single mass — the map labels `(40)(42)` together above the footprint. Yellow tint throughout = wooden frame (class C). Interior labels, stacked north→south along the building's length, describe a sectional composition: street-end magasin, Turkish-vault middle zone with 4 basement bays, an 'old' (V.x.) vault zone, a 3-storey section, and a shop window (Vitrine) at the far south end. NOTE: the FIRIN bakery label on the wider Pervititch screenshot belongs to a DIFFERENT yellow strip, not this building — confirmed by user. No oven chimney on this one.

## Zones

### street_magasin  (C, 1.0-storey, flat/sheet_metal_T)
- description: Street-end magasin at the T…L Sokak frontage. Map labels: Y (yellow) + 1.M (1-storey magasin).
- map_labels: ['Y', '1.M']
- footprint_fraction: (0.0, 0.18)
- vertices / faces: 416 / 102
  - CorniceSurface: 57
  - PlinthSurface: 18
  - WallSurface: 17
  - Door: 3
  - JambSurface: 2
  - GroundSurface: 1
  - HeaderSurface: 1
  - SillSurface: 1
  - Window: 1
  - RoofSurface: 1

### middle_vault  (C, 2.0-storey, vault_flat/vault_VT)
- description: 2-bay Turkish vault zone with Turkish brick arch ceiling.
- map_labels: ['2.b', 'V.T.']
- footprint_fraction: (0.18, 0.42)
- vertices / faces: 350 / 88
  - CorniceSurface: 27
  - WallSurface: 18
  - JambSurface: 8
  - RoofSurface: 8
  - Mullion: 7
  - HeaderSurface: 4
  - SillSurface: 4
  - Window: 4
  - PlinthSurface: 3
  - StringcourseSurface: 3
  - GroundSurface: 1
  - FloorSurface: 1

### basement_bays  (C, 2.0-storey, vault_flat/vault_VT)
- description: 4 basement bays (sub-grade) under this section. Rendered as an additional basement storey on the zone above; does not add an above-grade mass.
- map_labels: ['4 b']
- footprint_fraction: (0.42, 0.58)
- vertices / faces: 142 / 36
  - WallSurface: 12
  - RoofSurface: 8
  - JambSurface: 4
  - Mullion: 4
  - HeaderSurface: 2
  - SillSurface: 2
  - Window: 2
  - GroundSurface: 1
  - FloorSurface: 1

### old_vault_zone  (C, 2.0-storey, vault_flat/vault_VT)
- description: 'V.x.' zone — probably an older (vieux) vault section, possibly in poorer condition on the map.
- map_labels: ['V.x.']
- footprint_fraction: (0.58, 0.72)
- vertices / faces: 142 / 36
  - WallSurface: 12
  - RoofSurface: 8
  - JambSurface: 4
  - Mullion: 4
  - HeaderSurface: 2
  - SillSurface: 2
  - Window: 2
  - GroundSurface: 1
  - FloorSurface: 1

### rear_three_storey  (C, 3.0-storey, hip/sheet_metal_T)
- description: Tallest section at the rear (south end) — 3 storeys with sheet metal T roof.
- map_labels: ['3.T.']
- footprint_fraction: (0.72, 0.92)
- vertices / faces: 420 / 104
  - WallSurface: 32
  - JambSurface: 18
  - Mullion: 18
  - HeaderSurface: 9
  - SillSurface: 9
  - Window: 9
  - RoofSurface: 6
  - FloorSurface: 2
  - GroundSurface: 1

### vitrine  (C, 1.0-storey, flat/sheet_metal_T)
- description: Shop window (Vitrine) at the far south end facing the church courtyard. Low 1-storey glazed annex.
- map_labels: ['Vitr.']
- footprint_fraction: (0.92, 1.0)
- vertices / faces: 70 / 18
  - WallSurface: 8
  - Door: 3
  - JambSurface: 2
  - GroundSurface: 1
  - HeaderSurface: 1
  - SillSurface: 1
  - Window: 1
  - RoofSurface: 1

## Open questions

- Which adjacent yellow strip IS the actual FIRIN? Need to identify the correct parcel and add chimney + bakery use to that one, not this.