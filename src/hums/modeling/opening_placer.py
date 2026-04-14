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
    FACE_MAP = {"N": "N", "NORTH": "N", "E": "E", "EAST": "E",
                "S": "S", "SOUTH": "S", "W": "W", "WEST": "W"}

    def place(self, segments, storeys, excel, parcel_id, tracker):
        if excel.get("_structure_type") != "building":
            return
        primary_face_raw = (excel.get("openings") or {}).get("primary_door_face") or ""
        target_face: Face | None = None
        for key, val in self.FACE_MAP.items():
            if key in primary_face_raw.upper():
                target_face = val  # type: ignore[assignment]
                break

        chosen = self._choose_segment(segments, target_face)
        if chosen is None:
            return

        o = PROFILE.openings
        w = min(o.door_w_m, max(0.0, chosen.length_m - 0.4))
        if w < 0.6:
            return
        pos = max(0.2, (chosen.length_m - w) / 2.0)

        chosen.openings.append(Opening(
            kind="door", storey_level=0,
            position_along_wall_m=round(pos, 3),
            width_m=round(w, 3), height_m=o.door_h_m, sill_m=0.0,
        ))
        src = "excel" if target_face else "assumption:pervititch_1923"
        tracker.record(parcel_id, f"wall[{chosen.face}].door", src, {"w": w, "h": o.door_h_m})

    def _choose_segment(self, segments, target_face):
        street = [s for s in segments if s.is_street_facing and s.length_m > 1.5]
        if not street:
            return None
        if target_face:
            matches = [s for s in street if s.face == target_face]
            if matches:
                matches.sort(key=lambda s: s.length_m, reverse=True)
                return matches[0]
        street.sort(key=lambda s: s.length_m, reverse=True)
        return street[0]


class ShopWindowPlacer(OpeningPlacer):
    def place(self, segments, storeys, excel, parcel_id, tracker):
        if excel.get("_structure_type") != "building":
            return
        gf = excel.get("ground_floor") or {}
        if not _is_shop_use(gf.get("code"), gf.get("use")):
            return
        o = PROFILE.openings
        for seg in segments:
            if not seg.is_street_facing:
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
                ))
            tracker.assume(parcel_id, f"wall[{seg.face}].shop_windows.count", count)


class UpperWindowPlacer(OpeningPlacer):
    def place(self, segments, storeys, excel, parcel_id, tracker):
        if excel.get("_structure_type") != "building":
            return
        o = PROFILE.openings
        upper_levels = [s.level for s in storeys if s.level >= 1 and not s.is_basement]
        if not upper_levels:
            return
        for seg in segments:
            if not seg.is_street_facing or seg.length_m < 1.5:
                continue
            count = max(1, int(round(seg.length_m / o.upper_window_spacing_m)))
            if count == 0:
                continue
            gap = (seg.length_m - count * o.upper_window_w_m) / (count + 1)
            if gap < 0.3:
                count = max(1, count - 1)
                gap = (seg.length_m - count * o.upper_window_w_m) / (count + 1)
            for lvl in upper_levels:
                for i in range(count):
                    pos = gap + i * (o.upper_window_w_m + gap)
                    seg.openings.append(Opening(
                        kind="window", storey_level=lvl,
                        position_along_wall_m=round(pos, 3),
                        width_m=o.upper_window_w_m, height_m=o.upper_window_h_m,
                        sill_m=o.upper_window_sill_m,
                        style="rectangular",
                        pane_layout="2x2",
                        has_shutters=True,
                        frame_profile="moulded",
                    ))
            tracker.assume(parcel_id, f"wall[{seg.face}].upper_windows.count_per_storey", count)


def _overlaps(a0, a1, ranges):
    for b0, b1 in ranges:
        if not (a1 < b0 or a0 > b1):
            return True
    return False
