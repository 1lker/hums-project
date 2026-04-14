"""PRD-001 · Data Foundation — shared filesystem anchors.

Single source of truth for project-relative paths. Every module imports from
here rather than recomputing.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW = PROJECT_ROOT / "data" / "raw"
RAW_KML = RAW / "kml"
RAW_SHP = RAW / "shp"
RAW_RASTER = RAW / "raster"
RAW_EXCEL = RAW / "excel"
RAW_QGIS = RAW / "qgis"

PARSED = PROJECT_ROOT / "data" / "parsed"
IMAGERY = PROJECT_ROOT / "data" / "imagery"
PRDS = PROJECT_ROOT / "PRDs"

EXCEL_REGISTER = RAW_EXCEL / "Block147_Pervititch_BIM_v3_FINAL (1).xlsx"

PARCELS_JSON = PARSED / "parcels.json"
FOOTPRINTS_GEOJSON = PARSED / "footprints.geojson"
NON_PARCEL_FOOTPRINTS_GEOJSON = PARSED / "non_parcel_footprints.geojson"
BLOCK_GEOJSON = PARSED / "block.geojson"
COVERAGE_REPORT = PARSED / "coverage_report.md"


def ensure_parsed_dir() -> None:
    PARSED.mkdir(parents=True, exist_ok=True)
