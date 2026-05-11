# Section-Line Interpretation Audit

Date: 2026-05-11

This controls the rule raised during review: vertical/black map lines must be checked before splitting or merging buildings. A line is used as a physical zone boundary only when it reads as an internal building-area/height boundary inside the same footprint. Parcel-border/context lines are not used to create extra roofs or fake standalone masses.

| area | section-line reading | current action | status |
|---|---|---|---|
| `W-34-36-FIRIN` | West-side map text reads Firin/VF/MB/2½/TR.4/3+; 38 is handled by the W-32 source override, not this bakery mass. | One masonry bakery mass, one coherent TR/tile roof, one Firin street/service door for 34 on the short diagonal/kinked west corner; W-36 remains internal-only. | Corrected |
| `N-40-42` | Black internal vertical lines inside the yellow strip read as real height/area zones. | Three rectangular wooden zones: 2-storey north, 4-storey middle, 3-storey south/vitrine. | Corrected |
| `N-52-54-E2` | User clarified 52/54/02 belongs to one building; label/entry references do not create separate masses. | One masonry corner mass, one hip roof, two north doors for 52/54 and one east door for 02. | Corrected |
| `S-41-43-45-E16` | Numbers 41/43/45/16 read as four joined entrance/building units under one connected row. | One connected mass and shared roof, four doors, plus subtle south-facade vertical division seams between the 41/43/45 frontage units. No separate triangular or sliced buildings. | Corrected |
| `N-44`, `N-46`, `N-48`, `N-50` | Visible vertical lines are parcel boundaries between separate north-row buildings. `×` marks are roof/skylight/gate ambiguity, not a new facade opening. | Keep separate KML/SHP buildings; no windows on same-height party walls; no extra shopfront glass. | Keep current |
| `E-4`, `E-6`, `E-8`, `E-10`, `E-12`, `E-14` | East-row vertical lines are parcel boundaries/context edges, not internal zones within one footprint. `E-12` was re-read as `1p.Mg`/`VF` with a barrel/vault roof, not full `2p`; `E-14` was checked but no confirmed two-height boundary was found. | Keep individual footprints; correct E-12 to one storey with vaulted roof and no upper windows; keep E-6/E-8/E-10/E-14 one-storey unless sharper evidence confirms a break. | Corrected / keep current |
| `W-32#1/#2/#3` | Three tiny KMLs are the only small magazine geometries in that corner. | Keep one-storey low shop volumes with west doors only. | Keep current |
| `W-39/1` | Camlı/Vitre hatching and masonry side area read as material/roof split inside the porch/narthex footprint. | Keep glass zone separate from opaque narthex; clocher remains pinned to the map square. | Keep current |
| `CHURCH` | Church roof/kubbe/clocher are special symbols, not parcel split lines. | Keep one church mass with georeferenced kubbe and clocher. | Keep current |
