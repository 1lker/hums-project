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
from .building import Building, Opening, RoofDescriptor, Storey, Provenance
from .facade_palette import FacadePaletteBuilder
from .local_frame import LocalFrameBuilder
from .opening_placer import DoorPlacer, UpperWindowPlacer, _is_shop_use
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
        self._openers = [DoorPlacer(), UpperWindowPlacer()]

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
        if structure_type == "fountain":
            roof = RoofDescriptor(
                shape="flat",
                material="unknown",
                pitch_deg=0.0,
                slope_direction=None,
                has_chimney=False,
                has_skylight=False,
            )
            tracker.record(
                pid,
                "roof.fountain_coping",
                "map:pervititch",
                "non-building çeşme uses stone coping/plinth surfaces, not a house gable roof",
            )
        elif pid.startswith("W-32#"):
            roof = RoofDescriptor(
                shape="flat",
                material="unknown",
                pitch_deg=PROFILE.roofs.vault_flat_deg,
                slope_direction=None,
                has_chimney=False,
                has_skylight=False,
            )
            tracker.record(
                pid,
                "roof.W-32",
                "map:user-corrected",
                "tiny one-storey magazines use low flat/near-flat roof; no speculative gable",
            )
        elif pid in {"N-44", "N-48"}:
            roof.has_skylight = True
            tracker.record(
                pid,
                "roof.tabatiere",
                "map:pervititch",
                "interior x mark read as roof tabatiere/skylight, not as a facade door/window",
            )
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
        height_m = _above_grade_height(storeys)
        segments = self._wall_segmenter.segment(
            local_ring,
            footprint_utm,
            thickness,
            parcel_id=pid,
            building_height_m=height_m,
        )

        placer_ctx = {**parcel, "_structure_type": structure_type}
        for placer in self._openers:
            placer.place(segments, storeys, placer_ctx, pid, tracker)
        if pid.startswith("W-32#"):
            self._place_w32_magazine_openings(pid, segments, storeys, tracker)
        self._place_numbered_entrance_fallback(pid, parcel, source_file, segments, tracker)
        self._place_east_row_rear_map_window(pid, segments, storeys, tracker)

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

    def _place_w32_magazine_openings(self, pid: str, segments, storeys, tracker) -> None:
        """W-32 has three traced magazine polygons, but only parcel-level map
        text. The map arrow confirms west-facing access; add a conservative
        door and small upper openings on the best west/outer segment instead
        of leaving these as blank stone blocks.
        """
        candidates = [s for s in segments if s.length_m > 1.0]
        if not candidates:
            return
        west = [s for s in candidates if s.face == "W"]
        pool = west or candidates
        chosen = max(pool, key=lambda s: s.length_m)
        chosen.is_party_wall = False
        chosen.is_street_facing = True
        chosen.hatch_pattern = "_street"

        o = PROFILE.openings
        door_w = min(o.door_w_m, max(0.75, chosen.length_m - 0.4))
        door_pos = max(0.2, (chosen.length_m - door_w) / 2.0)
        if not any(op.kind == "door" for op in chosen.openings):
            chosen.openings.append(Opening(
                kind="door",
                storey_level=0,
                position_along_wall_m=round(door_pos, 3),
                width_m=round(door_w, 3),
                height_m=o.door_h_m,
                sill_m=0.0,
                style="arched",
                frame_profile="moulded",
                color_source="map:pervititch:W-32 west entrance arrow",
            ))

        tracker.record(pid, "openings.W-32", "map:pervititch", "west door only; unmarked window assumptions suppressed")

    def _place_numbered_entrance_fallback(self, pid: str, parcel: dict, source_file: str | None,
                                          segments, tracker) -> None:
        """Conservative door for numbered `building-entrence` map areas.

        Some parsed rows mark the door arrow as uncertain ("dash", "possible
        shared gate") even though the traced source and map label are a
        numbered entrance parcel. In those cases, add one plain door on the
        best exterior segment instead of leaving the numbered unit blank.
        """
        if parcel.get("_structure_type") not in (None, "building"):
            return
        if not parcel.get("parcel_number"):
            return
        source = (source_file or "").lower()
        if "building-entrence" not in source and "buildingentrence" not in source:
            return
        if any(op.kind == "door" for seg in segments for op in seg.openings):
            return

        target_faces = _face_hints_from_text(
            " ".join(str(v) for v in (
                (parcel.get("openings") or {}).get("primary_door_face"),
                parcel.get("street_facing"),
            ) if v)
        )

        candidates = [
            s for s in segments
            if not s.is_party_wall and s.length_m > 1.2
        ]
        if not candidates:
            return
        face_candidates = [s for s in candidates if s.face in target_faces]
        strict_candidates = [s for s in candidates if s.hatch_pattern == "_street"]
        pool = face_candidates or strict_candidates or candidates
        chosen = max(pool, key=lambda s: s.length_m)
        chosen.is_street_facing = True
        if chosen.hatch_pattern is None and chosen.face in {"N", "E", "S", "W"}:
            chosen.hatch_pattern = "_street"

        o = PROFILE.openings
        width = min(o.door_w_m, max(0.75, chosen.length_m - 0.4))
        if width < 0.6:
            return
        pos = max(0.2, (chosen.length_m - width) / 2.0)
        chosen.openings.append(Opening(
            kind="door",
            storey_level=0,
            position_along_wall_m=round(pos, 3),
            width_m=round(width, 3),
            height_m=o.door_h_m,
            sill_m=0.0,
            style="rectangular",
            frame_profile="moulded",
            color_source="map:pervititch:numbered-entrance-fallback",
        ))
        tracker.record(
            pid,
            f"wall[{chosen.face}].numbered_entrance_fallback",
            "map:pervititch",
            {"parcel_number": parcel.get("parcel_number"), "source_file": source_file},
        )

    def _place_east_row_rear_map_window(self, pid: str, segments, storeys, tracker) -> None:
        """User/map-confirmed rear/notch window for east-row magazines.

        This is deliberately not a generic shop-window rule. These small
        shops otherwise have no upper-window logic when they are one-storey,
        and rear edges can be over-classified as party walls by the
        georeferenced footprint overlap. The Pervititch reread marks one
        centered rear opening/notch for 4, 6, 8, 10 and the same small
        notch/triangle evidence is visible on 12 and 14.
        """
        if pid not in {"E-4", "E-6", "E-8", "E-10", "E-12", "E-14"}:
            return
        if any(
            op.kind == "window" and op.color_source.startswith("map:pervititch:east-row-rear")
            for seg in segments
            for op in seg.openings
        ):
            return

        seg = _rear_segment_for_east_row_shop(segments)
        if seg is None or seg.length_m < 1.05:
            tracker.record(pid, "wall.rear_center_window", "map:pervititch", "no eligible rear segment")
            return

        # The map evidence is a modest rear window, not a street shopfront.
        seg.is_party_wall = False
        seg.is_street_facing = True
        seg.adjacent_height_m = None
        width = min(0.90, max(0.62, seg.length_m - 0.80))
        pos = max(0.18, (seg.length_m - width) / 2.0)
        seg.openings.append(Opening(
            kind="window",
            storey_level=0,
            position_along_wall_m=round(pos, 3),
            width_m=round(width, 3),
            height_m=1.05,
            sill_m=1.35,
            style="rectangular",
            pane_layout="2x2",
            has_shutters=False,
            has_balcony=False,
            frame_profile="moulded",
            color_source="map:pervititch:east-row-rear-notch-window",
        ))
        tracker.record(
            pid,
            f"wall[{seg.face}].rear_center_window",
            "map:pervititch",
            "one centered rear-facing window placed from map notch/triangle evidence",
        )

    def _storeys(self, parcel: dict, tracker: AssumptionTracker, structure_type: str = "building") -> list[Storey]:
        # Monuments (çeşme etc.) get one facade-storey; no upper floors/basement.
        if structure_type == "fountain":
            h_body = 3.65
            tracker.assume(parcel["parcel_id"], "storeys[0].height_m", h_body,
                           note="fountain: photo-guided Ottoman street-fountain facade height, no upper floors")
            return [Storey(level=0, height_m=h_body, use="fountain_body")]

        if structure_type == "bell_tower":
            h_body = 10.0
            tracker.assume(parcel["parcel_id"], "storeys[0].height_m", h_body,
                           note="bell tower (clocher)")
            return [Storey(level=0, height_m=h_body, use="bell_tower")]

        if parcel["parcel_id"].startswith("W-32#"):
            h_body = 3.0
            tracker.record(
                parcel["parcel_id"],
                "storeys.W-32",
                "map:user-corrected",
                "three tiny corner magazines are one-storey, not the Excel row's 2-storey interpretation",
            )
            tracker.assume(parcel["parcel_id"], "storeys[0].height_m", h_body,
                           note="low one-storey corner magazine")
            return [Storey(level=0, height_m=h_body, use="tiny_magazine")]

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


