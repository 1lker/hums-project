"""PRD-005 · Split a footprint polygon into sub-polygons along an axis."""
from __future__ import annotations

from shapely.geometry import Polygon, box

from ..common.prd import prd


@prd("005", "ZoneSplitter")
def split_zone(poly: Polygon, axis: str, frac_range: tuple[float, float]) -> Polygon:
    """Cut ``poly`` between ``frac_range[0]`` and ``frac_range[1]`` along axis.

    Axis values:
      ``north_to_south`` — f=0 at the NORTH edge (max Y), f=1 at the SOUTH (min Y).
      ``south_to_north`` — reverse.
      ``west_to_east``   — f=0 at the WEST edge (min X), f=1 at the EAST (max X).
      ``east_to_west``   — reverse.
    """
    minx, miny, maxx, maxy = poly.bounds
    f0, f1 = frac_range
    if f0 > f1:
        f0, f1 = f1, f0

    if axis == "north_to_south":
        y_top = maxy - f0 * (maxy - miny)
        y_bot = maxy - f1 * (maxy - miny)
        cutter = box(minx - 1, y_bot, maxx + 1, y_top)
    elif axis == "south_to_north":
        y_bot = miny + f0 * (maxy - miny)
        y_top = miny + f1 * (maxy - miny)
        cutter = box(minx - 1, y_bot, maxx + 1, y_top)
    elif axis == "west_to_east":
        x_left = minx + f0 * (maxx - minx)
        x_right = minx + f1 * (maxx - minx)
        cutter = box(x_left, miny - 1, x_right, maxy + 1)
    elif axis == "east_to_west":
        x_left = maxx - f1 * (maxx - minx)
        x_right = maxx - f0 * (maxx - minx)
        cutter = box(x_left, miny - 1, x_right, maxy + 1)
    else:
        raise ValueError(f"unknown axis {axis!r}")

    clipped = poly.intersection(cutter)
    if clipped.is_empty:
        return clipped
    if clipped.geom_type == "Polygon":
        return clipped
    if hasattr(clipped, "geoms"):
        # pick the largest piece
        return max(clipped.geoms, key=lambda g: g.area)
    return clipped
