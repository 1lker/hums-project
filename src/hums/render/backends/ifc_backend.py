"""PRD-003 · §7 — IFC 4.3 writer (ifcopenshell).

Minimal but valid IFC 4.3 scene:
  IfcProject → IfcSite (Block 147) → IfcBuilding (per parcel) → IfcBuildingStorey
  → building elements (IfcWall, IfcRoof, IfcWindow, IfcDoor, IfcSlab).

Each element's body is an IfcTriangulatedFaceSet built from our mesh graph.
We emit per-role elements rather than a single IfcProxy so downstream tools
see "walls, roofs, windows" the way heritage-BIM pipelines expect.
"""
from __future__ import annotations
import math
from pathlib import Path

import ifcopenshell
from ifcopenshell import api, guid

from ...common.prd import prd
from ..mesh_graph import BuildingMesh, Face, SceneGraph
from ._triangulate import fan

# IFC element type per semantic role.
ROLE_TO_IFC = {
    "WallSurface": ("IfcWall", "SOLIDWALL"),
    "RoofSurface": ("IfcRoof", "FLAT_ROOF"),   # overridden per-building below
    "GroundSurface": ("IfcSlab", "BASESLAB"),
    "FloorSurface": ("IfcSlab", "FLOOR"),
    "Window": ("IfcWindow", "WINDOW"),
    "Door": ("IfcDoor", "DOOR"),
    "Chimney": ("IfcChimney", "NOTDEFINED"),
    "Skylight": ("IfcWindow", "SKYLIGHT"),
    "MonumentBody": ("IfcBuildingElementProxy", "NOTDEFINED"),
    "ClosureSurface": ("IfcVirtualElement", "NOTDEFINED"),
    "OuterCeilingSurface": ("IfcCovering", "CEILING"),
    "InteriorWallSurface": ("IfcWall", "MOVABLE"),
}


@prd("003", "§7 IfcBackend")
class IfcBackend:
    SCHEMA = "IFC4X3"

    def export_scene(self, scene: SceneGraph, out_path: Path) -> None:
        model = api.run("project.create_file", version=self.SCHEMA)
        project = api.run("root.create_entity", model, ifc_class="IfcProject", name="Pervititch Block 147")
        api.run("unit.assign_unit", model, length={"is_metric": True, "raw": "METERS"})
        ctx = api.run("context.add_context", model, context_type="Model")
        body = api.run("context.add_context", model, context_type="Model",
                       context_identifier="Body", target_view="MODEL_VIEW", parent=ctx)

        site = api.run("root.create_entity", model, ifc_class="IfcSite", name="Block 147")
        api.run("aggregate.assign_object", model, products=[site], relating_object=project)

        placements = {p["parcel_id"]: p for p in scene.metadata.get("placements", [])}

        for mesh in scene.buildings:
            self._add_building(model, site, body, mesh, placements.get(mesh.parcel_id, {}))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        model.write(str(out_path))

    def export_building(self, mesh: BuildingMesh, out_path: Path) -> None:
        scene = SceneGraph(buildings=[mesh], block_centroid_utm=(0.0, 0.0),
                           metadata={"placements": [
                               {"parcel_id": mesh.parcel_id, "translation": [0, 0, 0], "rotation_deg_z": 0.0}
                           ]})
        self.export_scene(scene, out_path)

    # -- helpers --------------------------------------------------------------
    def _add_building(self, model, site, body_ctx, mesh: BuildingMesh, placement: dict) -> None:
        if not mesh.vertices or not mesh.faces:
            return
        bldg = api.run("root.create_entity", model, ifc_class="IfcBuilding", name=mesh.parcel_id)
        api.run("aggregate.assign_object", model, products=[bldg], relating_object=site)
        storey = api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name=f"{mesh.parcel_id}.storey")
        api.run("aggregate.assign_object", model, products=[storey], relating_object=bldg)

        # Local placement for this building
        tx, ty, tz = placement.get("translation", [0, 0, 0])
        theta = math.radians(placement.get("rotation_deg_z", 0.0))
        c, s = math.cos(theta), math.sin(theta)
        ifc_placement = model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=model.create_entity(
                "IfcAxis2Placement3D",
                Location=model.create_entity("IfcCartesianPoint", Coordinates=[tx, ty, tz]),
                Axis=model.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
                RefDirection=model.create_entity("IfcDirection", DirectionRatios=[c, s, 0.0]),
            ),
        )
        bldg.ObjectPlacement = ifc_placement

        # Pset with Pervititch-specific attrs
        pset = api.run("pset.add_pset", model, product=bldg, name="Pervititch_Attrs")
        api.run("pset.edit_pset", model, pset=pset, properties={
            "material_class": mesh.metadata.get("material_class") or "",
            "structure_type": mesh.metadata.get("structure_type") or "building",
            "footprint_source": mesh.metadata.get("footprint_source") or "",
            "notes_json": repr(mesh.metadata.get("notes") or {}),
        })

        # Group faces by role → one IFC element per role-group
        groups: dict[str, list[Face]] = {}
        for f in mesh.faces:
            groups.setdefault(f.semantic_role, []).append(f)

        for role, faces in groups.items():
            ifc_class, ptype = ROLE_TO_IFC.get(role, ("IfcBuildingElementProxy", "NOTDEFINED"))
            if role == "RoofSurface" and mesh.metadata.get("roof_shape") == "gable":
                ptype = "GABLE_ROOF"
            element = api.run("root.create_entity", model, ifc_class=ifc_class,
                              name=f"{mesh.parcel_id}.{role}")
            try:
                element.PredefinedType = ptype
            except Exception:
                pass
            api.run("spatial.assign_container", model, products=[element], relating_structure=storey)
            rep = self._triangulated_rep(model, body_ctx, mesh, faces)
            if rep is not None:
                element.Representation = model.create_entity(
                    "IfcProductDefinitionShape", Representations=[rep])

    def _triangulated_rep(self, model, body_ctx, mesh: BuildingMesh, faces: list[Face]):
        # Gather unique vertex indices used by these faces
        local_map: dict[int, int] = {}
        points: list[list[float]] = []

        def local(g: int) -> int:
            if g not in local_map:
                local_map[g] = len(points) + 1   # IFC indices are 1-based
                v = mesh.vertices[g]
                points.append([v.x, v.y, v.z])
            return local_map[g]

        tris: list[list[int]] = []
        for f in faces:
            for t in fan(f.vertices):
                tris.append([local(t[0]), local(t[1]), local(t[2])])

        if not tris:
            return None

        coords = model.create_entity("IfcCartesianPointList3D", CoordList=points)
        face_set = model.create_entity(
            "IfcTriangulatedFaceSet",
            Coordinates=coords,
            CoordIndex=tris,
            Closed=False,
        )
        return model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body_ctx,
            RepresentationIdentifier="Body",
            RepresentationType="Tessellation",
            Items=[face_set],
        )
