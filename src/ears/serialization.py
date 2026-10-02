from __future__ import annotations

import json
from pathlib import Path

from .model import EvidenceTimeline


SCHEMA = "ears.evidence-timeline.v1"


def _json(data: object) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def write_artifact(
    timeline: EvidenceTimeline,
    out_dir: str | Path,
) -> tuple[Path, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema": SCHEMA,
        "source": {
            "source_id": timeline.source_id,
            "source_name": timeline.source_name,
            "sample_rate": timeline.sample_rate,
            "channels": timeline.channels,
            "duration_ms": round(timeline.duration_ms, 6),
        },
        "evidence_count": len(timeline.evidence),
        "evidence_kind_counts": timeline.kind_counts(),
        "raw_audio_copied": False,
        "transcript_required": False,
        "source_trust": "UNTRUSTED_AUDIO_CONTENT",
        "control_authority": "NONE",
    }
    manifest_path = target / "manifest.json"
    evidence_path = target / "evidence.jsonl"

    manifest_path.write_text(_json(manifest) + "\n", encoding="utf-8")
    evidence_path.write_text(
        "".join(
            _json(item.to_dict()) + "\n"
            for item in timeline.ordered()
        ),
        encoding="utf-8",
    )
    return manifest_path, evidence_path