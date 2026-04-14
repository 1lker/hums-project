"""PRD-001 · Data Foundation §6 step 3 — cross-match parcels ↔ footprints.

Produces the coverage_report.md that gates PRD-002.
"""
from __future__ import annotations
import json
from collections import defaultdict

from ..common.paths import (
    PARCELS_JSON,
    FOOTPRINTS_GEOJSON,
    NON_PARCEL_FOOTPRINTS_GEOJSON,
    BLOCK_GEOJSON,
    COVERAGE_REPORT,
)
from ..common.prd import prd


@prd("001", "§4 coverage_report.md")
class CoverageMatcher:
    def run(self) -> dict:
        parcels = json.loads(PARCELS_JSON.read_text())
        foot_fc = json.loads(FOOTPRINTS_GEOJSON.read_text())
        foot_features = foot_fc["features"]
        non_features = json.loads(NON_PARCEL_FOOTPRINTS_GEOJSON.read_text())["features"] if NON_PARCEL_FOOTPRINTS_GEOJSON.exists() else []
        has_block = BLOCK_GEOJSON.exists()

        by_num = _index_parcels(parcels)
        matched, unmatched = self._match(foot_features, by_num)

        # persist enriched features
        FOOTPRINTS_GEOJSON.write_text(json.dumps(foot_fc, indent=2))

        missing = [p for p in parcels if p["parcel_id"] not in matched]
        self._write_report(parcels, foot_features, non_features, has_block, matched, missing, unmatched)
        return {
            "parcels_total": len(parcels),
            "parcels_matched": len(matched),
            "parcels_missing": len(missing),
            "footprints_total": len(foot_features),
        }

    def _match(self, features, by_num):
        matched_ids: set[str] = set()
        unmatched = []
        for f in features:
            ids: list[str] = []
            override = f["properties"].get("parcel_ids_override") or []
            if override:
                ids = list(override)
            else:
                for n in (f["properties"].get("parcel_numbers") or []):
                    key = str(int(n)) if n.isdigit() else n
                    ids.extend(by_num.get(key, []))
            if ids:
                f["properties"]["parcel_ids_matched"] = sorted(set(ids))
                matched_ids.update(ids)
            else:
                unmatched.append(f)
        return matched_ids, unmatched

    def _write_report(self, parcels, foot_features, non_features, has_block, matched, missing, unmatched):
        lines: list[str] = ["# PRD-001 Coverage Report\n"]
        lines.append(f"- Excel parcels: **{len(parcels)}**")
        lines.append(f"- Parcel footprints traced: **{len(foot_features)}**")
        lines.append(f"- Non-parcel footprints: **{len(non_features)}**")
        lines.append(f"- Block outline: **{'yes' if has_block else 'NO'}**")
        lines.append(f"- Parcels WITH footprint: **{len(matched)} / {len(parcels)}**")
        lines.append(f"- Parcels MISSING footprint: **{len(missing)}**\n")

        lines.append("## Parcels missing a footprint (trace or stub in PRD-002)\n")
        lines.append("| parcel_id | number | zone | street | material | storeys |")
        lines.append("|---|---|---|---|---|---|")
        for p in missing:
            lines.append("| {id} | {num} | {zone} | {street} | {mat} | {st} |".format(
                id=p["parcel_id"],
                num=p.get("parcel_number") or "",
                zone=p.get("zone") or "",
                street=p.get("street_facing") or "",
                mat=(p["material"] or {}).get("decoded") or "",
                st=(p["storeys"] or {}).get("raw") or "",
            ))

        lines.append("\n## Footprints without Excel match\n")
        if unmatched:
            lines.append("| source_file | parcel_numbers | area_m2 |")
            lines.append("|---|---|---|")
            for f in unmatched:
                pr = f["properties"]
                lines.append(f"| {pr['source_file']} | {pr.get('parcel_numbers')} | {pr['area_m2']} |")
        else:
            lines.append("_None._")

        lines.append("\n## Non-parcel features\n")
        for f in non_features:
            pr = f["properties"]
            lines.append(f"- **{pr.get('kind')}** — `{pr.get('name')}` ({pr.get('area_m2')} m²)")

        # Explicit audit: parcels backed by more than one traced footprint.
        # Each one MUST become multiple Building volumes downstream (PRD-002
        # used to silently drop the extras — a real bug).
        from collections import Counter
        pid_counts: Counter[str] = Counter()
        for f in foot_features:
            for pid in f["properties"].get("parcel_ids_matched") or []:
                pid_counts[pid] += 1
        multi = {pid: n for pid, n in pid_counts.items() if n > 1}
        if multi:
            lines.append("\n## Multi-footprint parcels (each must emit N buildings)\n")
            lines.append("| parcel_id | footprints |")
            lines.append("|---|---|")
            for pid, n in sorted(multi.items()):
                lines.append(f"| {pid} | {n} |")

        COVERAGE_REPORT.write_text("\n".join(lines))


def _index_parcels(parcels) -> dict[str, list[str]]:
    by_num: dict[str, list[str]] = defaultdict(list)
    for p in parcels:
        raw = (p.get("parcel_number") or "").strip("()").strip()
        if not raw:
            continue
        head = raw.split("/")[0]
        by_num[head].append(p["parcel_id"])
        if head.isdigit():
            by_num[str(int(head))].append(p["parcel_id"])
    return by_num
