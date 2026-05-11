# N-40 — Building Profile

## Excel register (from authoritative spreadsheet)

- parcel_number: **(40)**
- zone: North — NW corner
- street_facing: T…L Sokak (N)
- material class: **C** (Wooden; map colour YELLOW → WOODEN)
- wall_code: `Mg.+VF+MB+2½+TR.4+3.T`
- vault_code: `VF`
- storeys_raw: **2½**
- bim_notes: Wooden GF frontage of the masonry Firin body (98); dual-material BIM required

## Roof + openings (Excel-derived)

- roof shape: **complex_pitched** · material **vault_VF** · pitch 2.86°
- chimney: True, skylight: False
- primary door face (Excel hint): **North (T…L Sok.)**

## Current geometry (what the 3D exporter actually built)

- vertices: 2340
- faces: 585
- footprint_source: **traced**
- local frame rotation: 0.0°
  - WallSurface: 143
  - CorniceSurface: 138
  - Window: 117
  - JambSurface: 38
  - Mullion: 32
  - Shutter: 28
  - HeaderSurface: 19
  - SillSurface: 19
  - StringcourseSurface: 18
  - PlinthSurface: 9
  - Chimney: 9
  - RoofSurface: 6
  - Door: 3
  - SoffitSurface: 3
  - FloorSurface: 2
  - GroundSurface: 1

## Wall segments

| # | face | length (m) | street | party | openings |
|---|---|---|---|---|---|
| 0 | INT | 4.61 | · | ⚠ | 0 |
| 1 | E | 5.14 | ✓ | · | 5 |
| 2 | S | 4.06 | ✓ | · | 5 |
| 3 | W | 7.10 | ✓ | · | 9 |

## Verification checklist (compare with Pervititch screenshot)

- [ ] Footprint shape matches map outline
- [ ] Street-facing side is correct (not on a party wall)
- [ ] Door is on the face Excel says
- [ ] Storey count visibly matches Excel
- [ ] Roof shape matches map indication (gable/hip/vault)
- [ ] Chimney present when map shows FIRIN or equivalent
- [ ] Party walls have no windows
- [ ] Material palette looks right for class A/B/C
- [ ] Windows reasonable count/size for street length