"""PRD-002 · §5 / §11b — intermediate LOD3 domain model.

Geometry-ready representation; no meshes yet (that's PRD-003).
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Literal

from ..common.prd import prd

RGB = tuple[int, int, int]
Point = tuple[float, float]
FootprintSource = Literal["traced", "inferred", "stub", "missing", "absorbed"]
Face = Literal["N", "E", "S", "W", "INT"]
StructureType = Literal["building", "fountain", "bell_tower", "monument"]


@dataclass
class LocalFrame:
    origin_utm: Point                # (easting, northing) EPSG:32635
    street_rotation_deg: float       # rotation applied so longest street edge is +X


@dataclass
class Opening:
    kind: Literal["door", "shop_window", "window"]
    storey_level: int
    position_along_wall_m: float
    width_m: float
    height_m: float
    sill_m: float
    style: Literal["rectangular", "arched", "ogee", "bay", "oriel"] = "rectangular"
    pane_layout: str | None = None
    has_shutters: bool = False
    has_balcony: bool = False
    frame_profile: Literal["flat", "moulded", "cornice"] | None = "flat"
    color_source: str = "assumption:pervititch_1923"


@dataclass
class WallSegment:
    start: Point                     # local frame
    end: Point
    thickness_m: float
    face: Face
    is_street_facing: bool
    is_party_wall: bool = False      # shared with a neighbour — no openings
    adjacent_height_m: float | None = None  # if party wall, neighbour's total above-grade height
    hatch_pattern: str | None = None
    openings: list[Opening] = field(default_factory=list)

    @property
    def length_m(self) -> float:
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return (dx * dx + dy * dy) ** 0.5


@dataclass
class Storey:
    level: int                       # 0 = ground
    height_m: float
    is_mezzanine: bool = False
    is_basement: bool = False
    use: str | None = None           # "shop" | "residential" | "bakery" | ...


@dataclass
class RoofDescriptor:
    shape: Literal["gable", "hip", "mansard", "flat", "complex_pitched", "vault_flat"]
    material: Literal["tile_TR", "tile_TF", "sheet_metal_T", "vault_VF", "vault_VT", "glass_roof", "unknown"]
    pitch_deg: float
    slope_direction: str | None
    has_chimney: bool = False
    has_skylight: bool = False
    ridge_axis_hint: Literal["along_street", "perpendicular", None] | None = None


@dataclass
class FacadePalette:
    wall_main: RGB
    trim: RGB
    roof: RGB
    wall_accent: RGB | None = None
    shutters: RGB | None = None
    gf_shopfront: RGB | None = None
    source: str = "period_default"


@dataclass
class ReferenceImage:
    image_id: str
    path: str
    facade: Literal["N", "E", "S", "W", "aerial", "interior"]
    source_url: str | None = None
    captured_date: str | None = None
    aligned: bool = False
    notes: str | None = None


@dataclass
class Provenance:
    footprint_source_file: str | None = None
    attribute_sources: dict[str, str] = field(default_factory=dict)


@prd("002", "§5 Building")
@dataclass
class Building:
    parcel_id: str
    material_class: str | None                # "A" | "B" | "C"
    footprint_source: FootprintSource
    local_frame: LocalFrame | None
    structure_type: StructureType = "building"
    notes: dict[str, Any] = field(default_factory=dict)   # e.g. {"contains_clocher": True}
    footprint_local: list[Point] = field(default_factory=list)
    storeys: list[Storey] = field(default_factory=list)
    wall_segments: list[WallSegment] = field(default_factory=list)
    roof: RoofDescriptor | None = None
    facade_palette: FacadePalette | None = None
    reference_imagery: list[ReferenceImage] = field(default_factory=list)
    shared_footprint_group_id: str | None = None
    parent_parcel_id: str | None = None       # e.g. INT-N2 attached to N-44
    provenance: Provenance = field(default_factory=Provenance)
    # carry-through from PRD-001 for inspection
    excel_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
