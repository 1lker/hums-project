"""Wooden facade texture for Class C buildings.

Pervititch yellow/Class C parcels should read as timber-framed/wooden, not as
flat ochre plaster. This adds lightweight facade geometry: horizontal board
seams plus sparse vertical battens, clipped around doors/windows so openings
stay clean.
"""
from __future__ import annotations
import math

from ...common.prd import prd
from ...modeling.building import Building, Opening, WallSegment
from ..mesh_graph import BuildingMesh


BOARD_SPACING = 0.34
BOARD_SEAM_H = 0.035
BATTEN_SPACING = 1.15
BATTEN_W = 0.055
SURFACE_OFFSET = 0.032
MIN_RUN = 0.18


@prd("004", "WoodCladding")
class WoodCladding:
    def emit(self, mesh: BuildingMesh, building: Building) -> None:
        if building.structure_type != "building":
            return
        cls = (building.material_class or "").upper()
        if not cls.startswith("C") or "GLASS" in cls:
            return
        total_height = sum(s.height_m for s in building.storeys if not s.is_basement)
        if total_height <= 0:
            return

        floor_zs = _floor_zs(building)
        for idx, seg in enumerate(building.wall_segments):
            if seg.is_party_wall or not seg.is_street_facing:
                continue
            self._emit_segment_texture(mesh, building.parcel_id, seg, idx, total_height, floor_zs)

    def _emit_segment_texture(
        self,
        mesh: BuildingMesh,
        pid: str,
        seg: WallSegment,
        idx: int,
        total_height: float,
        floor_zs: dict[int, float],
    ) -> None:
        sx, sy = seg.start
        ex, ey = seg.end
        length = math.hypot(ex - sx, ey - sy)
        if length < 0.7:
            return
        ux = (ex - sx) / length
        uy = (ey - sy) / length
        nx, ny = uy, -ux
        nx, ny = -nx, -ny

        holes = [_opening_rect(op, floor_zs) for op in seg.openings]

        def p(u: float, z: float, off: float = SURFACE_OFFSET) -> tuple[float, float, float]:
            return (sx + ux * u + nx * off, sy + uy * u + ny * off, z)

        # Horizontal board seams.
        z = 0.72
        n = 0
        while z < total_height - 0.25:
            z0 = z
            z1 = min(z + BOARD_SEAM_H, total_height)
            blocked = [(u0, u1) for u0, hz0, u1, hz1 in holes if _ranges_overlap(z0, z1, hz0, hz1)]
            for run_idx, (u0, u1) in enumerate(_subtract_ranges(0.12, length - 0.12, blocked)):
                if u1 - u0 < MIN_RUN:
                    continue
                mesh.add_quad(
                    p0=p(u0, z0),
                    p1=p(u0, z1),
                    p2=p(u1, z1),
                    p3=p(u1, z0),
                    role="WoodCladding",
                    surface_id=f"{pid}.wood_board.{seg.face}.{idx}.{n}.{run_idx}",
                    material_key="wood_grain_dark",
                )
            z += BOARD_SPACING
            n += 1

        # Sparse vertical battens/trim pieces, clipped around openings.
        u = 0.45
        k = 0
        while u < length - 0.35:
            u0 = max(0.08, u - BATTEN_W / 2)
            u1 = min(length - 0.08, u + BATTEN_W / 2)
            blocked_z = [(z0, z1) for hu0, z0, hu1, z1 in holes if _ranges_overlap(u0, u1, hu0, hu1)]
            for run_idx, (z0, z1) in enumerate(_subtract_ranges(0.58, total_height - 0.18, blocked_z)):
                if z1 - z0 < 0.28:
                    continue
                mesh.add_quad(
                    p0=p(u0, z0, SURFACE_OFFSET + 0.004),
                    p1=p(u0, z1, SURFACE_OFFSET + 0.004),
                    p2=p(u1, z1, SURFACE_OFFSET + 0.004),
                    p3=p(u1, z0, SURFACE_OFFSET + 0.004),
                    role="WoodCladding",
                    surface_id=f"{pid}.wood_batten.{seg.face}.{idx}.{k}.{run_idx}",
                    material_key="wood_batten",
                )
            u += BATTEN_SPACING
            k += 1


def _floor_zs(building: Building) -> dict[int, float]:
    out: dict[int, float] = {}
    z = 0.0
    for storey in building.storeys:
        if storey.is_basement:
            continue
        out[storey.level] = z
        z += storey.height_m
    return out


def _opening_rect(op: Opening, floor_zs: dict[int, float]) -> tuple[float, float, float, float]:
    u0 = op.position_along_wall_m - 0.08
    u1 = op.position_along_wall_m + op.width_m + 0.08
    z0 = floor_zs.get(op.storey_level, 0.0) + op.sill_m - 0.08
    z1 = z0 + op.height_m + 0.16
    return (u0, z0, u1, z1)


def _ranges_overlap(a0: float, a1: float, b0: float, b1: float) -> bool:
    return not (a1 <= b0 or a0 >= b1)


def _subtract_ranges(start: float, end: float, blocked: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if end <= start:
        return []
    runs = [(start, end)]
    for b0, b1 in sorted(blocked):
        next_runs: list[tuple[float, float]] = []
        for r0, r1 in runs:
            lo = max(r0, b0)
            hi = min(r1, b1)
            if hi <= lo:
                next_runs.append((r0, r1))
                continue
            if lo - r0 > MIN_RUN:
                next_runs.append((r0, lo))
            if r1 - hi > MIN_RUN:
                next_runs.append((hi, r1))
        runs = next_runs
    return runs
