"""PRD-003 — fan triangulation helper shared by glTF + IFC backends.

Our mesh graph uses N-gons (quads and polygons). glTF requires triangles and
IFC 4.3's IfcTriangulatedFaceSet does too. Fan triangulation is adequate for
convex quads/polys, which is what our geometry emits.
"""
from __future__ import annotations


def fan(indices: list[int]) -> list[tuple[int, int, int]]:
    if len(indices) < 3:
        return []
    out: list[tuple[int, int, int]] = []
    v0 = indices[0]
    for i in range(1, len(indices) - 1):
        out.append((v0, indices[i], indices[i + 1]))
    return out
