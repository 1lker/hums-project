"""PRD-001 · Data Foundation §6 step 1 — Template Method for Excel sheets.

All Pervititch sheets share the same shape: a header row somewhere in the
first handful of rows, then N parcel rows interspersed with section-divider
rows. Subclasses only override `extract(row_dict)`.
"""
from __future__ import annotations
import re
from abc import ABC, abstractmethod
from typing import Any

from openpyxl.worksheet.worksheet import Worksheet

from ...common.prd import prd

_PARCEL_ID_RE = re.compile(r"^(?:[NSEW]-|INT-|C-)")


@prd("001", "§6 step 1")
class BaseSheetParser(ABC):
    """Template Method: find header → iterate rows → extract()."""

    header_probe_col: str = "ID"

    def __init__(self, worksheet: Worksheet) -> None:
        self._ws = worksheet
        self._headers: list[str] | None = None
        self._header_row_idx: int | None = None

    def parse(self) -> list[dict[str, Any]]:
        self._locate_header()
        assert self._header_row_idx is not None and self._headers is not None
        rows: list[dict[str, Any]] = []
        for raw in self._ws.iter_rows(min_row=self._header_row_idx + 1, values_only=True):
            row = self._zip_row(raw)
            if self._is_parcel_row(row):
                rows.append(self.extract(row))
        return rows

    def _locate_header(self) -> None:
        for i, row in enumerate(self._ws.iter_rows(values_only=True), start=1):
            if row and any(self._norm_cell(c) == self.header_probe_col for c in row):
                self._header_row_idx = i
                self._headers = [self._norm_cell(c) or f"col_{j}" for j, c in enumerate(row)]
                return
        raise RuntimeError(f"Header row not found in {self._ws.title!r}")

    def _zip_row(self, raw: tuple) -> dict[str, Any]:
        assert self._headers is not None
        return {h: v for h, v in zip(self._headers, raw) if h}

    @staticmethod
    def _norm_cell(c: Any) -> str:
        """Normalize header cell: strip and replace embedded newlines with spaces."""
        if c is None:
            return ""
        return " ".join(str(c).split())

    @staticmethod
    def _is_parcel_row(row: dict[str, Any]) -> bool:
        pid = row.get("ID")
        if not pid:
            return False
        return bool(_PARCEL_ID_RE.match(str(pid).strip()))

    @abstractmethod
    def extract(self, row: dict[str, Any]) -> dict[str, Any]:
        """Return a flat dict keyed by semantic name (not column title)."""

    # ---- shared coercions ----
    @staticmethod
    def yes_no(v: Any) -> bool | None:
        """Coerce cell to bool. Excel sheets often have 'YES (reason...)' prose,
        so we match on leading token rather than exact equality.
        """
        if v is None:
            return None
        s = str(v).strip().upper()
        if not s:
            return None
        head = s.split()[0].rstrip(":,;.")
        if head in {"YES", "Y", "TRUE", "✓"}:
            return True
        if head in {"NO", "N", "FALSE", "—", "-"}:
            return False
        return None
