"""PRD-001 · Data Foundation §4 — Building Register sheet."""
from __future__ import annotations
import re
from typing import Any

from .base_sheet_parser import BaseSheetParser
from ...common.prd import prd

_STOREY_RE = re.compile(r"(?:Δ|\b)(\d+)(½|b)?")


@prd("001", "§4 parcels.json")
class RegisterParser(BaseSheetParser):
    def extract(self, row: dict[str, Any]) -> dict[str, Any]:
        pid = str(row["ID"]).strip()
        return {
            "parcel_id": pid,
            "parcel_number": _clean(row.get("Parcel")),
            "sub": _clean(row.get("Sub")),
            "zone": row.get("Zone"),
            "street_facing": row.get("Street Facing"),
            "material": self._material(row),
            "wall": {
                "code": row.get("Wall Code"),
                "decoded": row.get("Wall Decoded"),
                "thickness_raw": row.get("Wall Thick (Ep)"),
                "thickness_m": None,
            },
            "vault": {"code": row.get("Vault/Ceil Code"), "decoded": row.get("Vault/Ceil Decoded")},
            "ground_floor": {"use": row.get("GF Use"), "code": row.get("GF Code")},
            "storeys": self._storeys(row.get("Storeys (Δ)")),
            "basement": row.get("Basement"),
            "condition": row.get("Condition"),
            "change_v2": row.get("Change v2?"),
            "bim_notes": row.get("BIM Notes"),
        }

    @staticmethod
    def _material(row: dict[str, Any]) -> dict[str, Any]:
        colour = (str(row.get("Map Colour")) if row.get("Map Colour") else "").upper()
        mat_raw = str(row.get("Material (Corrected)") or "").upper()
        decoded = None
        if "PINK" in colour or "MASONRY" in mat_raw:
            decoded = "Masonry"
        elif "YELLOW" in colour or "WOODEN" in mat_raw:
            decoded = "Wooden"
        return {
            "class": _clean(row.get("Class")),
            "decoded": decoded,
            "map_colour": colour or None,
            "raw_material_label": _clean(row.get("Material (Corrected)")),
        }

    @staticmethod
    def _storeys(raw: Any) -> dict[str, Any]:
        if raw is None:
            return {"raw": None, "count": None, "has_mezzanine": False, "is_basement_level": False}
        s = str(raw)
        m = _STOREY_RE.search(s)
        if not m:
            return {"raw": s, "count": None, "has_mezzanine": "½" in s, "is_basement_level": "b" in s.lower()}
        return {
            "raw": s,
            "count": int(m.group(1)),
            "has_mezzanine": m.group(2) == "½",
            "is_basement_level": m.group(2) == "b",
        }


def _clean(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None
