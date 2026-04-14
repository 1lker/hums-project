"""PRD-001 · Data Foundation §4 — Doors & Windows sheet."""
from __future__ import annotations
from typing import Any

from .base_sheet_parser import BaseSheetParser
from ...common.prd import prd


@prd("001", "§4 parcels.json.openings")
class DoorsParser(BaseSheetParser):
    def extract(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "parcel_id": str(row["ID"]).strip(),
            "primary_door_face": row.get("Primary Door Face"),
            "primary_door_type": row.get("Primary Door Type"),
            "secondary_door_face": row.get("Secondary Door Face"),
            "secondary_door_type": row.get("Secondary Door Type"),
            "shared_entrance_with": row.get("Shared Entrance With"),
            "arrow_type": row.get("Arrow Type on Map"),
            "x_mark_observed": self.yes_no(row.get("× Mark Observed")),
            "x_mark_interpretation": row.get("× Mark Interpretation"),
            "line_type_gf": row.get("Line Type (Ground Floor)"),
            "wall_opening_type": row.get("Wall Opening Type"),
            "bim_notes": row.get("BIM Door/ Window Notes") or row.get("BIM Door/Window Notes"),
        }