def _above_grade_height(storeys: list[Storey]) -> float:
    return sum(s.height_m for s in storeys if not s.is_basement)


def _rear_segment_for_east_row_shop(segments) -> object | None:
    west = [s for s in segments if s.face == "W" and s.length_m > 1.0]
    if west:
        return max(west, key=lambda s: s.length_m)

    door_idx = None
    for idx, seg in enumerate(segments):
        if any(op.kind == "door" for op in seg.openings):
            door_idx = idx
            break
    if door_idx is not None and segments:
        opposite = segments[(door_idx + len(segments) // 2) % len(segments)]
        if opposite.length_m > 1.0:
            return opposite

    candidates = [
        s for s in segments
        if s.length_m > 1.0
        and not any(op.kind == "door" for op in s.openings)
    ]
    return max(candidates, key=lambda s: s.length_m) if candidates else None


def _snapshot(parcel: dict) -> dict:
    """Slim view of Excel data worth keeping on each Building for inspection."""
    return {
        "parcel_number": parcel.get("parcel_number"),
        "zone": parcel.get("zone"),
        "street_facing": parcel.get("street_facing"),
        "material": parcel.get("material"),
        "openings": parcel.get("openings"),
        "storeys_raw": (parcel.get("storeys") or {}).get("raw"),
        "wall_code": (parcel.get("wall") or {}).get("code"),
        "vault_code": (parcel.get("vault") or {}).get("code"),
        "bim_notes": parcel.get("bim_notes"),
    }


def _face_hints_from_text(text: str) -> list[str]:
    t = text.upper()
    out: list[str] = []
    for word, face in (
        ("NORTH", "N"), ("EAST", "E"), ("SOUTH", "S"), ("WEST", "W"),
    ):
        if word in t and face not in out:
            out.append(face)
    for face in ("N", "E", "S", "W"):
        if f" {face} " in f" {t} " and face not in out:
            out.append(face)
    return out
