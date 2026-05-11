# W-34-36-FIRIN — Manual Rendering Profile

- parcel_ids: **W-34, W-36**
- verified: **False**
- structure_type: building
- primary_zone_axis: **long_axis_north_to_south**
- zones rendered: **1** / 1
- total faces: **399**

## Map notes

`building-entrence-34-36-38` traces the Firin block on the north-west corner. The map text on this footprint reads Firin with VF/MB, 2 1/2, TR.4 and 3+ construction notes, so do not render it as a row of Mg./magazine storefronts. Model one connected masonry bakery mass with one coherent TR/tile roof, but keep the visible numbered entries 34, 36 and 38 as three distinct bakery/service entrances on the street frontage. The 34/Firin entry sits on the short diagonal/kinked west corner; 36 and 38 remain on the long west frontage. User-supplied 2024 street photos are used only as facade-material language here: pale plaster masonry and restrained bakery/service base, not copied modern signage or changed footprint geometry.

## Zones

### bakery_mass  (B, 3.0-storey, gable/tile_TR)
- description: Single connected Firin masonry mass. Internal number lines are frontage/entry divisions; no separate cut roof is generated.
- map_labels: ['Firin', 'VF', 'MB', '2 1/2', 'TR.4', '3+', '34', '36', '38']
- footprint_fraction: (0.0, 1.0)
- vertices / faces: 1600 / 399
  - CorniceSurface: 108
  - WallSurface: 66
  - JambSurface: 55
  - Mullion: 48
  - HeaderSurface: 29
  - SillSurface: 26
  - Window: 23
  - StringcourseSurface: 14
  - RoofSurface: 10
  - Door: 9
  - PlinthSurface: 8
  - FloorSurface: 2
  - GroundSurface: 1

## Open questions

- Firin height/roof notes combine 2 1/2, 3+, VF/MB and TR.4. Current visual priority is a coherent, non-cut single bakery roof; a finer stepped roof can be added only where the map division lines clearly require it without creating fake separate masses.