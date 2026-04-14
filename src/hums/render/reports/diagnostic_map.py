"""PRD-004 · diagnostic 2D SVG of block 147.

Draws the block outline + every parcel / stub / church footprint + labels so
you can eyeball placement without a 3D viewer. Output: output/reports/block_map.svg.
"""
from __future__ import annotations
import json
from pathlib import Path

from shapely.geometry import shape

from ...common.paths import (
    BLOCK_GEOJSON, FOOTPRINTS_GEOJSON, NON_PARCEL_FOOTPRINTS_GEOJSON, PARSED,
)
from ...common.prd import prd

STUBS_GEOJSON = PARSED / "stubs.geojson"
OUT = Path("output/reports/block_map.svg")


PALETTE = {
    "building": "#E8D49E",
    "stub":     "#F4E8C8",
    "church":   "#E8A598",
    "fountain": "#B8CDDC",
    "magazine": "#D5B08A",
}


@prd("004", "DiagnosticMap")
def render(width_px: int = 1800) -> Path:
    block = _load_polygon(BLOCK_GEOJSON)
    if block is None:
        raise RuntimeError("No block outline available")

    minx, miny, maxx, maxy = block.buffer(8).bounds
    scale = width_px / (maxx - minx)
    height_px = int((maxy - miny) * scale) + 2

    def to_svg(xy):
        x, y = xy
        sx = (x - minx) * scale
        sy = height_px - (y - miny) * scale
        return f"{sx:.2f},{sy:.2f}"

    svg: list[str] = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" '
               f'height="{height_px}" viewBox="0 0 {width_px} {height_px}" '
               f'style="font-family: -apple-system, sans-serif; background: #f4efe4;">')
    svg.append(_grid_hint(width_px, height_px, minx, miny, scale))

    # Block outline
    svg.append(_poly_path(block, to_svg, stroke="#333", fill="#fffbf0",
                          stroke_width=3, dash="4 4"))

    # Parcels + stubs
    feats = json.loads(FOOTPRINTS_GEOJSON.read_text())["features"]
    stubs_fc = json.loads(STUBS_GEOJSON.read_text()) if STUBS_GEOJSON.exists() else {"features": []}
    non_feats = json.loads(NON_PARCEL_FOOTPRINTS_GEOJSON.read_text())["features"] \
        if NON_PARCEL_FOOTPRINTS_GEOJSON.exists() else []

    for f in feats:
        poly = shape(f["geometry"])
        label = "/".join(f["properties"].get("parcel_ids_matched") or
                         [f["properties"].get("source_file", "?")])
        svg.append(_poly_path(poly, to_svg, stroke="#5a4a3a",
                              fill=PALETTE["building"], stroke_width=1.2))
        svg.append(_label(poly, label, to_svg, scale))

    for f in stubs_fc.get("features", []):
        poly = shape(f["geometry"])
        label = f["properties"].get("parcel_id", "stub")
        svg.append(_poly_path(poly, to_svg, stroke="#8a7a5a",
                              fill=PALETTE["stub"], stroke_width=1.0, dash="2 2"))
        svg.append(_label(poly, f"{label} (stub)", to_svg, scale, italic=True))

    for f in non_feats:
        poly = shape(f["geometry"])
        kind = f["properties"].get("kind") or "church"
        label = f["properties"].get("name") or kind
        fill = PALETTE.get(kind, PALETTE["church"])
        svg.append(_poly_path(poly, to_svg, stroke="#6a3a2a", fill=fill,
                              stroke_width=1.2, opacity=0.65))
        svg.append(_label(poly, kind.upper(), to_svg, scale, italic=True))

    # Compass
    svg.append(_compass(width_px))

    # Legend
    svg.append(_legend(width_px, height_px))

    svg.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(svg))
    return OUT


def _load_polygon(path):
    if not path.exists():
        return None
    feats = json.loads(path.read_text()).get("features", [])
    return shape(feats[0]["geometry"]) if feats else None


def _poly_path(poly, to_svg, *, stroke="#000", fill="none",
               stroke_width=1.0, dash=None, opacity=1.0):
    coords = list(poly.exterior.coords)
    pts = " ".join(to_svg(p) for p in coords)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{stroke_width}" fill-opacity="{opacity}"{dash_attr}/>')


def _label(poly, text, to_svg, scale, italic=False):
    c = poly.centroid
    x, y = to_svg((c.x, c.y)).split(",")
    font_style = ' font-style="italic"' if italic else ""
    size = max(8, min(14, int(scale / 8)))
    return (f'<text x="{x}" y="{y}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="{size}"{font_style} '
            f'fill="#222">{text}</text>')


def _grid_hint(w, h, minx, miny, scale):
    # 5m grid gridlines for scale reference
    out = [f'<rect width="{w}" height="{h}" fill="#f4efe4"/>']
    # Minor grid every 5m
    step = int(5 * scale)
    for i in range(0, w, step):
        out.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{h}" '
                   f'stroke="#e0d8c4" stroke-width="0.5"/>')
    for j in range(0, h, step):
        out.append(f'<line x1="0" y1="{j}" x2="{w}" y2="{j}" '
                   f'stroke="#e0d8c4" stroke-width="0.5"/>')
    out.append(f'<text x="{w - 6}" y="{h - 6}" text-anchor="end" '
               f'font-size="10" fill="#888">grid: 5 m</text>')
    return "\n".join(out)


def _compass(w):
    cx, cy = w - 60, 60
    return (
        f'<g transform="translate({cx},{cy})">'
        f'<circle r="28" fill="#fffbf0" stroke="#555"/>'
        f'<path d="M0,-20 L6,10 L0,4 L-6,10 Z" fill="#c54"/>'
        f'<text x="0" y="-14" text-anchor="middle" font-size="10" fill="#333">N</text>'
        f'</g>'
    )


def _legend(w, h):
    y = h - 100
    items = [
        ("traced building", PALETTE["building"]),
        ("stub (inferred)", PALETTE["stub"]),
        ("church",          PALETTE["church"]),
        ("çeşme fountain",  PALETTE["fountain"]),
        ("magazine",        PALETTE["magazine"]),
    ]
    parts = [f'<g transform="translate(20,{y})">']
    for i, (name, color) in enumerate(items):
        parts.append(f'<rect x="0" y="{i * 18}" width="14" height="14" '
                     f'fill="{color}" stroke="#333"/>')
        parts.append(f'<text x="20" y="{i * 18 + 11}" font-size="11">{name}</text>')
    parts.append("</g>")
    return "\n".join(parts)


if __name__ == "__main__":
    p = render()
    print(f"wrote {p}")
