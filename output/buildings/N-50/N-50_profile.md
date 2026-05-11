# N-50 — Manual Rendering Profile

- parcel_ids: **N-50**
- verified: **False**
- structure_type: building
- primary_zone_axis: **long_axis_south_to_north**
- zones rendered: **2** / 2
- total faces: **142**

## Map notes

Parcel 50 is not a single flat 3-storey block. The Pervititch crop shows a right/rear open void and a height/roof change. Split the mass approximately through the centre of its long axis: the front/north half is the lower 2-unit flat-roofed part, while the rear/dashed half is the taller 3-unit roofed part. In the rear half, the right-side quarter is missing down to ground level, so model it as a real L-plan cut/open lightwell, not as a shallow roof mark or separate grey box.

## Zones

### north_front_two_storey_flat  (B, 2.0-storey, flat/unknown)
- description: Lower north/front masonry mass for the numbered 50 entrance; front half reads flatter on the map.
- map_labels: ['50', '2?', 'front/lower flat half']
- footprint_fraction: (0.0, 0.66)
- vertices / faces: 322 / 81
  - CorniceSurface: 30
  - WallSurface: 13
  - Door: 13
  - JambSurface: 6
  - PlinthSurface: 5
  - StringcourseSurface: 3
  - HeaderSurface: 2
  - SillSurface: 2
  - Mullion: 2
  - RoofSurface: 2
  - GroundSurface: 1
  - FloorSurface: 1
  - Window: 1

### south_rear_three_storey_roofed  (B, 3.0-storey, gable/unknown)
- description: Taller south/rear wing; the right-side quarter of this rear half is missing down to grade as the open lightwell.
- map_labels: ['rear dashed roofed half', 'right quarter open to ground', '3?']
- footprint_fraction: (0.66, 1.0)
- vertices / faces: 245 / 61
  - WallSurface: 24
  - JambSurface: 8
  - Mullion: 7
  - RoofSurface: 7
  - HeaderSurface: 4
  - SillSurface: 4
  - Window: 4
  - FloorSurface: 2
  - GroundSurface: 1

## Open questions

- The exact handwritten height abbreviation on N-50 remains soft in the raster, but the latest map reread/user correction sets the front/north part as 2-unit flat and the rear/dashed part as 3-unit roofed.