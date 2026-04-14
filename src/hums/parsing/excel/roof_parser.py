"""PRD-001 · Data Foundation §4 — Roof Analysis sheet."""
from __future__ import annotations
from typing import Any

from .base_sheet_parser import BaseSheetParser
from ...common.prd import prd


@prd("001", "§4 parcels.json.roof")
class RoofParser(BaseSheetParser):
    def extract(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "parcel_id": str(row["ID"]).strip(),
            "shape": row.get("Roof Shape"),
            "material_code": row.get("Roof Material (Code)"),
            "material_decoded": row.get("Roof Material (Decoded)"),
            "slope_direction": row.get("Slope Direction (from map markers)"),
            "structure": row.get("Roof Structure (inferred)"),
            "special_features": row.get("Special Roof Features"),
            "has_chimney": self.yes_no(row.get("Chimney Marker")),
            "has_skylight": self.yes_no(row.get("Skylight/ Tabatière") or row.get("Skylight/Tabatière")),
            "bim_family": row.get("Roof BIM Family"),
            "notes": row.get("Notes"),
        }
