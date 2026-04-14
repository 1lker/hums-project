"""PRD-002 · §4 Heritage Assumption Profile.

Frozen table of period-standard defaults for 1923 Kadıköy Pervititch block.
Every default applied is recorded via ``AssumptionTracker`` with source tag
``assumption:pervititch_1923`` so assumptions never masquerade as survey data.
"""
from __future__ import annotations
from dataclasses import dataclass

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class StoreyHeights:
    ground_shop_m: float = 3.8
    upper_residential_m: float = 3.2
    mezzanine_m: float = 2.2
    basement_m: float = 2.4
    parapet_m: float = 0.60
    floor_slab_m: float = 0.25


@dataclass(frozen=True)
class WallThickness:
    masonry_m: float = 0.55   # Class A/B
    wooden_m: float = 0.20    # Class C


@dataclass(frozen=True)
class RoofPitches:
    tile_TR_deg: float = 30.0
    sheet_metal_T_deg: float = 20.0
    vault_flat_deg: float = 2.86   # ~5% slope


@dataclass(frozen=True)
class OpeningSizes:
    door_w_m: float = 1.0
    door_h_m: float = 2.2
    shop_window_w_m: float = 1.8
    shop_window_h_m: float = 2.4
    shop_window_sill_m: float = 0.4
    upper_window_w_m: float = 1.0
    upper_window_h_m: float = 1.6
    upper_window_sill_m: float = 0.9
    upper_window_spacing_m: float = 2.5   # target spacing centre-to-centre


@dataclass(frozen=True)
class FacadePaletteDefaults:
    # (main, accent, trim, shutters, roof) per material class
    masonry_A: tuple[RGB, RGB, RGB, RGB, RGB] = (
        (201, 183, 156), (176, 155, 122), (110, 90, 62),  (70, 50, 35),  (142, 74, 50))
    masonry_B: tuple[RGB, RGB, RGB, RGB, RGB] = (
        (224, 201, 174), (201, 170, 140), (90, 74, 58),   (60, 45, 30),  (142, 74, 50))
    masonry_B_shop_gf: RGB = (181, 83, 60)  # Kadıköy shop red
    wooden_C: tuple[RGB, RGB, RGB, RGB, RGB] = (
        (210, 184, 119), (180, 150, 95),  (61, 42, 26),   (40, 30, 20),  (78, 82, 86))
    church_stone: tuple[RGB, RGB, RGB, RGB, RGB] = (
        (216, 204, 179), (196, 182, 156), (90, 78, 60),   (0, 0, 0),     (91, 96, 104))


@dataclass(frozen=True)
class HeritageProfile:
    source_tag: str = "assumption:pervititch_1923"
    storeys: StoreyHeights = StoreyHeights()
    walls: WallThickness = WallThickness()
    roofs: RoofPitches = RoofPitches()
    openings: OpeningSizes = OpeningSizes()
    palette: FacadePaletteDefaults = FacadePaletteDefaults()


PROFILE = HeritageProfile()
