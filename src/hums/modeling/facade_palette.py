"""PRD-002 · §11b — period-default facade palette lookup.

Photo-sourced overrides land here in PRD-005.
"""
from __future__ import annotations

from ..common.prd import prd
from ..common.heritage_profile import PROFILE
from .building import FacadePalette
from .assumption_tracker import AssumptionTracker


@prd("002", "§11b FacadePaletteBuilder")
class FacadePaletteBuilder:
    def build(self, material_class: str | None, gf_is_shop: bool,
              parcel_id: str, tracker: AssumptionTracker) -> FacadePalette:
        p = PROFILE.palette
        cls = (material_class or "").upper()

        if "GLASS" in cls:
            wall, accent, trim, shutters, roof = (
                (132, 174, 190), (92, 118, 130), (68, 74, 72), (0, 0, 0), (112, 128, 136)
            )
            shopfront = None
        elif cls.startswith("A"):
            wall, accent, trim, shutters, roof = p.masonry_A
            shopfront = p.masonry_B_shop_gf if gf_is_shop else None
        elif cls.startswith("B"):
            wall, accent, trim, shutters, roof = p.masonry_B
            shopfront = p.masonry_B_shop_gf if gf_is_shop else None
        elif cls.startswith("C"):
            wall, accent, trim, shutters, roof = p.wooden_C
            shopfront = None
        else:
            wall, accent, trim, shutters, roof = p.masonry_B
            shopfront = None
            tracker.assume(parcel_id, "facade_palette.material_class", "unknown", "No class in Excel; fell back to Masonry B")

        palette = FacadePalette(
            wall_main=wall, wall_accent=accent, trim=trim,
            shutters=shutters, roof=roof, gf_shopfront=shopfront,
            source="period_default",
        )
        tracker.assume(parcel_id, "facade_palette", "period_default")
        return palette
