"""PRD-002 revision — infer ``structure_type`` from Excel metadata.

Rules (applied in order):
1. Explicit override via the Excel zone string (e.g. "street furniture").
2. "low monumental" storey description → monument.
3. Parcel id convention (future-proof hooks for INT-*, church parts).
4. Otherwise → building (default for 99% of parcels).
"""
from __future__ import annotations

from ..common.prd import prd
from .building import StructureType


@prd("002", "StructureClassifier")
class StructureClassifier:
    def classify(self, parcel: dict, filename_override: str | None = None) -> tuple[StructureType, dict]:
        notes: dict[str, object] = {}
        zone = (parcel.get("zone") or "").lower()
        storeys_raw = ((parcel.get("storeys") or {}).get("raw") or "").lower()
        pid = parcel.get("parcel_id", "")

        if "street furniture" in zone or "low monumental" in storeys_raw:
            return "fountain", notes

        # NB: "clocher" as a substring is ambiguous — Excel uses "S of Clocher"
        # as a position reference for INT-S1/S2 which are buildings, not
        # bell towers. Only match explicit "bell_tower" / "= clocher" labels.
        if "bell_tower" in zone or zone.strip().startswith("clocher"):
            return "bell_tower", notes

        # Flag combined camli+clocher polygon: W-39/1 carries the bell tower
        # until PRD-004 models the church precisely.
        if pid == "W-39/1" and filename_override and "clocher" in filename_override.lower():
            notes["contains_clocher"] = True

        return "building", notes
