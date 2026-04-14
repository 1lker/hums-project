"""PRD-001 · Data Foundation §5 — classify footprint files by filename.

One class per classification rule keeps the decision table readable and
extensible for PRD-002+ as new artefact types arrive.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from enum import Enum

from ...common.paths import FILENAME_OVERRIDES
from ...common.prd import prd


class FootprintKind(str, Enum):
    PARCEL = "parcel"
    BLOCK_OUTLINE = "block_outline"
    CHURCH = "church"
    FOUNTAIN = "fountain"
    MAGAZINE = "magazine"
    OTHER_NON_PARCEL = "other_non_parcel"


@dataclass
class Classification:
    kind: FootprintKind
    parcel_numbers: list[str] | None = None  # normalized (leading zeros stripped)
    parcel_ids_override: list[str] | None = None  # from filename_overrides.json


_NON_PARCEL_KINDS = [
    (FootprintKind.CHURCH, ("church", "kilise", "kubbe", "clocher")),
    (FootprintKind.FOUNTAIN, ("fountain", "cesme")),
    (FootprintKind.MAGAZINE, ("magazine",)),
]


@prd("001", "§5 ID normalization")
class FilenameClassifier:
    _ENTRANCE_RE = re.compile(r"building[-]?entrence[-]?", re.I)

    def __init__(self) -> None:
        self._overrides = self._load_overrides()

    def classify(self, basename: str) -> Classification:
        b = basename.lower()

        if "blobk-147" in b or "block-147-layer" in b:
            return Classification(FootprintKind.BLOCK_OUTLINE)

        # Manual override wins over every heuristic below.
        override_ids = self._overrides.get(basename) or self._overrides.get(b)
        if override_ids:
            return Classification(FootprintKind.PARCEL, parcel_ids_override=override_ids)

        for kind, hints in _NON_PARCEL_KINDS:
            if any(h in b for h in hints):
                return Classification(kind)

        nums = self._extract_nums(basename)
        if nums:
            return Classification(FootprintKind.PARCEL, parcel_numbers=nums)

        return Classification(FootprintKind.OTHER_NON_PARCEL)

    @staticmethod
    def _load_overrides() -> dict[str, list[str]]:
        if not FILENAME_OVERRIDES.exists():
            return {}
        raw = json.loads(FILENAME_OVERRIDES.read_text())
        out: dict[str, list[str]] = {}
        for k, v in raw.items():
            if k.startswith("_") or not isinstance(v, list):
                continue
            out[k] = list(v)
            out[k.lower()] = list(v)
        return out

    def _extract_nums(self, basename: str) -> list[str]:
        b = self._ENTRANCE_RE.sub("", basename.lower())
        b = re.sub(r"[^0-9\-]", "-", b)
        return [str(int(n)) for n in b.split("-") if n.isdigit()]
