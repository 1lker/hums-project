"""PRD-003 · §6.2 — roof generator Strategy ABC."""
from __future__ import annotations
from abc import ABC, abstractmethod

from ....common.prd import prd
from ....modeling.building import Building
from ...mesh_graph import BuildingMesh


@prd("003", "§6.2 RoofGenerator")
class RoofGenerator(ABC):
    @abstractmethod
    def generate(self, mesh: BuildingMesh, building: Building, eaves_z: float) -> None:
        ...

    @staticmethod
    def total_wall_height(building: Building) -> float:
        return sum(s.height_m for s in building.storeys if not s.is_basement)

    @staticmethod
    def material_key(building: Building) -> str:
        material = (building.roof.material if building.roof else "") or ""
        if material == "sheet_metal_T":
            return "sheet_metal_grey"
        if material in {"tile_TR"}:
            return "tile_terracotta"
        return "roof"
