from __future__ import annotations

import math
import statistics
from typing import Any

from .model import EvidenceKind, EvidenceTimeline


SCHEMA = "ears.acoustic-counterfactual.v1"


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(statistics.median(values)), 6)


def _mean_continuous_vector(timeline: EvidenceTimeline) -> list[float] | None:
    vectors = [
        item.payload.get("values")
        for item in timeline.evidence
        if item.kind is EvidenceKind.CONTINUOUS_ACOUSTIC_FEATURE
    ]
    vectors = [vector for vector in vectors if isinstance(vector, list) and vector]
    if not vectors:
        return None
    width = len(vectors[0])
    if any(len(vector) != width for vector in vectors):
        return None
    return [
        sum(float(vector[index]) for vector in vectors) / len(vectors)
        for index in range(width)
    ]


def _summary(timeline: EvidenceTimeline) -> dict[str, Any]:
    prosody = [
        item
        for item in timeline.evidence
        if item.kind is EvidenceKind.PROSODIC_OBSERVATION
    ]
    frames = [
        item
        for item in timeline.evidence
        if item.kind is EvidenceKind.ACOUSTIC_FRAME_OBSERVATION
    ]
    f0 = [
        float(item.payload["f0_hz"])
        for item in prosody
        if item.payload.get("f0_hz") is not None
    ]
    prosody_rms = [float(item.payload["rms"]) for item in prosody]
    zcr = [float(item.payload["zero_crossing_rate"]) for item in frames]
    return {
        "source_id": timeline.source_id,
        "duration_ms": round(timeline.duration_ms, 6),
        "median_f0_hz": _median(f0),
        "voiced_fraction": round(len(f0) / len(prosody), 6) if prosody else 0.0,
        "median_rms": _median(prosody_rms),
        "median_zero_crossing_rate": _median(zcr),
        "continuous_feature_count": sum(
            item.kind is EvidenceKind.CONTINUOUS_ACOUSTIC_FEATURE
            for item in timeline.evidence
        ),
    }


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(abs(left - right), 6)


def compare_acoustic_counterfactual(
    left: EvidenceTimeline,
    right: EvidenceTimeline,
    *,
    lexical_control: str | None = None,
) -> dict[str, Any]:
    """Compare two sources without pretending their lexical equivalence is verified."""
    left_summary = _summary(left)
    right_summary = _summary(right)
    left_vector = _mean_continuous_vector(left)
    right_vector = _mean_continuous_vector(right)
    vector_l2 = None
    if left_vector is not None and right_vector is not None:
        if len(left_vector) == len(right_vector):
            vector_l2 = round(
                math.sqrt(
                    sum(
                        (left_value - right_value) ** 2
                        for left_value, right_value in zip(left_vector, right_vector)
                    )
                ),
                6,
            )
    return {
        "schema": SCHEMA,
        "lexical_control": {
            "value": lexical_control,
            "status": (
                "USER_DECLARED_UNVERIFIED"
                if lexical_control is not None
                else "NOT_PROVIDED"
            ),
        },
        "left": left_summary,
        "right": right_summary,
        "absolute_deltas": {
            "median_f0_hz": _delta(
                left_summary["median_f0_hz"],
                right_summary["median_f0_hz"],
            ),
            "voiced_fraction": _delta(
                left_summary["voiced_fraction"],
                right_summary["voiced_fraction"],
            ),
            "median_rms": _delta(
                left_summary["median_rms"],
                right_summary["median_rms"],
            ),
            "median_zero_crossing_rate": _delta(
                left_summary["median_zero_crossing_rate"],
                right_summary["median_zero_crossing_rate"],
            ),
            "mean_continuous_vector_l2": vector_l2,
        },
        "claim_ceiling": "ACOUSTIC_DIFFERENCE_ONLY_NOT_SEMANTIC_REASONING",
    }
