"""PRD-002 · §5 — Excel roof row → RoofDescriptor."""
from __future__ import annotations

from ..common.prd import prd
from ..common.heritage_profile import PROFILE
from .building import RoofDescriptor
from .assumption_tracker import AssumptionTracker


@prd("002", "§5 RoofDescriptor")
class RoofDescriptorBuilder:
    def build(self, roof_excel: dict, parcel_id: str, tracker: AssumptionTracker) -> RoofDescriptor:
        shape_raw = (roof_excel.get("shape") or "").lower()
        code = (roof_excel.get("material_code") or "").upper()

        material = "unknown"
        pitch = PROFILE.roofs.tile_TR_deg
        pitch_source = "assumption:pervititch_1923"

        if "VF" in code:
            material, pitch = "vault_VF", PROFILE.roofs.vault_flat_deg
        elif "VT" in code:
            material, pitch = "vault_VT", PROFILE.roofs.vault_flat_deg
        elif code.startswith("T") and "TR" not in code:
            material, pitch = "sheet_metal_T", PROFILE.roofs.sheet_metal_T_deg
        elif "TR" in code or "TILE" in code:
            material, pitch = "tile_TR", PROFILE.roofs.tile_TR_deg

        if any(w in shape_raw for w in ("complex", "multi")):
            shape = "complex_pitched"
        elif "mansard" in shape_raw:
            shape = "mansard"
        elif "hip" in shape_raw:
            shape = "hip"
        elif "gable" in shape_raw:
            shape = "gable"
        elif "flat" in shape_raw or material.startswith("vault"):
            shape = "vault_flat" if material.startswith("vault") else "flat"
        else:
            shape = "gable"
            tracker.assume(parcel_id, "roof.shape", shape, "Excel shape unrecognized; default gable")

        tracker.record(parcel_id, "roof.material", "excel" if code else pitch_source, material)
        tracker.record(parcel_id, "roof.pitch_deg", pitch_source, pitch)

        return RoofDescriptor(
            shape=shape,
            material=material,  # type: ignore[arg-type]
            pitch_deg=pitch,
            slope_direction=roof_excel.get("slope_direction"),
            has_chimney=bool(roof_excel.get("has_chimney")),
            has_skylight=bool(roof_excel.get("has_skylight")),
        )
