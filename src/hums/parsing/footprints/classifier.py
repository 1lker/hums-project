"""PRD-001 · Data Foundation §5 — classify footprint files by filename.

One class per classification rule keeps the decision table readable and
extensible for PRD-002+ as new artefact types arrive.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum

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


_NON_PARCEL_KINDS = [
    (FootprintKind.CHURCH, ("church", "kilise", "kubbe", "clocher")),
    (FootprintKind.FOUNTAIN, ("fountain", "cesme")),
    (FootprintKind.MAGAZINE, ("magazine",)),
]


@prd("001", "§5 ID normalization")
class FilenameClassifier:
    _ENTRANCE_RE = re.compile(r"building[-]?entrence[-]?", re.I)

    def classify(self, basename: str) -> Classification:
        b = basename.lower()

        if "blobk-147" in b or "block-147-layer" in b:
            return Classification(FootprintKind.BLOCK_OUTLINE)

        if "green-area-wooden" in b:
            # Described as "wooden at 147 block near the church middle of the block".
            # Not a parcel; treat as church-precinct feature for now.
            return Classification(FootprintKind.CHURCH)

        for kind, hints in _NON_PARCEL_KINDS:
            if any(h in b for h in hints):
                return Classification(kind)

        nums = self._extract_nums(basename)
        if nums:
            return Classification(FootprintKind.PARCEL, parcel_numbers=nums)

        return Classification(FootprintKind.OTHER_NON_PARCEL)

    def _extract_nums(self, basename: str) -> list[str]:
        b = self._ENTRANCE_RE.sub("", basename.lower())
        b = re.sub(r"[^0-9\-]", "-", b)
        return [str(int(n)) for n in b.split("-") if n.isdigit()]
