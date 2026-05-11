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

from shapely.geometry import shape

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

        # Pre-compute all zone sub-polygons.
        zone_polys: dict[str, "object"] = {}
        for z in label.zones:
            sp = split_zone(footprint, label.primary_zone_axis, z.footprint_fraction)
            if not sp.is_empty and sp.geom_type == "Polygon" and sp.area > 1.0:
                zone_polys[z.id] = sp

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
        self._place_explicit_vitrine(label, zone, segments, tracker, zone_pid)
        UpperWindowPlacer().place(segments, storeys_proxy, ctx, zone_pid, tracker)

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

    def _place_explicit_vitrine(self, label: ManualLabel, zone: Zone,
                                segments: list[WallSegment], tracker,
                                zone_pid: str) -> None:
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


def _manual_footprint(poly, label: ManualLabel):
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
