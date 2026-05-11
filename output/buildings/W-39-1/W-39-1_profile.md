# W-39-1 — Manual Rendering Profile

- parcel_ids: **W-39/1**
- verified: **False**
- structure_type: building
- primary_zone_axis: **west_to_east**
- zones rendered: **3** / 3
- total faces: **590**

## Map notes

The W-39/1 church-edge footprint must not be rendered as one all-glass block. The Pervititch crop shows Camli/Vitre only on the lower hatched passage; the user-supplied front photo confirms this is the Ayia Efimia church entrance: normal plastered low narthex walls, white double door, a glazed/iron arched fanlight above the door, and glass only at the top/roof zone. The Camli/Vitre roof/entry zone stops at the earlier vertical map break; the masonry/brick-narthex zone starts there so the glass-top area does not overlap brick/concrete massing. The adjacent yellow/wooden church-edge area labelled T. 1 bs. is not glass; it is a wooden one-storey-plus-basement annex with sheet-metal T roof. The church body face looking toward this wooden annex is interpreted as an internal/service side; those openings are interior doors, not exterior glass windows. The east/right area near the Clocher square remains an opaque side/narthex mass.

## Zones

### camli_vitre_passage  (B, 1.0-storey, complex_pitched/glass_roof)
- description: Lower blue-hatched Camli-Vitre church entrance passage. Photo correction: walls are normal plaster/masonry, not glass; the camli/vitre reading belongs to the top glass roof/light and to the arched fanlight/transom over the white church door.
- map_labels: ['Camli', 'Vitre', 'church entrance', 'arched glazed fanlight']
- footprint_fraction: (0.0, 0.68)
- vertices / faces: 946 / 221
  - CorniceSurface: 111
  - Mullion: 44
  - Door: 20
  - PlinthSurface: 16
  - JambSurface: 9
  - WallSurface: 6
  - RoofSurface: 5
  - HeaderSurface: 4
  - SillSurface: 3
  - Window: 2
  - GroundSurface: 1

### wooden_church_edge_annex  (C, 1.0-storey, gable/sheet_metal_T)
- description: Yellow/wooden area adjacent to the lower passage and church, labelled T. 1 bs.; opaque timber annex.
- map_labels: ['T.', '1 bs.', 'wooden/yellow', 'church edge']
- footprint_fraction: (0.0, 0.68)
- vertices / faces: 452 / 115
  - CorniceSurface: 51
  - WoodCladding: 35
  - WallSurface: 14
  - RoofSurface: 5
  - PlinthSurface: 3
  - JambSurface: 2
  - GroundSurface: 1
  - HeaderSurface: 1
  - SillSurface: 1
  - Window: 1
  - Mullion: 1

### masonry_side_narthex  (B, 2.0-storey, hip/sheet_metal_T)
- description: East/right opaque side mass around the Clocher square. It reads as a different masonry material from the transparent passage.
- map_labels: ['side mass', '2p', 'Clocher edge', 'T']
- footprint_fraction: (0.68, 1.0)
- vertices / faces: 1036 / 254
  - CorniceSurface: 84
  - WallSurface: 50
  - JambSurface: 24
  - Mullion: 18
  - RoofSurface: 13
  - HeaderSurface: 12
  - SillSurface: 12
  - Window: 12
  - PlinthSurface: 12
  - StringcourseSurface: 12
  - Door: 3
  - GroundSurface: 1
  - FloorSurface: 1
