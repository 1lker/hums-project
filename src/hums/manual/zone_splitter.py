"""PRD-005 · Split a footprint polygon into sub-polygons along an axis."""
from __future__ import annotations
import math

from shapely.geometry import Polygon, box
from shapely import affinity

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
    if axis.startswith("long_axis_"):
        return _split_along_long_axis(poly, axis.removeprefix("long_axis_"), frac_range)

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


def _split_along_long_axis(poly: Polygon, axis: str, frac_range: tuple[float, float]) -> Polygon:
    """Split along the footprint's own long direction instead of global UTM axes.

    This is for hand-audited Pervititch rows where the map's black internal
    division lines cut a tilted rectangular building into storey zones.
    """
    angle = _long_axis_angle_deg(poly)
    # Rotate long axis onto +Y, so the existing north/south fraction logic
    # cuts bands perpendicular to the mapped long building direction.
    rotated = affinity.rotate(poly, 90.0 - angle, origin="centroid", use_radians=False)
    clipped = split_zone(rotated, axis, frac_range)
    return affinity.rotate(clipped, angle - 90.0, origin=rotated.centroid, use_radians=False)


def _long_axis_angle_deg(poly: Polygon) -> float:
    rect = poly.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)
    if coords and coords[0] == coords[-1]:
        coords = coords[:-1]
    best = ((1.0, 0.0), 0.0)
    for i in range(len(coords)):
        a = coords[i]
        b = coords[(i + 1) % len(coords)]
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        length = math.hypot(dx, dy)
        if length > best[1]:
            best = ((dx, dy), length)
    dx, dy = best[0]
    return math.degrees(math.atan2(dy, dx))
