"""PRD-005 · Manual label dataclasses mirroring `data/manual/schema.md`.

These replace the Excel-derived attributes once a parcel is hand-labelled.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


Face = Literal["N", "E", "S", "W"]
ZoneAxis = Literal["north_to_south", "south_to_north",
                    "west_to_east", "east_to_west"]


@dataclass
class ZoneRoof:
    shape: str
    material: str
    pitch_deg: float
    has_chimney: bool = False
    has_skylight: bool = False


@dataclass
class Zone:
    id: str
    description: str
    material_class: str                       # A | B | C
    map_colour: str                           # yellow | pink
    storeys_above_grade: float
    has_mezzanine: bool
    has_basement: bool
    storey_heights_m: list[float]
    ground_floor_use: str
    roof: ZoneRoof
    footprint_fraction: tuple[float, float]   # [start, end] along primary axis
    map_labels: list[str] = field(default_factory=list)
    clip_ranges: list[tuple[str, tuple[float, float]]] = field(default_factory=list)


@dataclass
class DoorHint:
    face: Face
    zone: str
    description: str | None = None


@dataclass
class EntranceHint:
    face: Face
    zone: str
    count: int = 1
    description: str | None = None


@dataclass
class Facades:
    street_facing_faces: list[Face]
    opaque_faces: list[Face] = field(default_factory=list)
    primary_door: DoorHint | None = None
    secondary_door: DoorHint | None = None
    entrance_hints: list[EntranceHint] = field(default_factory=list)
    shop_windows: bool = False
    balconies: list[dict] = field(default_factory=list)
    shutters_on_upper: bool = False


@dataclass
class ManualLabel:
    label: str
    parcel_ids: list[str]
    verified: bool
    map_notes: str
    footprint_ref: str | None
    structure_type: str
    primary_zone_axis: ZoneAxis
    zones: list[Zone]
    facades: Facades
    footprint_mode: str = "traced"
    palette_override: dict | None = None
    open_questions: list[str] = field(default_factory=list)
