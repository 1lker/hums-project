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
    parent_parcel_id: str | None = None       # annex attached to this parcel


_NON_PARCEL_KINDS = [
    (FootprintKind.CHURCH, ("church", "kilise", "kubbe", "clocher")),
    (FootprintKind.FOUNTAIN, ("fountain", "cesme")),
    (FootprintKind.MAGAZINE, ("magazine",)),
]


@prd("001", "§5 ID normalization")
class FilenameClassifier:
    _ENTRANCE_RE = re.compile(r"building[-]?entrence[-]?", re.I)

    def __init__(self) -> None:
        self._overrides, self._overrides_parent = self._load_overrides()

    def classify(self, basename: str) -> Classification:
        b = basename.lower()

        # Loosened to recognise new filenames like blobk147layer-main.kml
        # (no hyphens between `blobk`/`147`/`layer`).
        if any(tag in b for tag in ("blobk-147", "block-147-layer", "blobk147layer", "block147layer")):
            return Classification(FootprintKind.BLOCK_OUTLINE)

        # Manual override wins over every heuristic below.
        if basename in self._overrides or b in self._overrides:
            override_ids = self._overrides.get(basename) or self._overrides.get(b)
            parent = self._overrides_parent.get(basename) or self._overrides_parent.get(b)
            if override_ids:
                return Classification(
                    FootprintKind.PARCEL,
                    parcel_ids_override=override_ids,
                    parent_parcel_id=parent,
                )
            # Empty override list → explicit "ignore this file".
            return Classification(FootprintKind.OTHER_NON_PARCEL)

        for kind, hints in _NON_PARCEL_KINDS:
            if any(h in b for h in hints):
                return Classification(kind)

        nums = self._extract_nums(basename)
        if nums:
            return Classification(FootprintKind.PARCEL, parcel_numbers=nums)

        return Classification(FootprintKind.OTHER_NON_PARCEL)

    @staticmethod
    def _load_overrides() -> tuple[dict[str, list[str]], dict[str, str]]:
        """Return (parcel_id map, parent_parcel_id map).

        Syntax in filename_overrides.json:
            "<stem>": ["INT-N2"]                       # map file to parcel
            "<stem>__parent": "N-44"                    # annex parent link
        """
        if not FILENAME_OVERRIDES.exists():
            return {}, {}
        raw = json.loads(FILENAME_OVERRIDES.read_text())
        out: dict[str, list[str]] = {}
        parents: dict[str, str] = {}
        for k, v in raw.items():
            if k.startswith("_"):
                continue
            if k.endswith("__parent") and isinstance(v, str):
                base = k[: -len("__parent")]
                parents[base] = v
                parents[base.lower()] = v
                continue
            if not isinstance(v, list):
                continue
            out[k] = list(v)
            out[k.lower()] = list(v)
        return out, parents

    def _extract_nums(self, basename: str) -> list[str]:
        b = self._ENTRANCE_RE.sub("", basename.lower())
        b = re.sub(r"[^0-9\-]", "-", b)
        return [str(int(n)) for n in b.split("-") if n.isdigit()]
