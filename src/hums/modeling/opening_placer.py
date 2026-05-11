"""PRD-002 · §5 — opening placement strategies.

Strategies:
 * DoorPlacer      — one primary door on the Excel-specified primary face,
                     falling back to longest street-facing wall.
 * ShopWindowPlacer — ground-floor shop windows on street-facing walls when
                      GF use is a shop/bakery/magazine.
 * UpperWindowPlacer — evenly spaced residential windows on each
                       street-facing wall above GF.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from ..common.prd import prd
from .building import Opening, WallSegment, Face, Storey
from .assumption_tracker import AssumptionTracker
from ..common.heritage_profile import PROFILE


def _is_shop_use(gf_code: str | None, gf_use: str | None) -> bool:
    for s in (gf_code, gf_use):
        if not s:
            continue
        s_low = s.lower()
        if any(k in s_low for k in ("mg", "shop", "bakery", "firin", "magazine", "café", "cafe")):
            return True
    return False


@prd("002", "§5 OpeningPlacer")
class OpeningPlacer(ABC):
    @abstractmethod
    def place(self, segments: list[WallSegment], storeys: list[Storey],
              excel: dict, parcel_id: str, tracker: AssumptionTracker) -> None:
        ...


class DoorPlacer(OpeningPlacer):
    """Primary door on the face matching Excel 'primary_door_face'."""

    def place(self, segments, storeys, excel, parcel_id, tracker):
        if excel.get("_structure_type") != "building":
            return
        openings = excel.get("openings") or {}
        text = _openings_text(openings)
        target_faces = _door_faces(openings)
        if not target_faces and _blocks_exterior_openings(excel):
            tracker.record(parcel_id, "wall.door", "map:pervititch", "no street door indicated")
            return
        if not target_faces:
            tracker.record(parcel_id, "wall.door", "map:pervititch", "no explicit mapped door face")
            return
        if _negative_door_evidence(openings) and not _is_glazed_structure(excel):
            tracker.record(parcel_id, "wall.door", "map:pervititch", "door evidence marked uncertain/negative")
            return

        placed = 0
        used_segments: set[int] = set()
        for target_face in target_faces:
            chosen = self._choose_segment(segments, target_face, strict_street=target_face is None)
            if chosen is None and target_face is not None:
                chosen = self._choose_unused_strict_street_segment(segments, used_segments)
            if chosen is None:
                continue
            used_segments.add(id(chosen))
            if any(op.kind == "door" for op in chosen.openings):
                continue

            o = PROFILE.openings
            w = min(o.door_w_m, max(0.0, chosen.length_m - 0.4))
            if w < 0.6:
                continue
            pos = max(0.2, (chosen.length_m - w) / 2.0)

            src = "map:pervititch" if target_face else "assumption:pervititch_1923"
            chosen.openings.append(Opening(
                kind="door", storey_level=0,
                position_along_wall_m=round(pos, 3),
                width_m=round(w, 3), height_m=o.door_h_m, sill_m=0.0,
                color_source=src,
            ))
            tracker.record(parcel_id, f"wall[{chosen.face}].door", src, {"w": w, "h": o.door_h_m})
            placed += 1
        if placed == 0:
            tracker.record(parcel_id, "wall.door", "map:pervititch", "no eligible exterior segment")

    def _choose_segment(self, segments, target_face, strict_street: bool):
        exterior = [s for s in segments if s.is_street_facing and not s.is_party_wall and s.length_m > 1.5]
        if not exterior:
            return None
        if target_face:
            matches = [s for s in exterior if s.face == target_face]
            if matches:
                matches.sort(key=lambda s: s.length_m, reverse=True)
                return matches[0]
            return None
        pool = [s for s in exterior if _is_strict_street(s)] if strict_street else exterior
        if not pool:
            pool = exterior
        pool.sort(key=lambda s: s.length_m, reverse=True)
        return pool[0]

    def _choose_unused_strict_street_segment(self, segments, used_segments: set[int]):
        pool = [
            s for s in segments
            if _is_strict_street(s)
            and not s.is_party_wall
            and s.length_m > 1.5
            and id(s) not in used_segments
            and not any(op.kind == "door" for op in s.openings)
        ]
        if not pool:
            return None
        pool.sort(key=lambda s: s.length_m, reverse=True)
        return pool[0]


class ShopWindowPlacer(OpeningPlacer):
    def place(self, segments, storeys, excel, parcel_id, tracker):
        if excel.get("_structure_type") != "building":
            return
        if _is_glazed_structure(excel):
            return
        if _blocks_exterior_openings(excel):
            return
        gf = excel.get("ground_floor") or {}
        if not _is_shop_use(gf.get("code"), gf.get("use")):
            return
        o = PROFILE.openings
        for seg in segments:
            if seg.is_party_wall or not _is_strict_street(seg):
                continue
            # reserve door zone: skip if a door already placed here
            door_ranges = [(op.position_along_wall_m, op.position_along_wall_m + op.width_m)
                           for op in seg.openings if op.kind == "door"]

            usable = max(0.0, seg.length_m - 1.0)
            count = max(0, int(usable // (o.shop_window_w_m + 0.6)))
            if count == 0:
                continue
            gap = (seg.length_m - count * o.shop_window_w_m) / (count + 1)
            for i in range(count):
                pos = gap + i * (o.shop_window_w_m + gap)
                if _overlaps(pos, pos + o.shop_window_w_m, door_ranges):
                    continue
                seg.openings.append(Opening(
                    kind="shop_window", storey_level=0,
                    position_along_wall_m=round(pos, 3),
                    width_m=o.shop_window_w_m, height_m=o.shop_window_h_m,
                    sill_m=o.shop_window_sill_m,
                    style="rectangular", frame_profile="moulded",
                    color_source="map:pervititch:shop-frontage + assumption:spacing",
                ))
            tracker.record(parcel_id, f"wall[{seg.face}].shop_windows.count", "map:pervititch", count)


class UpperWindowPlacer(OpeningPlacer):
    def place(self, segments, storeys, excel, parcel_id, tracker):
        if excel.get("_structure_type") != "building":
            return
        if _is_glazed_structure(excel):
            return
        if _blocks_exterior_openings(excel):
            return
        o = PROFILE.openings
        material_class = ((excel.get("material") or {}).get("class") or "").upper()
        upper_levels = [s.level for s in storeys if s.level >= 1 and not s.is_basement]
        if not upper_levels:
            return
        floor_zs = _storey_floor_zs(storeys)
        for seg in segments:
            if seg.length_m < 1.5:
                continue
            if seg.is_party_wall:
                adjacent_height = seg.adjacent_height_m
                if adjacent_height is None:
                    continue
                eligible_levels = [
                    lvl for lvl in upper_levels
                    if floor_zs.get(lvl, 0.0) + o.upper_window_sill_m >= adjacent_height + 0.2
                ]
                if not eligible_levels:
                    continue
                src = "map:geometry-detected:height-difference-exposed-party-wall"
            elif seg.is_street_facing:
                eligible_levels = upper_levels
                src = (
                    "map:geometry-detected:street-exposed-facade"
                    if _is_strict_street(seg)
                    else "map:geometry-detected:courtyard-exposed-facade"
                )
            else:
                continue
            count = max(1, int(round(seg.length_m / o.upper_window_spacing_m)))
            if not _is_strict_street(seg):
                count = max(1, min(count, int(max(1, seg.length_m // 3.0))))
            if count == 0:
                continue
            gap = (seg.length_m - count * o.upper_window_w_m) / (count + 1)
            if gap < 0.3:
                count = max(1, count - 1)
                gap = (seg.length_m - count * o.upper_window_w_m) / (count + 1)
            for lvl in eligible_levels:
                for i in range(count):
                    pos = gap + i * (o.upper_window_w_m + gap)
                    seg.openings.append(Opening(
                        kind="window", storey_level=lvl,
                        position_along_wall_m=round(pos, 3),
                        width_m=o.upper_window_w_m, height_m=o.upper_window_h_m,
                        sill_m=o.upper_window_sill_m,
                        style="rectangular",
                        pane_layout="2x2",
                        has_shutters=material_class.startswith("C"),
                        frame_profile="moulded",
                        color_source=src,
                    ))
            tracker.record(parcel_id, f"wall[{seg.face}].upper_windows.count_per_storey", src, count)


def _overlaps(a0, a1, ranges):
    for b0, b1 in ranges:
        if not (a1 < b0 or a0 > b1):
            return True
    return False


def _is_strict_street(seg: WallSegment) -> bool:
    return seg.hatch_pattern == "_street"


def _storey_floor_zs(storeys: list[Storey]) -> dict[int, float]:
    z = 0.0
    out: dict[int, float] = {}
    for s in sorted([s for s in storeys if not s.is_basement], key=lambda item: item.level):
        out[s.level] = z
        z += s.height_m
    return out


def _openings_text(openings: dict) -> str:
    return " ".join(str(v) for v in openings.values() if v is not None).lower()


def _says_internal_only(text: str) -> bool:
    return any(token in text for token in (
        "internal only",
        "internal access only",
        "no street door",
        "no street access",
        "no direct street access",
    ))


def _blocks_exterior_openings(excel: dict) -> bool:
    openings = excel.get("openings") or {}
    text = _openings_text(openings)
    if _says_internal_only(text):
        return True
    return "no arrow" in text and not _door_faces(openings)


def _negative_door_evidence(openings: dict) -> bool:
    text = _openings_text(openings)
    if "glazed porch" in text or "glass wall" in text or "transparent entrance" in text:
        return False
    return any(token in text for token in (
        "not arrow",
        "not entrance",
        "no clear arrow",
        "no explicit arrow",
        "inferred from typology",
        "may share",
        "possible shared",
        "possible ↓",
        "possible gate",
    ))


def _is_glazed_structure(excel: dict) -> bool:
    material = (excel.get("material") or {})
    roof = excel.get("roof") or {}
    text = " ".join(str(v) for v in (
        material.get("class"),
        material.get("raw_material_label"),
        (excel.get("ground_floor") or {}).get("use"),
        roof.get("material_code"),
        roof.get("material_decoded"),
        excel.get("bim_notes"),
    ) if v is not None).lower()
    return "glass" in text or "glazed" in text or "camlı" in text or "camli" in text


def _door_faces(openings: dict) -> list[Face]:
    faces: list[Face] = []
    for raw in [openings.get("primary_door_face") or ""]:
        raw_s = str(raw)
        if _says_internal_only(raw_s.lower()):
            continue
        for face in _faces_from_text(raw_s):
            if face not in faces:
                faces.append(face)
    if _secondary_is_exterior(openings):
        raw_s = str(openings.get("secondary_door_face") or "")
        for face in _faces_from_text(raw_s):
            if face not in faces:
                faces.append(face)
    return faces


def _secondary_is_exterior(openings: dict) -> bool:
    text = " ".join(str(openings.get(k) or "") for k in ("secondary_door_face", "secondary_door_type")).lower()
    if not text.strip() or text.strip(" —-") == "":
        return False
    if any(token in text for token in ("street", "courtyard", "gate", "corner")):
        return True
    if any(token in text for token in ("internal", "passage", "shared", "connection")):
        return False
    return bool(_faces_from_text(text))


def _faces_from_text(text: str) -> list[Face]:
    t = text.upper()
    letter = "A-ZÇĞİÖŞÜ"
    pairs: list[tuple[int, Face]] = []
    for pattern, face in (
        (r"\bNORTH\b", "N"),
        (r"\bEAST\b", "E"),
        (r"\bSOUTH\b", "S"),
        (r"\bWEST\b", "W"),
        (rf"(?<![{letter}])N(?![{letter}])", "N"),
        (rf"(?<![{letter}])E(?![{letter}])", "E"),
        (rf"(?<![{letter}])S(?![{letter}])", "S"),
        (rf"(?<![{letter}])W(?![{letter}])", "W"),
    ):
        m = re.search(pattern, t)
        if m:
            pairs.append((m.start(), face))  # type: ignore[arg-type]
    pairs.sort(key=lambda item: item[0])
    out: list[Face] = []
    for _, face in pairs:
        if face not in out:
            out.append(face)
    return out
