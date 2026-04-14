"""PRD-001 · Data Foundation §4 — Facade that joins all Excel sheets.

Facade pattern: hides the per-sheet parsers behind a single `build()` call
that returns a list of parcels conforming to PRD-001 §4.
"""
from __future__ import annotations
import json
from pathlib import Path

import openpyxl

from ...common.paths import EXCEL_REGISTER, PARCELS_JSON, ensure_parsed_dir
from ...common.prd import prd
from .register_parser import RegisterParser
from .roof_parser import RoofParser
from .doors_parser import DoorsParser
from .walls_parser import WallsParser


@prd("001", "§6 step 1 · Facade")
class RegisterAssembler:
    """Reads the workbook once, dispatches to sheet parsers, joins on parcel_id."""

    SHEETS = {
        "register": ("Building Register", RegisterParser),
        "roof": ("Roof Analysis", RoofParser),
        "doors": ("Doors & Windows", DoorsParser),
        "walls": ("Line Type & Wall Analysis", WallsParser),
    }

    def __init__(self, xlsx_path: Path = EXCEL_REGISTER) -> None:
        self._xlsx_path = xlsx_path

    def build(self) -> list[dict]:
        wb = openpyxl.load_workbook(self._xlsx_path, data_only=True)
        register_rows = self._run(wb, "register")
        roof_idx = self._index(self._run(wb, "roof"))
        doors_idx = self._index(self._run(wb, "doors"))
        walls_idx = self._index(self._run(wb, "walls"))

        merged = []
        for row in register_rows:
            pid = row["parcel_id"]
            merged.append({
                **row,
                "roof": _without_id(roof_idx.get(pid, {})),
                "openings": _without_id(doors_idx.get(pid, {})),
                "walls_analysis": _without_id(walls_idx.get(pid, {})),
            })
        return merged

    def build_and_persist(self) -> list[dict]:
        data = self.build()
        ensure_parsed_dir()
        PARCELS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return data

    def _run(self, wb, key: str):
        sheet_name, parser_cls = self.SHEETS[key]
        return parser_cls(wb[sheet_name]).parse()

    @staticmethod
    def _index(rows):
        """Index by normalized parcel_id: strip `/(xx)` compound-parcel suffix.

        Sheets are inconsistent — Register uses bare `N-40` while the Roof sheet
        uses `N-40/(98)` for the same bakery.
        """
        import re
        idx: dict[str, dict] = {}
        for r in rows:
            key = re.sub(r"/\(.+\)$", "", str(r["parcel_id"]).strip())
            idx.setdefault(key, r)
        return idx


def _without_id(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "parcel_id"}
