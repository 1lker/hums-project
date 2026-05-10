"""CLI entrypoint — dispatches to PRD pipelines.

Usage:
    python -m hums prd001         # data foundation
    (future: prd002, prd003, ...)
"""
from __future__ import annotations
import sys

from .imagery.image_ingest import ingest as imagery_ingest
from .pipelines.prd001_data_foundation import Prd001Pipeline
from .pipelines.prd002_buildings import Prd002Pipeline
from .pipelines.prd003_geometry import Prd003Pipeline


PIPELINES = {
    "prd001": Prd001Pipeline,
    "prd002": Prd002Pipeline,
    "prd003": Prd003Pipeline,
}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        _usage()
        return 2
    cmd = argv[1]
    if cmd in PIPELINES:
        PIPELINES[cmd]().run()
        return 0
    if cmd == "render-building":
        if len(argv) < 3:
            print("usage: python -m hums render-building <parcel_id>", file=sys.stderr)
            return 2
        from .pipelines.render_building import render_building
        render_building(argv[2])
        return 0
    if cmd == "render-manual":
        if len(argv) < 3:
            print("usage: python -m hums render-manual <label>", file=sys.stderr)
            return 2
        from .pipelines.render_manual import ManualRenderer
        ManualRenderer().render(argv[2])
        return 0
    if cmd == "diagnostic-map":
        from .render.reports.diagnostic_map import render
        p = render()
        print(f"wrote {p}")
        return 0
    if cmd == "imagery-ingest":
        if len(argv) < 3:
            print("usage: python -m hums imagery-ingest <parcel_id>", file=sys.stderr)
            return 2
        imagery_ingest(argv[2])
        return 0
    _usage()
    return 2


def _usage() -> None:
    print(f"usage: python -m hums <{'|'.join(PIPELINES)}|imagery-ingest <parcel_id>>",
          file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
