"""PRD-005 · Read every `data/manual/parcels/*.json` → ManualLabel list."""
from __future__ import annotations
import json
from pathlib import Path

from ..common.prd import prd
from .label_schema import (
    DoorHint, EntranceHint, Facades, ManualLabel, Zone, ZoneRoof,
)

MANUAL_ROOT = Path(__file__).resolve().parents[3] / "data" / "manual" / "parcels"


@prd("005", "ManualLabelLoader")
class ManualLabelLoader:
    def load_all(self) -> list[ManualLabel]:
        if not MANUAL_ROOT.exists():
            return []
        out: list[ManualLabel] = []
        for path in sorted(MANUAL_ROOT.glob("*.json")):
            out.append(self._load_one(path))
        return out

    def _load_one(self, path: Path) -> ManualLabel:
        d = json.loads(path.read_text())
        zones = [
            Zone(
                id=z["id"],
                description=z.get("description", ""),
                material_class=z["material_class"],
                map_colour=z.get("map_colour", ""),
                storeys_above_grade=float(z["storeys_above_grade"]),
                has_mezzanine=bool(z.get("has_mezzanine", False)),
                has_basement=bool(z.get("has_basement", False)),
                storey_heights_m=list(z["storey_heights_m"]),
                ground_floor_use=z.get("ground_floor_use", "shop"),
                roof=ZoneRoof(
                    shape=z["roof"]["shape"],
                    material=z["roof"]["material"],
                    pitch_deg=float(z["roof"]["pitch_deg"]),
                    has_chimney=bool(z["roof"].get("has_chimney", False)),
                    has_skylight=bool(z["roof"].get("has_skylight", False)),
                ),
                footprint_fraction=tuple(z["footprint_fraction"]),
                map_labels=list(z.get("map_labels", [])),
            )
            for z in d.get("zones", [])
        ]
        facades_d = d.get("facades") or {}
        facades = Facades(
            street_facing_faces=list(facades_d.get("street_facing_faces", [])),
            primary_door=_door(facades_d.get("primary_door")),
            secondary_door=_door(facades_d.get("secondary_door")),
            entrance_hints=[
                EntranceHint(
                    face=e["face"],
                    zone=e.get("zone", ""),
                    count=int(e.get("count", 1)),
                    description=e.get("description"),
                )
                for e in facades_d.get("entrance_hints", [])
                if isinstance(e, dict) and e.get("face")
            ],
            shop_windows=bool(facades_d.get("shop_windows", False)),
            balconies=list(facades_d.get("balconies", [])),
            shutters_on_upper=bool(facades_d.get("shutters_on_upper", False)),
        )
        parcel_ids = list(d.get("parcel_ids") or [])
        if not parcel_ids and d.get("parcel_id"):
            parcel_ids = [d["parcel_id"]]
        label = d.get("label") or "-".join(pid.replace("/", "_") for pid in parcel_ids)
        return ManualLabel(
            label=label,
            parcel_ids=parcel_ids,
            verified=bool(d.get("verified", False)),
            map_notes=d.get("map_notes", ""),
            footprint_ref=d.get("footprint_ref"),
            structure_type=d.get("structure_type", "building"),
            primary_zone_axis=d.get("primary_zone_axis", "north_to_south"),
            zones=zones,
            facades=facades,
            palette_override=d.get("palette_override"),
            open_questions=list(d.get("open_questions", [])),
        )


def _door(d) -> DoorHint | None:
    if not isinstance(d, dict):
        return None
    return DoorHint(face=d["face"], zone=d.get("zone", ""), description=d.get("description"))
