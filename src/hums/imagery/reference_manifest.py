"""PRD-002 · §11b — reference image manifest per parcel.

File layout::

    data/imagery/<parcel_id>/manifest.json
    data/imagery/<parcel_id>/*.jpg|png|...

manifest.json schema::

    {
      "parcel_id": "N-44",
      "images": [
        {"image_id": "n44_streetview_01", "path": "...", "facade": "N",
         "source_url": "...", "captured_date": "YYYY-MM-DD", "aligned": false,
         "notes": "..."}
      ]
    }
"""
from __future__ import annotations
import json
from pathlib import Path

from ..common.prd import prd
from ..modeling.building import ReferenceImage

IMAGERY_ROOT = Path(__file__).resolve().parents[3] / "data" / "imagery"


@prd("002", "§11b ReferenceManifest")
class ReferenceManifest:
    @classmethod
    def load_for(cls, parcel_id: str) -> list[ReferenceImage]:
        mf = IMAGERY_ROOT / parcel_id / "manifest.json"
        if not mf.exists():
            return []
        data = json.loads(mf.read_text())
        return [ReferenceImage(**img) for img in data.get("images", [])]
