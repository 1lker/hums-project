"""PRD-001 · Data Foundation §6 step 2 — footprint readers (Strategy pattern).

Each reader emits a list of lon/lat rings; the rest of the pipeline doesn't
care whether the source was a shapefile or a KML.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from xml.etree import ElementTree as ET

import shapefile  # pyshp

from ...common.prd import prd

Ring = list[tuple[float, float]]


@prd("001", "§6 step 2 · Strategy")
class FootprintReader(ABC):
    @abstractmethod
    def read(self, path: Path) -> list[Ring]:
        ...


class ShapefileReader(FootprintReader):
    def read(self, path: Path) -> list[Ring]:
        rings: list[Ring] = []
        with shapefile.Reader(str(path)) as r:
            for shape in r.shapes():
                if not shape.points:
                    continue
                parts = list(shape.parts) + [len(shape.points)]
                for i in range(len(parts) - 1):
                    ring = shape.points[parts[i]:parts[i + 1]]
                    if len(ring) >= 3:
                        rings.append([(float(x), float(y)) for x, y in ring])
        return rings


class KmlReader(FootprintReader):
    _POLYGON_TAG = "{http://www.opengis.net/kml/2.2}Polygon"
    _OUTER_TAG = "{http://www.opengis.net/kml/2.2}outerBoundaryIs"
    _LINEAR_RING_TAG = "{http://www.opengis.net/kml/2.2}LinearRing"
    _COORDS_TAG = "{http://www.opengis.net/kml/2.2}coordinates"

    def read(self, path: Path) -> list[Ring]:
        rings: list[Ring] = []
        tree = ET.parse(path)
        for polygon in tree.getroot().iter(self._POLYGON_TAG):
            for outer in polygon.iter(self._OUTER_TAG):
                coords = outer.find(f"./{self._LINEAR_RING_TAG}/{self._COORDS_TAG}")
                if coords is None:
                    continue
                pts = self._parse_coordinates(coords.text or "")
                if len(pts) >= 3:
                    rings.append(pts)
        return rings

    @staticmethod
    def _parse_coordinates(text: str) -> Ring:
        pts: Ring = []
        for token in text.strip().split():
            parts = token.split(",")
            if len(parts) >= 2:
                pts.append((float(parts[0]), float(parts[1])))
        return pts
