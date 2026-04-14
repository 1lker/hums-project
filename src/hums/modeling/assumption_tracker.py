"""PRD-002 · §9 AssumptionTracker — per-field provenance recorder.

Every time the builder falls back to a heritage default (rather than using
an Excel value), it records (field_path, source, note). The tracker is the
single audit trail surfaced in ``assumptions_manifest.md``.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..common.prd import prd


@dataclass
class AssumptionEntry:
    parcel_id: str
    field_path: str        # e.g. "storeys[0].height_m"
    source: str            # "excel" | "assumption:pervititch_1923" | "photo:<id>"
    value: object | None
    note: str | None = None


@prd("002", "§9 AssumptionTracker")
class AssumptionTracker:
    def __init__(self) -> None:
        self._entries: list[AssumptionEntry] = []

    def record(self, parcel_id: str, field_path: str, source: str, value, note: str | None = None) -> object:
        self._entries.append(AssumptionEntry(parcel_id, field_path, source, value, note))
        return value

    def assume(self, parcel_id: str, field_path: str, value, note: str | None = None):
        return self.record(parcel_id, field_path, "assumption:pervititch_1923", value, note)

    def excel(self, parcel_id: str, field_path: str, value):
        return self.record(parcel_id, field_path, "excel", value)

    @property
    def entries(self) -> list[AssumptionEntry]:
        return list(self._entries)

    def per_parcel(self) -> dict[str, list[AssumptionEntry]]:
        grouped: dict[str, list[AssumptionEntry]] = {}
        for e in self._entries:
            grouped.setdefault(e.parcel_id, []).append(e)
        return grouped
