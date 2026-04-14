"""PRD-001 · Data Foundation §4 — CRS handling.

Wraps pyproj so call sites don't repeat transformer construction. Kadıköy
(~29°E) falls in UTM Zone 35N; EPSG:32635 is the metric CRS we pin for the
entire project.
"""
from __future__ import annotations
from pyproj import Transformer

from ..common.prd import prd

WGS84 = "EPSG:4326"
UTM_35N = "EPSG:32635"


@prd("001", "§4 EPSG:32635")
class CrsTransformer:
    def __init__(self, source: str = WGS84, target: str = UTM_35N) -> None:
        self._t = Transformer.from_crs(source, target, always_xy=True)
        self.target = target

    def points(self, lonlat: list[tuple[float, float]]) -> list[tuple[float, float]]:
        xs, ys = self._t.transform([p[0] for p in lonlat], [p[1] for p in lonlat])
        return list(zip(xs, ys))
