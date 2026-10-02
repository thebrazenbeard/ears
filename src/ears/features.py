from __future__ import annotations

from hashlib import sha256
import math

from .audio import PCMBuffer
from .model import AudioSpan, EvidenceItem, EvidenceKind


PRODUCER = "ears.core.signal"
PRODUCER_VERSION = "0.1.0"


def _stable_id(*parts: object) -> str:
    joined = "|".join(str(part) for part in parts)
    return "ev:" + sha256(joined.encode("utf-8")).hexdigest()


def waveform_references(buffer: PCMBuffer) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for channel in range(buffer.channels):
        span = AudioSpan(
            buffer.source_id, 0.0, buffer.duration_ms, channel=channel
        )
        items.append(
            EvidenceItem(
                evidence_id=_stable_id(
                    buffer.source_id, "waveform", channel, PRODUCER_VERSION
                ),
                span=span,
                kind=EvidenceKind.WAVEFORM_REFERENCE,
                producer=PRODUCER,
                producer_version=PRODUCER_VERSION,
                payload={
                    "container": "WAV",
                    "encoding": "PCM",
                    "sample_rate": buffer.sample_rate,
                    "sample_width_bytes": buffer.sample_width,
                    "frame_count": buffer.frame_count,
                },
            )
        )
    return items


def _frame_metrics(window: tuple[float, ...]) -> dict[str, float | int]:
    count = len(window)
    if count == 0:
        return {
            "sample_count": 0,
            "rms": 0.0,
            "peak_abs": 0.0,
            "zero_crossing_rate": 0.0,
        }
    square_sum = sum(sample * sample for sample in window)
    rms = math.sqrt(square_sum / count)
    peak = max(abs(sample) for sample in window)
    if count == 1:
        zcr = 0.0
    else:
        signs = [1 if sample >= 0 else -1 for sample in window]
        crossings = sum(left != right for left, right in zip(signs, signs[1:]))
        zcr = crossings / (count - 1)
    return {
        "sample_count": count,
        "rms": round(rms, 10),
        "peak_abs": round(peak, 10),
        "zero_crossing_rate": round(zcr, 10),
    }


def frame_observations(
    buffer: PCMBuffer,
    *,
    frame_ms: float = 20.0,
    hop_ms: float = 10.0,
) -> list[EvidenceItem]:
    if frame_ms <= 0 or hop_ms <= 0:
        raise ValueError("frame_ms and hop_ms must be positive")
    frame_samples = max(1, round(buffer.sample_rate * frame_ms / 1000.0))
    hop_samples = max(1, round(buffer.sample_rate * hop_ms / 1000.0))
    items: list[EvidenceItem] = []

    for channel, samples in enumerate(buffer.samples):
        start = 0
        while start < buffer.frame_count:
            end = min(start + frame_samples, buffer.frame_count)
            window = samples[start:end]
            start_ms = start * 1000.0 / buffer.sample_rate
            end_ms = end * 1000.0 / buffer.sample_rate
            span = AudioSpan(buffer.source_id, start_ms, end_ms, channel=channel)
            items.append(
                EvidenceItem(
                    evidence_id=_stable_id(
                        buffer.source_id,
                        "frame",
                        channel,
                        start,
                        end,
                        PRODUCER_VERSION,
                    ),
                    span=span,
                    kind=EvidenceKind.ACOUSTIC_FRAME_OBSERVATION,
                    producer=PRODUCER,
                    producer_version=PRODUCER_VERSION,
                    payload={
                        "frame_ms_requested": frame_ms,
                        "hop_ms_requested": hop_ms,
                        **_frame_metrics(window),
                    },
                    derivation=(
                        "PCM samples from source WAV",
                        "deterministic frame-level signal measurements",
                    ),
                )
            )
            start += hop_samples
    return items