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
from ..modeling.opening_placer import DoorPlacer, ShopWindowPlacer, UpperWindowPlacer
from ..modeling.wall_segmenter import WallSegmenter
from ..render.backends.gltf_backend import GltfBackend
from ..render.building_geometry_builder import BuildingGeometryBuilder
from ..render.scene_assembler import SceneAssembler


OUT_ROOT = PROJECT_ROOT / "output" / "buildings"


@prd("005", "ManualRenderer")
class ManualRenderer:
    def render(self, label_key: str) -> Path:
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
            party_index.register(f"{label.label}.{zid}", poly)
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
            meshes.append(mesh)

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
                return shape(feat["geometry"])
        for feat in fc["features"]:
            matched = feat["properties"].get("parcel_ids_matched") or []
            if any(pid in matched for pid in label.parcel_ids):
                return shape(feat["geometry"])
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
        segments = segmenter.segment(local_ring, sub_poly, thickness, parcel_id=zone_pid)

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

    def _place_zone_openings(self, label: ManualLabel, zone: Zone,
                             segments: list[WallSegment], tracker,
                             zone_pid: str) -> None:
        """Run the usual placers on non-party walls, respecting manual hints."""
        ctx = {
            "_structure_type": "building",
            "ground_floor": {
                "code": "Mg." if zone.ground_floor_use in ("shop", "bakery", "magazine") else "",
                "use": zone.ground_floor_use,
            },
            "openings": {
                "primary_door_face": label.facades.primary_door.face
                                      if (label.facades.primary_door and
                                          label.facades.primary_door.zone == zone.id)
                                      else None,
            },
        }
        storeys_proxy = [Storey(level=i, height_m=h)
                          for i, h in enumerate(zone.storey_heights_m)]
        for placer in (DoorPlacer(), ShopWindowPlacer(), UpperWindowPlacer()):
            placer.place(segments, storeys_proxy, ctx, zone_pid, tracker)

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
