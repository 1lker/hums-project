"""PRD-001 · Data Foundation — domain models.

Dataclasses mirror the JSON schema documented in PRD-001 §4. Keeping them in
one place means downstream PRDs (LOD3 generator, renderer) import from here
instead of re-deriving the shape from JSON.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class Material:
    class_: str | None = None
    decoded: str | None = None           # "Masonry" | "Wooden"
    map_colour: str | None = None
    raw_material_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"class": self.class_, "decoded": self.decoded,
                "map_colour": self.map_colour, "raw_material_label": self.raw_material_label}


@dataclass
class Wall:
    code: str | None = None
    decoded: str | None = None
    thickness_raw: str | None = None
    thickness_m: float | None = None


@dataclass
class Vault:
    code: str | None = None              # VF | VT | Tt | etc.
    decoded: str | None = None


@dataclass
class GroundFloor:
    use: str | None = None
    code: str | None = None              # Mg. | Bs. | etc.


@dataclass
class Storeys:
    raw: str | None = None
    count: int | None = None
    has_mezzanine: bool = False
    is_basement_level: bool = False


@dataclass
class Roof:
    shape: str | None = None
    material_code: str | None = None
    material_decoded: str | None = None
    slope_direction: str | None = None
    structure: str | None = None
    special_features: str | None = None
    has_chimney: bool | None = None
    has_skylight: bool | None = None
    bim_family: str | None = None
    notes: str | None = None


@dataclass
class Openings:
    primary_door_face: str | None = None
    primary_door_type: str | None = None
    secondary_door_face: str | None = None
    secondary_door_type: str | None = None
    shared_entrance_with: str | None = None
    arrow_type: str | None = None
    x_mark_observed: bool | None = None
    x_mark_interpretation: str | None = None
    line_type_gf: str | None = None
    wall_opening_type: str | None = None
    bim_notes: str | None = None


@dataclass
class WallsAnalysis:
    gf_line_type: str | None = None
    upper_line_type: str | None = None
    special_feature: str | None = None
    feature_meaning: str | None = None
    hatch_pattern: str | None = None
    hatch_meaning: str | None = None
    opening_gaps: str | None = None
    opening_location: str | None = None
    bim_notes: str | None = None


@dataclass
class Parcel:
    parcel_id: str
    parcel_number: str | None = None
    sub: str | None = None
    zone: str | None = None
    street_facing: str | None = None
    material: Material = field(default_factory=Material)
    wall: Wall = field(default_factory=Wall)
    vault: Vault = field(default_factory=Vault)
    ground_floor: GroundFloor = field(default_factory=GroundFloor)
    storeys: Storeys = field(default_factory=Storeys)
    basement: str | None = None
    condition: str | None = None
    change_v2: str | None = None
    bim_notes: str | None = None
    roof: Roof = field(default_factory=Roof)
    openings: Openings = field(default_factory=Openings)
    walls_analysis: WallsAnalysis = field(default_factory=WallsAnalysis)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # repair reserved-word rename
        d["material"]["class"] = d["material"].pop("class_")
        return d
