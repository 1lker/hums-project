"""PRD-003 · §6.2 — complex pitched roof fallback.

First-pass strategy: treat the footprint as a hip roof (works for most
irregular plans at LOD3). Convex decomposition + per-sub-region hip is
deferred to a later iteration — hip already produces a plausible shape for
N-40's L-shape bakery.
"""
from __future__ import annotations

from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh
from .base import RoofGenerator
from .hip import HipRoof


@prd("003", "§6.2 ComplexPitchedRoof")
class ComplexPitchedRoof(RoofGenerator):
    def __init__(self) -> None:
        self._delegate = HipRoof()

    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        self._delegate.generate(mesh, building, eaves_z)
