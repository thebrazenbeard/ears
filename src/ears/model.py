from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import math
from types import MappingProxyType
from typing import Any, Mapping


class EvidenceKind(StrEnum):
    WAVEFORM_REFERENCE = "WAVEFORM_REFERENCE"
    ACOUSTIC_FRAME_OBSERVATION = "ACOUSTIC_FRAME_OBSERVATION"
    CONTINUOUS_SPEECH_FEATURE = "CONTINUOUS_SPEECH_FEATURE"
    DISCRETE_SPEECH_UNIT = "DISCRETE_SPEECH_UNIT"
    PHONE_HYPOTHESIS = "PHONE_HYPOTHESIS"
    PROSODIC_OBSERVATION = "PROSODIC_OBSERVATION"
    NON_SPEECH_EVENT = "NON_SPEECH_EVENT"
    SPEAKER_TURN_EVENT = "SPEAKER_TURN_EVENT"
    TRANSCRIPT_HYPOTHESIS = "TRANSCRIPT_HYPOTHESIS"
    INTERPRETIVE_HYPOTHESIS = "INTERPRETIVE_HYPOTHESIS"


@dataclass(frozen=True, slots=True)
class AudioSpan:
    source_id: str
    start_ms: float
    end_ms: float
    channel: int = 0

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if not math.isfinite(self.start_ms) or not math.isfinite(self.end_ms):
            raise ValueError("audio span values must be finite")
        if self.start_ms < 0 or self.end_ms < self.start_ms:
            raise ValueError("invalid audio span")
        if self.channel < 0:
            raise ValueError("channel must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "start_ms": round(self.start_ms, 6),
            "end_ms": round(self.end_ms, 6),
            "channel": self.channel,
        }


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    span: AudioSpan
    kind: EvidenceKind
    producer: str
    producer_version: str
    payload: Mapping[str, Any]
    quality: float | None = None
    derivation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.producer or not self.producer_version:
            raise ValueError("evidence identity and producer are required")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "derivation", tuple(self.derivation))

    def to_dict(self) -> dict[str, Any]:
        data = {
            "evidence_id": self.evidence_id,
            "span": self.span.to_dict(),
            "kind": self.kind.value,
            "producer": self.producer,
            "producer_version": self.producer_version,
            "payload": dict(self.payload),
            "derivation": list(self.derivation),
        }
        if self.quality is not None:
            data["quality"] = self.quality
        return data


@dataclass(slots=True)
class EvidenceTimeline:
    source_id: str
    source_name: str
    sample_rate: int
    channels: int
    duration_ms: float
    evidence: list[EvidenceItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.sample_rate <= 0 or self.channels <= 0:
            raise ValueError("sample_rate and channels must be positive")
        if not math.isfinite(self.duration_ms) or self.duration_ms < 0:
            raise ValueError("duration_ms must be finite and non-negative")

    def add(self, item: EvidenceItem) -> None:
        if item.span.source_id != self.source_id:
            raise ValueError("evidence belongs to a different source")
        if item.span.end_ms > self.duration_ms + 1e-6:
            raise ValueError("evidence extends beyond source duration")
        if item.span.channel >= self.channels:
            raise ValueError("evidence channel does not exist")
        self.evidence.append(item)

    def ordered(self) -> list[EvidenceItem]:
        return sorted(
            self.evidence,
            key=lambda item: (
                item.span.start_ms,
                item.span.end_ms,
                item.span.channel,
                item.kind.value,
                item.evidence_id,
            ),
        )

    def kind_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.evidence:
            counts[item.kind.value] = counts.get(item.kind.value, 0) + 1
        return dict(sorted(counts.items()))