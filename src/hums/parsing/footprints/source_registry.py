"""PRD-001 · Data Foundation §6 step 2 — source file discovery + dedup.

Groups *.shp and *.kml that describe the same feature under a single
normalized key. SHP wins when both exist (authored source beats export).
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

from ...common.prd import prd


@dataclass
class FootprintSource:
    key: str          # normalized basename (stripped hyphens, lowercase)
    display_name: str # original stem preserved for reports
    shp: Path | None
    kml: Path | None

    @property
    def primary(self) -> Path:
        assert self.shp or self.kml
        return self.shp or self.kml  # type: ignore[return-value]

    @property
    def primary_format(self) -> str:
        return "shp" if self.shp else "kml"


@prd("001", "§6 step 2 · dedup")
class SourceRegistry:
    def __init__(self, root: Path) -> None:
        self._root = root

    def discover(self) -> list[FootprintSource]:
        buckets: dict[str, dict] = {}
        for path in self._root.rglob("*.shp"):
            buckets.setdefault(self._norm(path.stem), {"stem": path.stem})["shp"] = path
        for path in self._root.rglob("*.kml"):
            buckets.setdefault(self._norm(path.stem), {"stem": path.stem})["kml"] = path
        return [
            FootprintSource(key=k, display_name=b["stem"], shp=b.get("shp"), kml=b.get("kml"))
            for k, b in sorted(buckets.items())
        ]

    @staticmethod
    def _norm(stem: str) -> str:
        return re.sub(r"[^a-z0-9]", "", stem.lower())
