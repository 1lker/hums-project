"""PRD-001 · Data Foundation — pipeline orchestrator.

Pipeline pattern: each step is idempotent and owns its own output artefact.
Run via ``python -m hums prd001`` or ``python -m hums.pipelines.prd001_data_foundation``.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..common.paths import RAW
from ..common.prd import prd
from ..coverage.matcher import CoverageMatcher
from ..parsing.excel.register_assembler import RegisterAssembler
from ..parsing.footprints.builder import FootprintBuilder


@dataclass
class Prd001Result:
    parcels: int
    footprints_parcel: int
    footprints_non_parcel: int
    has_block: bool
    parcels_matched: int


@prd("001", "§6 orchestrator")
class Prd001Pipeline:
    def run(self) -> Prd001Result:
        parcels = RegisterAssembler().build_and_persist()
        foot_counts = FootprintBuilder(RAW).build_and_persist()
        cov = CoverageMatcher().run()
        return Prd001Result(
            parcels=len(parcels),
            footprints_parcel=foot_counts.get("parcel", 0),
            footprints_non_parcel=foot_counts.get("non_parcel", 0),
            has_block=foot_counts.get("block", 0) > 0,
            parcels_matched=cov["parcels_matched"],
        )


def main() -> None:
    r = Prd001Pipeline().run()
    print(f"[PRD-001] parcels={r.parcels}  footprints={r.footprints_parcel}  "
          f"non_parcel={r.footprints_non_parcel}  block={'yes' if r.has_block else 'NO'}  "
          f"coverage={r.parcels_matched}/{r.parcels}")


if __name__ == "__main__":
    main()
