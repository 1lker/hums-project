"""PRD-005 · Render one manually-labelled building (e.g. N-40-42).

For each zone in the label:
  * Splits the shared footprint along the building's primary axis via
    `footprint_fraction`.
  * Builds a `Building` dataclass with that zone's material / storeys /
    roof / GF use.
  * Every cross-zone edge is a party wall (no openings there).
  * Edges shared with other parcels' traced polygons are party walls too.

Emits:
    output/buildings/<label>/
        <label>.glb             — glTF of all zones combined
        <label>_profile.md      — per-zone stats
"""
from __future__ import annotations
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, shape

from ..common.heritage_profile import PROFILE
from ..common.paths import BLOCK_GEOJSON, FOOTPRINTS_GEOJSON, PROJECT_ROOT
from ..common.prd import prd
from ..manual.label_loader import ManualLabelLoader, MANUAL_ROOT
from ..manual.label_schema import ManualLabel, Zone
from ..manual.zone_splitter import split_zone
from ..modeling.building import (
    Building, FacadePalette, LocalFrame, Opening, Provenance,
    RoofDescriptor, Storey, WallSegment,
)
from ..modeling.party_wall_index import PartyWallIndex
from ..modeling.facade_palette import FacadePaletteBuilder
from ..modeling.assumption_tracker import AssumptionTracker
from ..modeling.local_frame import LocalFrameBuilder
from ..modeling.opening_placer import DoorPlacer, UpperWindowPlacer
from ..modeling.wall_segmenter import WallSegmenter
from ..render.backends.gltf_backend import GltfBackend
from ..render.building_geometry_builder import BuildingGeometryBuilder
from ..render.scene_assembler import SceneAssembler
from ..render.special.landscape_builder import N50_REAR_LIGHTWELL_UTM


OUT_ROOT = PROJECT_ROOT / "output" / "buildings"


