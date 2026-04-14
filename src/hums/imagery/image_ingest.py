"""PRD-002 · §11b — scaffold manifest entries for dropped photos.

Usage::

    python -m hums imagery-ingest N-44

Scans ``data/imagery/N-44/`` for image files not already referenced in
``manifest.json`` and appends stub entries for them. User fills in facade,
source_url, and captured_date afterward.
"""
from __future__ import annotations
import json
from pathlib import Path

from .reference_manifest import IMAGERY_ROOT

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def ingest(parcel_id: str) -> Path:
    folder = IMAGERY_ROOT / parcel_id
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.json"

    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "parcel_id": parcel_id, "images": [],
    }
    known = {img["path"] for img in manifest["images"]}

    new_entries = 0
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        rel = p.name
        if rel in known:
            continue
        manifest["images"].append({
            "image_id": f"{parcel_id}_{p.stem}".lower(),
            "path": rel,
            "facade": None,
            "source_url": None,
            "captured_date": None,
            "aligned": False,
            "notes": "TODO: fill facade + source_url",
        })
        new_entries += 1

    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"[imagery-ingest] {parcel_id}: {new_entries} new entries → {manifest_path}")
    return manifest_path
