# PRD-005 — Manual per-parcel labelling (replace Excel)

**Status:** Draft
**Iteration:** 5 of N
**Depends on:** PRD-001 (KML/SHP footprints still valid), PRD-003 (3D pipeline still valid)
**Supersedes:** the Excel register as source of truth

---

## 1. Goal

Replace `Block147_Pervititch_BIM_v3_FINAL (1).xlsx` as the authoritative source
of attributes. The register contradicts the 1923 map (e.g. N-42 as wooden
when the map clearly shows pink/masonry), treats multi-zone buildings like
N-40 (wooden Firin + masonry body) as uniform, and lacks the per-zone
richness we need for LOD3. Instead: **one JSON file per parcel, hand-written
from the map, reviewed building-by-building.**

## 2. File layout

```
data/manual/
├── parcels/
│   ├── N-40.json         # map-read truth for one parcel
│   ├── N-42.json
│   ├── N-44.json
│   └── ...
└── schema.md             # documents the JSON shape
```

One file per `parcel_id`. Existence of the file == "this parcel is
hand-labelled and verified against the map".

## 3. JSON schema

```json
{
  "parcel_id": "N-40",
  "verified": false,
  "map_notes": "FIRIN bakery on NW corner; two zones visible",

  "footprint_ref": "building-entrence-40-42.shp",

  "structure_type": "building",

  "zones": [
    {
      "id": "north_firin",
      "description": "FIRIN bakery body, yellow on map",
      "material_class": "C",
      "map_colour": "yellow",
      "storeys_above_grade": 2.5,
      "has_mezzanine": true,
      "has_basement": false,
      "storey_heights_m": [3.8, 2.2, 3.2],
      "ground_floor_use": "bakery",
      "roof": {
        "shape": "vault_flat",
        "material": "vault_VF",
        "pitch_deg": 2.86,
        "has_chimney": true,
        "has_skylight": false
      },
      "footprint_fraction": [0.0, 0.55]
    },
    {
      "id": "south_body",
      "description": "Masonry shop body behind bakery",
      "material_class": "B",
      "map_colour": "pink",
      "storeys_above_grade": 3,
      "storey_heights_m": [3.8, 3.2, 3.2],
      "ground_floor_use": "shop",
      "roof": {
        "shape": "hip",
        "material": "tile_TR",
        "pitch_deg": 30,
        "has_chimney": false
      },
      "footprint_fraction": [0.55, 1.0]
    }
  ],

  "facades": {
    "street_facing_faces": ["N", "W"],
    "primary_door": { "face": "N", "zone": "north_firin" },
    "secondary_door": { "face": "W", "zone": "south_body" },
    "shop_windows": true,
    "balconies": [],
    "shutters_on_upper": true
  },

  "palette_override": null,

  "excel_notes_legacy": "wall_code Mg.+VF+MB+2½+TR.4+3.T — matches zone split"
}
```

### Field semantics
- **`zones`** — 1-N sub-volumes of the footprint. Each zone is a distinct
  height/material/roof region. `footprint_fraction` splits the footprint
  along its long axis (`[0, 0.55]` = "first 55 % from south end"). For
  buildings where one axis isn't enough we'll add `footprint_split_line`
  as a manual polygon later; for now `footprint_fraction` handles all
  Block 147 cases.
- **`structure_type`** — `building`, `fountain`, `bell_tower`, `monument`.
- **`facades.street_facing_faces`** — manually-assigned cardinal faces
  (N/E/S/W). Overrides any auto-detected guesses.
- **`palette_override`** — optional `{wall_main, trim, roof, ...}` RGB tuples
  to bypass the default palette for this parcel.

## 4. Pipeline changes

### PRD-002 (buildings model)
- New **`ManualLabelLoader`** reads every `data/manual/parcels/*.json`
- Produces `Building` dataclasses directly (one per zone ⇒ sub-buildings
  sharing `parent_parcel_id`; or one Building with internal zone metadata
  — TBD, propose zone = sub-Building for rendering simplicity).
- When no manual file exists → Building is **skipped** (not rendered).
  Incremental rollout: we only render what's been labelled + verified.
- The Excel assembler becomes **legacy fallback** (moved to
  `hums/parsing/excel_legacy.py`), only invoked with `--legacy-excel` flag.

### PRD-003 (geometry)
- No major change; `BuildingGeometryBuilder` already operates on the
  `Building` dataclass. Zone splitting happens before it.

### New CLI
- `make label PARCEL=N-40` → opens the JSON file in `$EDITOR`, or creates
  from a template if missing.
- `make render-building PARCEL=N-40` → unchanged, but now reads the manual
  label.
- `make verified` → lists which parcels are `verified: true`, which are
  labelled but unverified, which are missing.

## 5. Workflow

1. I read the Pervititch map tile for parcel X, draft its JSON.
2. `make render-building PARCEL=X` produces the glTF + profile.
3. User reviews, corrects.
4. I update JSON, re-render.
5. User marks `"verified": true` when happy.
6. Commit.
7. Move to next parcel.

## 6. Success criteria

- [ ] Every parcel file validates against the schema (simple pydantic/dataclass check).
- [ ] Rendering pipeline uses manual data when present, ignores Excel.
- [ ] N-40 is the first verified parcel — multi-zone with chimney, matches map.
- [ ] `verified` count in `make verified` grows monotonically as we work through the block.

## 7. Excel disposition

Move the xlsx to `data/raw/_deprecated/` next to the old block KMLs. Keep
for archaeology; no pipeline reads it by default.

## 8. Sign-off

User approves this PRD → I scaffold the folder + write `schema.md` + draft
`N-40.json` from my map reading → user reviews N-40 → go/no-go for rollout.
