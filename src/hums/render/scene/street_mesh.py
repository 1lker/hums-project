"""PRD-004 · Track A — street mesh with curbs surrounding the block.

Emits:
  * a cobble-grey street plane extending ``STREET_WIDTH`` beyond the block
    outline in all directions,
  * a raised sidewalk ring hugging the block footprint (0.15 m tall, 2 m wide).

Consumed by the glTF backend via ``SceneGraph.ground`` replacement and extra
quads emitted at scene root.
"""
from __future__ import annotations
import json

from shapely.geometry import shape

from ...common.paths import BLOCK_GEOJSON
from ...common.prd import prd


STREET_HALF_EXTENT = 45.0
SIDEWALK_WIDTH = 2.0
SIDEWALK_HEIGHT = 0.15


@prd("004", "StreetMesh")
def load_block_ring_local(block_centroid_utm: tuple[float, float]) -> list[tuple[float, float]] | None:
    if not BLOCK_GEOJSON.exists():
        return None
    feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
    if not feats:
        return None
    poly = shape(feats[0]["geometry"])
    cx, cy = block_centroid_utm
    return [(x - cx, y - cy) for (x, y) in list(poly.exterior.coords)[:-1]]