@prd("005", "ManualRenderer")
class ManualRenderer:
    def render(self, label_key: str) -> Path:
        label, meshes, block_centroid = self.build_meshes(label_key)
        scene = SceneAssembler().assemble(meshes, block_centroid)

        out_dir = OUT_ROOT / label.label
        out_dir.mkdir(parents=True, exist_ok=True)
        glb = out_dir / f"{label.label}.glb"
        GltfBackend().export_scene(scene, glb)

        profile = out_dir / f"{label.label}_profile.md"
        profile.write_text(self._profile(label, meshes))

        print(f"Rendered {label_key}")
        print(f"  label: {label.label}  parcels: {label.parcel_ids}")
        print(f"  zones rendered: {len(meshes)}/{len(label.zones)}")
        print(f"  faces total: {sum(len(m.faces) for m in meshes)}")
        print(f"  3D: {glb.relative_to(PROJECT_ROOT)}")
        print(f"  report: {profile.relative_to(PROJECT_ROOT)}")
        return out_dir

    def build_meshes(self, label_key: str):
        """Build manual-zone meshes without exporting them.

        PRD-003 uses this to substitute map-verified manual labels into the
        full block scene while keeping this focused renderer as the source of
        truth for the zone split.
        """
        label = self._find_label(label_key)
        if label is None:
            raise SystemExit(f"no manual label found for {label_key!r}")

        footprint = self._load_footprint(label)
        if footprint is None:
            raise SystemExit(f"no footprint polygon for {label_key!r} "
                             f"(footprint_ref={label.footprint_ref})")

        block_centroid = self._block_centroid()
        block_poly = self._block_polygon()

        # Pre-compute all zone sub-polygons. Most manual labels use fractional
        # splits; N-50 is map-read as an L plan, so it has a dedicated cutter.
        zone_polys = _zone_polys_for_label(label, footprint)

        # Party wall index seeded with (a) every zone (so inter-zone edges
        # are party walls) and (b) every OTHER parcel's traced polygon so
        # shared block-perimeter walls are recognised.
        party_index = PartyWallIndex()
        for zid, poly in zone_polys.items():
            zone = next((z for z in label.zones if z.id == zid), None)
            party_index.register(
                f"{label.label}.{zid}",
                poly,
                sum(zone.storey_heights_m) if zone else None,
            )
        for feat in self._other_parcel_features(label):
            for matched in feat["properties"].get("parcel_ids_matched") or []:
                party_index.register(matched, shape(feat["geometry"]))

        frame_builder = LocalFrameBuilder(block_poly)
        segmenter = WallSegmenter(block_poly, party_index=party_index)
        palette_builder = FacadePaletteBuilder()
        tracker = AssumptionTracker()
        geom_builder = BuildingGeometryBuilder()

        meshes = []
        for z in label.zones:
            sub_poly = zone_polys.get(z.id)
            if sub_poly is None:
                continue
            building = self._build_zone_building(
                label, z, sub_poly, frame_builder, segmenter,
                palette_builder, tracker,
            )
            mesh = geom_builder.build(building)
            if mesh is None:
                continue
            self._emit_manual_subunit_details(label, building, mesh)
            mesh.metadata["source_footprint_file"] = label.footprint_ref
            mesh.metadata["manual_label"] = label.label
            mesh.metadata["manual_zone"] = z.id
            mesh.metadata["opening_counts"] = self._opening_counts(building)
            meshes.append(mesh)

        return label, meshes, block_centroid

    # ---- helpers -----------------------------------------------------------
    def _find_label(self, key: str) -> ManualLabel | None:
        for label in ManualLabelLoader().load_all():
            if label.label == key or key in label.parcel_ids:
                return label
        return None

    def _load_footprint(self, label: ManualLabel):
        if not FOOTPRINTS_GEOJSON.exists():
            return None
        fc = json.loads(FOOTPRINTS_GEOJSON.read_text())
        # Prefer the explicit footprint_ref; fall back to any feature whose
        # parcel_ids_matched overlap label.parcel_ids.
        for feat in fc["features"]:
            if label.footprint_ref and feat["properties"].get("source_file") == label.footprint_ref:
                return _manual_footprint(shape(feat["geometry"]), label)
        for feat in fc["features"]:
            matched = feat["properties"].get("parcel_ids_matched") or []
            if any(pid in matched for pid in label.parcel_ids):
                return _manual_footprint(shape(feat["geometry"]), label)
        return None

    def _other_parcel_features(self, label: ManualLabel):
        if not FOOTPRINTS_GEOJSON.exists():
            return []
        fc = json.loads(FOOTPRINTS_GEOJSON.read_text())
        out = []
        for feat in fc["features"]:
            matched = feat["properties"].get("parcel_ids_matched") or []
            if not matched:
                continue
            if any(pid in matched for pid in label.parcel_ids):
                continue   # same building's polygon
            out.append(feat)
        return out

    def _block_centroid(self):
        if not BLOCK_GEOJSON.exists():
            return (0.0, 0.0)
        feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
        if not feats:
            return (0.0, 0.0)
        c = shape(feats[0]["geometry"]).centroid
        return (c.x, c.y)

    def _block_polygon(self):
        if not BLOCK_GEOJSON.exists():
            return None
        feats = json.loads(BLOCK_GEOJSON.read_text())["features"]
        return shape(feats[0]["geometry"]) if feats else None

    def _build_zone_building(self, label: ManualLabel, zone: Zone, sub_poly,
                             frame_builder, segmenter, palette_builder,
                             tracker) -> Building:
        zone_pid = f"{label.label}.{zone.id}"
        frame, local_ring = frame_builder.build(sub_poly)
        thickness = 0.55 if zone.material_class in ("A", "B") else 0.20
        segments = segmenter.segment(
            local_ring,
            sub_poly,
            thickness,
            parcel_id=zone_pid,
            building_height_m=sum(zone.storey_heights_m),
        )
        self._apply_manual_facade_overrides(label, segments)

        storeys: list[Storey] = []
        if zone.has_basement:
            storeys.append(Storey(level=-1, height_m=2.4, is_basement=True, use="basement"))
        for i, h in enumerate(zone.storey_heights_m):
            use = zone.ground_floor_use if i == 0 else "residential"
            is_mezz = (i == 1 and zone.has_mezzanine and h < 3.0)
            storeys.append(Storey(
                level=i, height_m=h,
                is_mezzanine=is_mezz, is_basement=False,
                use=use,
            ))

        roof = RoofDescriptor(
            shape=zone.roof.shape,  # type: ignore[arg-type]
            material=zone.roof.material,  # type: ignore[arg-type]
            pitch_deg=zone.roof.pitch_deg,
            slope_direction=None,
            has_chimney=zone.roof.has_chimney,
            has_skylight=zone.roof.has_skylight,
        )

        gf_shop = zone.ground_floor_use in ("shop", "bakery", "magazine", "cafe")
        palette = palette_builder.build(zone.material_class, gf_shop, zone_pid, tracker)
        if label.palette_override:
            for k, v in label.palette_override.items():
                if hasattr(palette, k) and v:
                    setattr(palette, k, tuple(v))
            palette.source = "manual_palette_override"

        # Opening placement per manual hints.
        self._place_zone_openings(label, zone, segments, tracker, zone_pid)

        return Building(
            parcel_id=zone_pid,
            material_class=zone.material_class,
            footprint_source="traced",
            local_frame=frame,
            structure_type="building",
            notes={"label": label.label, "zone_id": zone.id,
                   "map_labels": zone.map_labels,
                   "description": zone.description},
            footprint_local=local_ring,
            storeys=storeys,
            wall_segments=segments,
            roof=roof,
            facade_palette=palette,
            shared_footprint_group_id=label.label,
            parent_parcel_id=label.label,
            provenance=Provenance(
                footprint_source_file=label.footprint_ref,
                attribute_sources={"zone": "manual", "material": "manual"},
            ),
            excel_snapshot={"parcel_ids": label.parcel_ids, "manual": True},
        )

    @staticmethod
    def _apply_manual_facade_overrides(label: ManualLabel, segments: list[WallSegment]) -> None:
        """Use map-read facade hints to close faces that georeferencing left ambiguous."""
        strict_faces = set(label.facades.street_facing_faces)
        opaque_faces = set(getattr(label.facades, "opaque_faces", []) or [])
        if not strict_faces and not opaque_faces:
            return

        for seg in segments:
            if seg.face in opaque_faces:
                seg.is_street_facing = False
                seg.is_party_wall = True
                seg.hatch_pattern = None
                continue
            if seg.face in strict_faces and not seg.is_party_wall:
                seg.is_street_facing = True
                seg.hatch_pattern = "_street"
            elif seg.hatch_pattern == "_street":
                seg.hatch_pattern = None

    @staticmethod
    def _opening_counts(building: Building) -> dict[str, int]:
        counts = {"door": 0, "shop_window": 0, "window": 0}
        for seg in building.wall_segments:
            for opening in seg.openings:
                if opening.kind in counts:
                    counts[opening.kind] += 1
        return counts

    def _place_zone_openings(self, label: ManualLabel, zone: Zone,
                             segments: list[WallSegment], tracker,
                             zone_pid: str) -> None:
        """Run the usual placers on non-party walls, respecting manual hints."""
        primary_face = (
            label.facades.primary_door.face
            if label.facades.primary_door and label.facades.primary_door.zone == zone.id
            else None
        )
        secondary_face = (
            label.facades.secondary_door.face
            if label.facades.secondary_door and label.facades.secondary_door.zone == zone.id
            else None
        )
        ctx = {
            "_structure_type": "building",
            "ground_floor": {
                "code": "Mg." if zone.ground_floor_use in ("shop", "bakery", "magazine") else "",
                "use": zone.ground_floor_use,
            },
            "openings": {
                "primary_door_face": primary_face,
                "secondary_door_face": secondary_face,
                "secondary_door_type": "courtyard/service" if secondary_face else None,
            },
        }
        storeys_proxy = [Storey(level=i, height_m=h)
                          for i, h in enumerate(zone.storey_heights_m)]
        if primary_face or secondary_face:
            DoorPlacer().place(segments, storeys_proxy, ctx, zone_pid, tracker)
        self._place_manual_entrances(label, zone, segments, tracker, zone_pid)
        self._adjust_firin_corner_entrance(label, zone, segments, tracker, zone_pid)
        self._adjust_church_camli_entrance(label, zone, segments, tracker, zone_pid)
        self._place_church_wooden_annex_window(label, zone, segments, tracker, zone_pid)
        self._place_explicit_vitrine(label, zone, segments, tracker, zone_pid)
        UpperWindowPlacer().place(segments, storeys_proxy, ctx, zone_pid, tracker)
        self._place_n50_lower_lightwell_window(label, zone, segments, tracker, zone_pid)
        self._place_n50_rear_lightwell_windows(label, zone, segments, tracker, zone_pid)

    def _place_manual_entrances(self, label: ManualLabel, zone: Zone,
                                segments: list[WallSegment], tracker,
                                zone_pid: str) -> None:
        hints = [h for h in label.facades.entrance_hints if h.zone == zone.id]
        if not hints:
            return

        o = PROFILE.openings
        for hint in hints:
            wants_vitrine = _zone_wants_vitrine(zone)
            pool = [
                s for s in segments
                if s.face == hint.face
                and not s.is_party_wall
                and s.length_m > 0.75
            ]
            if not pool:
                pool = [
                    s for s in segments
                    if not s.is_party_wall and s.length_m > 0.9
                ]
            if not pool:
                continue

            pool.sort(key=lambda s: s.length_m, reverse=True)
            seg = pool[0]
            count = max(1, min(int(hint.count), max(1, int(seg.length_m // 1.8))))
            edge_margin = 0.15 if seg.length_m < 1.5 else 0.25
            door_w = min(o.door_w_m, (seg.length_m - edge_margin * (count + 1)) / count)
            if wants_vitrine and count == 1:
                door_w = min(door_w, 0.8)
            if door_w < 0.55:
                continue
            gap = (seg.length_m - count * door_w) / (count + 1)
            if gap < edge_margin:
                gap = edge_margin
            existing = [
                (op.position_along_wall_m, op.position_along_wall_m + op.width_m)
                for op in seg.openings
                if op.kind == "door"
            ]
            for i in range(count):
                if wants_vitrine and count == 1:
                    pos = edge_margin
                else:
                    pos = max(edge_margin, gap + i * (door_w + gap))
                end = pos + door_w
                if any(not (end < a or pos > b) for a, b in existing):
                    continue
                seg.openings.append(Opening(
                    kind="door",
                    storey_level=0,
                    position_along_wall_m=round(pos, 3),
                    width_m=round(door_w, 3),
                    height_m=o.door_h_m,
                    sill_m=0.0,
                    style="rectangular",
                    frame_profile="moulded",
                    color_source=f"map:pervititch:{label.label}:entrance-labels",
                ))
                existing.append((pos, end))
            tracker.record(
                zone_pid,
                f"wall[{hint.face}].manual_entrances",
                "map:pervititch",
                {"count": count, "description": hint.description},
            )

    def _adjust_firin_corner_entrance(self, label: ManualLabel, zone: Zone,
                                      segments: list[WallSegment], tracker,
                                      zone_pid: str) -> None:
        if label.label != "W-34-36-FIRIN" or zone.id != "bakery_mass":
            return
        long_w_segments = [
            s for s in segments
            if s.face == "W" and not s.is_party_wall and s.length_m > 3.0
        ]
        if not long_w_segments:
            return
        main_seg = max(long_w_segments, key=lambda s: s.length_m)
        main_doors = [
            op for op in main_seg.openings
            if op.kind == "door" and op.storey_level == 0
        ]
        if not main_doors:
            return

        diagonal_w_candidates = [
            s for s in segments
            if s is not main_seg
            and s.face == "W"
            and not s.is_party_wall
            and 1.45 <= s.length_m <= 2.75
        ]
        if diagonal_w_candidates:
            # The map kink for the Firin door is the short diagonal W face
            # immediately before the long west frontage, not the tiny connector
            # segment between the two.
            corner_seg = max(
                diagonal_w_candidates,
                key=lambda s: ((s.start[1] + s.end[1]) * 0.5, s.length_m),
            )
        else:
            corner_candidates = []
            for seg in segments:
                if seg is main_seg or seg.is_party_wall or seg.length_m < 0.72:
                    continue
                touches_main_start = (
                    _pt_dist(seg.start, main_seg.start) < 0.08
                    or _pt_dist(seg.end, main_seg.start) < 0.08
                )
                if not touches_main_start:
                    continue
                dx = seg.end[0] - seg.start[0]
                dy = seg.end[1] - seg.start[1]
                diagonal_score = abs(dx) + abs(dy) - max(abs(dx), abs(dy))
                corner_candidates.append((diagonal_score, seg))
            if not corner_candidates:
                return
            corner_seg = max(corner_candidates, key=lambda item: item[0])[1]
        moved = min(main_doors, key=lambda op: op.position_along_wall_m)
        main_seg.openings.remove(moved)
        width = min(1.12, max(0.82, corner_seg.length_m - 0.36))
        moved.position_along_wall_m = round(max(0.12, (corner_seg.length_m - width) / 2.0), 3)
        moved.width_m = round(width, 3)
        moved.height_m = max(moved.height_m, 2.55)
        moved.style = "rectangular"
        moved.frame_profile = "bakery_service"
        moved.color_source = "map:pervititch:W-34-36-FIRIN:single-firin-service-entry"
        corner_seg.is_street_facing = True
        corner_seg.is_party_wall = False
        corner_seg.hatch_pattern = "_street"
        corner_seg.openings = [
            op for op in corner_seg.openings
            if not (op.kind == "door" and op.storey_level == 0)
        ]
        corner_seg.openings.append(moved)
        tracker.record(
            zone_pid,
            f"wall[{corner_seg.face}].leftmost_corner_bakery_entry",
            "map+user-correction:pervititch",
            "single Firin street/service entrance belongs on the short diagonal/kinked corner segment; W-36 is internal-only and this is not an Mg./magazine storefront row",
        )

    def _place_explicit_vitrine(self, label: ManualLabel, zone: Zone,
                                segments: list[WallSegment], tracker,
                                zone_pid: str) -> None:
        if label.label == "W-39-1" and zone.id == "camli_vitre_passage":
            tracker.record(
                zone_pid,
                "wall.vitrine",
                "map+photo:pervititch",
                "Camli/Vitre is modeled as top glass roof plus arched fanlight, not a side shop-window panel",
            )
            return
        text = " ".join([zone.id, zone.description, *zone.map_labels]).lower()
        if "vitr" not in text and "cam" not in text and "glaz" not in text:
            return
        preferred_faces = []
        if label.facades.secondary_door and label.facades.secondary_door.zone == zone.id:
            preferred_faces.append(label.facades.secondary_door.face)
        if label.facades.primary_door and label.facades.primary_door.zone == zone.id:
            preferred_faces.append(label.facades.primary_door.face)

        o = PROFILE.openings
        preferred_pool = [
            s for s in segments
            if not s.is_party_wall
            and s.length_m > 1.0
            and preferred_faces
            and s.face in preferred_faces
        ]
        fallback_pool = [
            s for s in segments
            if not s.is_party_wall
            and s.length_m > 1.0
            and s not in preferred_pool
        ]

        placement = None
        for seg in sorted(preferred_pool + fallback_pool, key=lambda s: s.length_m, reverse=True):
            door_ranges = [
                (op.position_along_wall_m, op.position_along_wall_m + op.width_m)
                for op in seg.openings
                if op.kind == "door"
            ]
            slots = _available_opening_slots(seg.length_m, door_ranges)
            slot_placement = _shop_window_placement_from_slots(slots, o.shop_window_w_m)
            if slot_placement is None and door_ranges:
                _move_one_door_to_edge(seg)
                door_ranges = [
                    (op.position_along_wall_m, op.position_along_wall_m + op.width_m)
                    for op in seg.openings
                    if op.kind == "door"
                ]
                slots = _available_opening_slots(seg.length_m, door_ranges)
                slot_placement = _shop_window_placement_from_slots(slots, o.shop_window_w_m)
            if slot_placement is not None:
                pos, width = slot_placement
                placement = (seg, pos, width)
                break
            for start, end in sorted(slots, key=lambda slot: slot[1] - slot[0], reverse=True):
                width = min(o.shop_window_w_m, end - start)
                if width < 0.55:
                    continue
                pos = start + (end - start - width) / 2.0
                placement = (seg, pos, width)
                break
            if placement is not None:
                break
        if placement is None:
            return
        seg, pos, width = placement
        seg.openings.append(Opening(
            kind="shop_window",
            storey_level=0,
            position_along_wall_m=round(pos, 3),
            width_m=round(width, 3),
            height_m=o.shop_window_h_m,
            sill_m=o.shop_window_sill_m,
            style="rectangular",
            frame_profile="moulded",
            color_source=f"map:pervititch:{label.label}:explicit-vitrine",
        ))
        tracker.record(
            zone_pid,
            f"wall[{seg.face}].explicit_vitrine",
            "map:pervititch",
            {"zone": zone.id, "labels": zone.map_labels},
        )

    def _adjust_church_camli_entrance(self, label: ManualLabel, zone: Zone,
                                      segments: list[WallSegment], tracker,
                                      zone_pid: str) -> None:
        if label.label != "W-39-1" or zone.id != "camli_vitre_passage":
            return
        candidates = [
            s for s in segments
            if not s.is_party_wall and s.face in {"W", "S", "E"} and s.length_m > 1.0
        ]
        if not candidates:
            return
        with_doors = [s for s in candidates if any(op.kind == "door" for op in s.openings)]
        seg = max(with_doors or candidates, key=lambda s: s.length_m)

        # Keep only the map/photo-indicated church gate for this Camli passage.
        for other in segments:
            if other is seg:
                continue
            other.openings = [op for op in other.openings if op.kind != "door"]

        if not any(op.kind == "door" for op in seg.openings):
            seg.openings.append(Opening(
                kind="door",
                storey_level=0,
                position_along_wall_m=0.0,
                width_m=1.8,
                height_m=2.45,
                sill_m=0.0,
                style="arched",
                frame_profile="moulded",
                color_source="map+photo:ayia-efimia-church-entrance",
            ))

        for op in seg.openings:
            if op.kind != "door":
                continue
            if seg.length_m > 4.0:
                width = min(2.15, max(1.72, seg.length_m * 0.17))
            else:
                width = min(1.72, max(1.12, seg.length_m - 0.42))
            op.position_along_wall_m = round(max(0.22, (seg.length_m - width) / 2.0), 3)
            op.width_m = round(width, 3)
            op.height_m = 2.45
            op.style = "arched"
            op.frame_profile = "moulded"
            op.color_source = "map+photo:ayia-efimia-camli-entrance-white-double-door"
            break
        tracker.record(
            zone_pid,
            f"wall[{seg.face}].photo_guided_church_door",
            "user-photo:Ayia Efimia entrance",
            "white double door with arched iron/glass fanlight; walls opaque, top roof glass",
        )

    def _place_church_wooden_annex_window(self, label: ManualLabel, zone: Zone,
                                          segments: list[WallSegment], tracker,
                                          zone_pid: str) -> None:
        if label.label != "W-39-1" or zone.id != "wooden_church_edge_annex":
            return
        candidates = [
            s for s in segments
            if not s.is_party_wall and s.face == "W" and s.length_m > 1.25
        ]
        if not candidates:
            candidates = [
                s for s in segments
                if not s.is_party_wall and s.face in {"W", "N"} and s.length_m > 1.25
            ]
        if not candidates:
            return
        seg = max(candidates, key=lambda s: s.length_m)
        if any(op.kind == "window" for op in seg.openings):
            return
        width = min(0.92, max(0.72, seg.length_m * 0.14))
        margin = min(0.55, max(0.28, seg.length_m * 0.08))
        available = seg.length_m - width - margin * 2
        pos = margin + max(0.0, available * 0.45)
        seg.openings.append(Opening(
            kind="window",
            storey_level=0,
            position_along_wall_m=round(pos, 3),
            width_m=round(width, 3),
            height_m=1.25,
            sill_m=1.05,
            style="rectangular",
            frame_profile="barred_wooden_annex",
            color_source="map+photo:ayia-efimia-wooden-annex-single-window",
        ))
        tracker.record(
            zone_pid,
            f"wall[{seg.face}].wooden_annex_single_window",
            "map+photo:Ayia Efimia church edge",
            "single window on the wooden/T. 1 bs. annex beside the Camli entrance",
        )

    def _place_n50_rear_lightwell_windows(self, label: ManualLabel, zone: Zone,
                                          segments: list[WallSegment], tracker,
                                          zone_pid: str) -> None:
        if label.label != "N-52-54-E2" or zone.id != "corner_mass":
            return
        candidates = [
            s for s in segments
            if s.face == "INT"
            and s.length_m > 6.0
            and s.is_party_wall
        ]
        if not candidates:
            return
        # This is the west/rear wall descending toward the N-50 lightwell.
        # It was previously treated as an opaque party wall because the KML
        # footprints nearly touch; the Pervititch crop shows a small open void.
        seg = min(candidates, key=lambda s: (s.start[0] + s.end[0]) * 0.5)
        source = "map:georeference:n50-rear-lightwell-window"
        if any(op.kind == "window" and op.color_source == source for op in seg.openings):
            return

        seg.is_party_wall = False
        seg.is_street_facing = True
        seg.adjacent_height_m = None
        seg.hatch_pattern = None

        o = PROFILE.openings
        width = min(o.upper_window_w_m, max(0.72, seg.length_m * 0.12))
        pos = min(seg.length_m - width - 0.35, max(0.35, seg.length_m * 0.74))
        for level in (1, 2):
            seg.openings.append(Opening(
                kind="window",
                storey_level=level,
                position_along_wall_m=round(pos, 3),
                width_m=round(width, 3),
                height_m=o.upper_window_h_m,
                sill_m=o.upper_window_sill_m,
                style="rectangular",
                pane_layout="2x2",
                has_shutters=False,
                frame_profile="moulded",
                color_source=source,
            ))
        tracker.record(
            zone_pid,
            "wall[rear-west].n50_lightwell_windows",
            "map+georeference:building-entrence-50",
            "one upper window per floor on the rear face looking into the small N-50 lightwell",
        )

    def _place_n50_lower_lightwell_window(self, label: ManualLabel, zone: Zone,
                                          segments: list[WallSegment], tracker,
                                          zone_pid: str) -> None:
        if label.label != "N-50" or zone.id != "south_rear_three_storey_roofed":
            return
        candidates = [
            s for s in segments
            if not s.is_party_wall
            and 1.05 <= s.length_m <= 1.85
        ]
        if not candidates:
            return
        seg = max(candidates, key=lambda s: s.length_m)
        source = "map:georeference:n50-rear-roofed-wing-lightwell-window"
        if any(op.kind == "window" and op.color_source == source for op in seg.openings):
            return
        width = min(0.82, max(0.54, seg.length_m - 0.44))
        seg.openings.append(Opening(
            kind="window",
            storey_level=1,
            position_along_wall_m=round((seg.length_m - width) / 2.0, 3),
            width_m=round(width, 3),
            height_m=1.35,
            sill_m=0.95,
            style="rectangular",
            pane_layout="2x2",
            has_shutters=False,
            frame_profile="moulded",
            color_source=source,
        ))
        tracker.record(
            zone_pid,
            "wall[lightwell].rear_roofed_wing_window",
            "map+georeference:building-entrence-50",
            "single narrow upper window facing the N-50 rear rectangular lightwell on the roofed rear wing",
        )

    def _profile(self, label: ManualLabel, meshes) -> str:
        from collections import Counter
        lines = [f"# {label.label} — Manual Rendering Profile\n"]
        lines.append(f"- parcel_ids: **{', '.join(label.parcel_ids)}**")
        lines.append(f"- verified: **{label.verified}**")
        lines.append(f"- structure_type: {label.structure_type}")
        lines.append(f"- primary_zone_axis: **{label.primary_zone_axis}**")
        lines.append(f"- zones rendered: **{len(meshes)}** / {len(label.zones)}")
        lines.append(f"- total faces: **{sum(len(m.faces) for m in meshes)}**\n")
        lines.append("## Map notes\n")
        lines.append(label.map_notes + "\n")
        lines.append("## Zones\n")
        for z, m in zip(label.zones, meshes):
            roles = Counter(f.semantic_role for f in m.faces)
            lines.append(f"### {z.id}  ({z.material_class}, {z.storeys_above_grade}-storey, "
                         f"{z.roof.shape}/{z.roof.material})")
            lines.append(f"- description: {z.description}")
            lines.append(f"- map_labels: {z.map_labels}")
            lines.append(f"- footprint_fraction: {z.footprint_fraction}")
            lines.append(f"- vertices / faces: {len(m.vertices)} / {len(m.faces)}")
            for role, n in sorted(roles.items(), key=lambda x: -x[1]):
                lines.append(f"  - {role}: {n}")
            lines.append("")
        if label.open_questions:
            lines.append("## Open questions\n")
            for q in label.open_questions:
                lines.append(f"- {q}")
        return "\n".join(lines)

    def _emit_manual_subunit_details(self, label: ManualLabel, building: Building, mesh) -> None:
        if label.label != "S-41-43-45-E16":
            return
        if building.notes.get("zone_id") != "merged_mass":
            return
        total_height = sum(s.height_m for s in building.storeys if not s.is_basement)
        seam_count = 0
        for idx, seg in enumerate(building.wall_segments):
            if seg.face != "S" or seg.length_m < 6.0:
                continue
            door_centers = sorted(
                op.position_along_wall_m + op.width_m / 2.0
                for op in seg.openings
                if op.kind == "door"
            )
            if len(door_centers) >= 3:
                seam_positions = [
                    (door_centers[i] + door_centers[i + 1]) / 2.0
                    for i in range(len(door_centers) - 1)
                ]
            else:
                seam_positions = [seg.length_m / 3.0, 2.0 * seg.length_m / 3.0]
            for n, pos in enumerate(seam_positions):
                _emit_vertical_facade_seam(
                    mesh, seg,
                    pos=max(0.35, min(seg.length_m - 0.35, pos)),
                    z0=0.25,
                    z1=max(0.8, total_height - 0.12),
                    surface_id=f"{building.parcel_id}.subunit_seam.S.{idx}.{n}",
                )
                seam_count += 1
        mesh.metadata["subunit_group"] = "41-43-45-16"
        mesh.metadata["subunit_count"] = 4
        mesh.metadata["subunit_seam_count"] = seam_count


def _zone_wants_vitrine(zone: Zone) -> bool:
    text = " ".join([zone.id, zone.description, *zone.map_labels]).lower()
    return "vitr" in text or "cam" in text or "glaz" in text


N50_REAR_LEFT_UTM = (670358.181, 4539708.674)
N50_FRONT_LEFT_UTM = (670363.529, 4539718.195)
N50_FRONT_SPLIT_LOCAL_Y = 5.46


def _zone_polys_for_label(label: ManualLabel, footprint: Polygon) -> dict[str, Polygon]:
    if label.label == "N-50":
        special = _n50_l_plan_zone_polys(label, footprint)
        if special:
            return special

    zone_polys: dict[str, Polygon] = {}
    for z in label.zones:
        if z.clip_ranges:
            sp = footprint
            for axis, frac in z.clip_ranges:
                sp = split_zone(sp, axis, frac)
                if sp.is_empty:
                    break
        else:
            sp = split_zone(footprint, label.primary_zone_axis, z.footprint_fraction)
        poly = _largest_polygon(sp)
        if poly is not None and poly.area > 1.0:
            zone_polys[z.id] = poly
    return zone_polys


def _n50_l_plan_zone_polys(label: ManualLabel, footprint: Polygon) -> dict[str, Polygon]:
    """Map-specific N-50 L plan.

    The KML outline is a long masonry parcel, but the Pervititch crop shows a
    small right/rear void beside E-4 and N-52/54. The front/north piece is the
    lower flat-roofed mass; the rear/dashed piece is the taller roofed wing.
    """
    l_plan = footprint.difference(Polygon(N50_REAR_LIGHTWELL_UTM).buffer(0)).buffer(0)
    l_plan = _largest_polygon(l_plan) or footprint
    front_cut = _n50_local_band(N50_FRONT_SPLIT_LOCAL_Y, 11.40, -0.25, 4.45)
    front = _largest_polygon(l_plan.intersection(front_cut).buffer(0))
    if front is None or front.area < 1.0:
        return {}

    rear = _largest_polygon(l_plan.difference(front).buffer(0))
    if rear is None or rear.area < 1.0:
        return {}

    out: dict[str, Polygon] = {}
    for z in label.zones:
        if z.id == "north_front_two_storey_flat":
            out[z.id] = front
        elif z.id == "south_rear_three_storey_roofed":
            out[z.id] = rear
    return out


def _n50_local_band(y0: float, y1: float, x0: float, x1: float) -> Polygon:
    return Polygon([
        _n50_local_to_utm(x0, y0),
        _n50_local_to_utm(x1, y0),
        _n50_local_to_utm(x1, y1),
        _n50_local_to_utm(x0, y1),
    ])


def _n50_local_to_utm(x: float, y: float) -> tuple[float, float]:
    fx, fy = N50_REAR_LEFT_UTM
    ax, ay = N50_FRONT_LEFT_UTM
    vx = ax - fx
    vy = ay - fy
    length = math.hypot(vx, vy)
    ux = vy / length
    uy = -vx / length
    vx /= length
    vy /= length
    return (fx + ux * x + vx * y, fy + uy * x + vy * y)


def _largest_polygon(geom) -> Polygon | None:
    if geom.is_empty:
        return None
    if geom.geom_type == "Polygon":
        return geom
    if hasattr(geom, "geoms"):
        polys = [g for g in geom.geoms if g.geom_type == "Polygon" and g.area > 0.5]
        if polys:
            return max(polys, key=lambda g: g.area)
    return None


def _manual_footprint(poly, label: ManualLabel):
    if label.footprint_mode == "n50_lightwell_cut":
        cut = poly.difference(Polygon(N50_REAR_LIGHTWELL_UTM).buffer(0)).buffer(0)
        if cut.is_empty:
            return poly
        if cut.geom_type == "Polygon":
            return cut
        if hasattr(cut, "geoms"):
            polys = [g for g in cut.geoms if g.geom_type == "Polygon" and g.area > 0.5]
            if polys:
                return max(polys, key=lambda g: g.area)
        return poly
    if label.footprint_mode == "minimum_rotated_rectangle":
        return poly.minimum_rotated_rectangle
    return poly


def _available_opening_slots(length_m: float, occupied: list[tuple[float, float]]) -> list[tuple[float, float]]:
    margin = 0.12
    slots: list[tuple[float, float]] = []
    cursor = margin
    for start, end in sorted(occupied):
        free_end = max(cursor, start - margin)
        if free_end - cursor > 0.45:
            slots.append((cursor, free_end))
        cursor = max(cursor, end + margin)
    tail_end = max(cursor, length_m - margin)
    if tail_end - cursor > 0.45:
        slots.append((cursor, tail_end))
    return slots


def _shop_window_placement_from_slots(
    slots: list[tuple[float, float]],
    preferred_width_m: float,
) -> tuple[float, float] | None:
    for start, end in sorted(slots, key=lambda slot: slot[1] - slot[0], reverse=True):
        width = min(preferred_width_m, end - start)
        if width < 0.55:
            continue
        pos = start + (end - start - width) / 2.0
        return pos, width
    return None


def _move_one_door_to_edge(seg: WallSegment) -> None:
    for opening in seg.openings:
        if opening.kind != "door":
            continue
        new_width = min(opening.width_m, 0.8, max(0.55, seg.length_m - 1.0))
        opening.width_m = round(new_width, 3)
        opening.position_along_wall_m = 0.15
        return


def _pt_dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _emit_vertical_facade_seam(
    mesh,
    seg: WallSegment,
    pos: float,
    z0: float,
    z1: float,
    surface_id: str,
) -> None:
    sx, sy = seg.start
    ex, ey = seg.end
    length = math.hypot(ex - sx, ey - sy)
    if length < 0.5 or z1 <= z0:
        return
    ux = (ex - sx) / length
    uy = (ey - sy) / length
    nx = -uy
    ny = ux
    # Match the outward-normal convention used by FacadeBanding and offset a
    # hair forward so the seam reads as a surface detail rather than z-fight.
    outward = 0.045
    half_w = 0.045
    u0 = max(0.05, pos - half_w)
    u1 = min(length - 0.05, pos + half_w)
    p0 = (sx + ux * u0 + nx * outward, sy + uy * u0 + ny * outward, z0)
    p1 = (sx + ux * u0 + nx * outward, sy + uy * u0 + ny * outward, z1)
    p2 = (sx + ux * u1 + nx * outward, sy + uy * u1 + ny * outward, z1)
    p3 = (sx + ux * u1 + nx * outward, sy + uy * u1 + ny * outward, z0)
    mesh.add_quad(
        p0=p0, p1=p1, p2=p2, p3=p3,
        role="WallSurface",
        surface_id=surface_id,
        material_key="trim",
    )
