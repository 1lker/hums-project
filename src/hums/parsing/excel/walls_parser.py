"""PRD-001 · Data Foundation §4 — Line Type & Wall Analysis sheet."""
from __future__ import annotations
from typing import Any

from .base_sheet_parser import BaseSheetParser
from ...common.prd import prd


@prd("001", "§4 parcels.json.walls_analysis")
class WallsParser(BaseSheetParser):
    def extract(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "parcel_id": str(row["ID"]).strip(),
            "gf_line_type": row.get("GF Wall Line Type"),
            "upper_line_type": row.get("Upper Floor Line Type"),
            "special_feature": row.get("Special Line Feature"),
            "feature_meaning": row.get("Line Feature Meaning"),
            "hatch_pattern": row.get("Hatch Pattern"),
            "hatch_meaning": row.get("Hatch Meaning"),
            "opening_gaps": row.get("Wall Opening (gaps in line)"),
            "opening_location": row.get("Opening Location"),
            "bim_notes": row.get("BIM Wall Notes"),
        }
