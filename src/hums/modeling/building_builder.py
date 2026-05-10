"""PRD-002 · §9 BuildingBuilder — Facade joining all subsystems.

Input : one parcel dict (from parcels.json) + matched footprint polygon (UTM) + block outline.
Output: one fully-populated ``Building`` + provenance entries on the shared tracker.
"""
from __future__ import annotations
from dataclasses import replace

from shapely.geometry import Polygon

from ..common.prd import prd
from ..common.heritage_profile import PROFILE
from .assumption_tracker import AssumptionTracker
from .building import Building, Storey, Provenance
from .facade_palette import FacadePaletteBuilder
from .local_frame import LocalFrameBuilder
from .opening_placer import DoorPlacer, ShopWindowPlacer, UpperWindowPlacer, _is_shop_use
from .party_wall_index import PartyWallIndex
from .roof_descriptor import RoofDescriptorBuilder
from .structure_classifier import StructureClassifier
from .wall_segmenter import WallSegmenter


@prd("002", "§9 BuildingBuilder")
class BuildingBuilder:
    def __init__(self, block_outline: Polygon | None,
                 party_index: PartyWallIndex | None = None) -> None:
        self._frame_builder = LocalFrameBuilder(block_outline)
        self._wall_segmenter = WallSegmenter(block_outline, party_index=party_index)
        self._roof_builder = RoofDescriptorBuilder()
        self._palette_builder = FacadePaletteBuilder()
        self._structure_classifier = StructureClassifier()
        self._openers = [DoorPlacer(), ShopWindowPlacer(), UpperWindowPlacer()]

    def build(
        self,
        parcel: dict,
        footprint_utm: Polygon | None,
        footprint_source: str,
        source_file: str | None,
        tracker: AssumptionTracker,
    ) -> Building:
        pid = parcel["parcel_id"]
        material_class = (parcel.get("material") or {}).get("class")
        gf = parcel.get("ground_floor") or {}
        gf_shop = _is_shop_use(gf.get("code"), gf.get("use"))

        structure_type, notes = self._structure_classifier.classify(parcel, filename_override=source_file)
        tracker.record(pid, "structure_type", "excel-inferred", structure_type)

        storeys = self._storeys(parcel, tracker, structure_type)
        roof = self._roof_builder.build(parcel.get("roof") or {}, pid, tracker)
        palette = self._palette_builder.build(material_class, gf_shop, pid, tracker)

        if footprint_utm is None:
            tracker.record(pid, "footprint", "missing", None)
            return Building(
                parcel_id=pid,
                material_class=material_class,
                footprint_source="missing",
                local_frame=None,
                structure_type=structure_type,
                notes=notes,
                storeys=storeys,
                roof=roof,
                facade_palette=palette,
                provenance=Provenance(footprint_source_file=None),
                excel_snapshot=_snapshot(parcel),
            )

        frame, local_ring = self._frame_builder.build(footprint_utm)
        thickness = self._wall_thickness(material_class, parcel, tracker)
        segments = self._wall_segmenter.segment(local_ring, footprint_utm, thickness, parcel_id=pid)

        placer_ctx = {**parcel, "_structure_type": structure_type}
        for placer in self._openers:
            placer.place(segments, storeys, placer_ctx, pid, tracker)

        return Building(
            parcel_id=pid,
            material_class=material_class,
            footprint_source=footprint_source,  # type: ignore[arg-type]
            local_frame=frame,
            structure_type=structure_type,
            notes=notes,
            footprint_local=local_ring,
            storeys=storeys,
            wall_segments=segments,
            roof=roof,
            facade_palette=palette,
            provenance=Provenance(footprint_source_file=source_file),
            excel_snapshot=_snapshot(parcel),
        )

    def _storeys(self, parcel: dict, tracker: AssumptionTracker, structure_type: str = "building") -> list[Storey]:
        # Monuments (çeşme etc.) get a single short body storey; no upper levels, no basement.
        if structure_type == "fountain":
            h_body = 1.8
            tracker.assume(parcel["parcel_id"], "storeys[0].height_m", h_body,
                           note="fountain: monumental body, no upper floors")
            return [Storey(level=0, height_m=h_body, use="fountain_body")]

        if structure_type == "bell_tower":
            h_body = 10.0
            tracker.assume(parcel["parcel_id"], "storeys[0].height_m", h_body,
                           note="bell tower (clocher)")
            return [Storey(level=0, height_m=h_body, use="bell_tower")]

        s_info = parcel.get("storeys") or {}
        count = s_info.get("count") or 1
        mezzanine = bool(s_info.get("has_mezzanine"))
        basement = parcel.get("basement")
        basement_present = bool(basement) and str(basement).strip().lower() not in {"none", "—", "-", ""}
        gf = parcel.get("ground_floor") or {}
        gf_use = _gf_use_label(gf, parcel)

        h = PROFILE.storeys
        out: list[Storey] = []
        level = 0
        if basement_present:
            out.append(Storey(level=-1, height_m=h.basement_m, is_basement=True, use="basement"))
            tracker.assume(parcel["parcel_id"], "storeys[-1].height_m", h.basement_m)

        out.append(Storey(level=level, height_m=h.ground_shop_m, use=gf_use))
        tracker.assume(parcel["parcel_id"], "storeys[0].height_m", h.ground_shop_m)

        if mezzanine:
            out.append(Storey(level=1, height_m=h.mezzanine_m, is_mezzanine=True, use="mezzanine"))
            tracker.assume(parcel["parcel_id"], "storeys[mezz].height_m", h.mezzanine_m)

        base_level = 2 if mezzanine else 1
        for i in range(max(0, count - 1)):
            lvl = base_level + i
            out.append(Storey(level=lvl, height_m=h.upper_residential_m, use="residential"))
            tracker.assume(parcel["parcel_id"], f"storeys[{lvl}].height_m", h.upper_residential_m)
        return out

    def _wall_thickness(self, material_class, parcel, tracker) -> float:
        # Future: parse parcel['wall']['thickness_raw'] if populated.
        if (material_class or "").upper().startswith("C"):
            tracker.assume(parcel["parcel_id"], "wall.thickness_m", PROFILE.walls.wooden_m)
            return PROFILE.walls.wooden_m
        tracker.assume(parcel["parcel_id"], "wall.thickness_m", PROFILE.walls.masonry_m)
        return PROFILE.walls.masonry_m


def _gf_use_label(gf: dict, parcel: dict) -> str:
    code = (gf.get("code") or "").lower()
    use = (gf.get("use") or "").lower()
    if "firin" in use or "bakery" in use:
        return "bakery"
    if "mg" in code or "shop" in use:
        return "shop"
    if "magazine" in use:
        return "magazine"
    return gf.get("use") or "ground_floor"


def _snapshot(parcel: dict) -> dict:
    """Slim view of Excel data worth keeping on each Building for inspection."""
    return {
        "parcel_number": parcel.get("parcel_number"),
        "zone": parcel.get("zone"),
        "street_facing": parcel.get("street_facing"),
        "material": parcel.get("material"),
        "storeys_raw": (parcel.get("storeys") or {}).get("raw"),
        "wall_code": (parcel.get("wall") or {}).get("code"),
        "vault_code": (parcel.get("vault") or {}).get("code"),
        "bim_notes": parcel.get("bim_notes"),
    }
