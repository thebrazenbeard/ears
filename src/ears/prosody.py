from __future__ import annotations

from hashlib import sha256
import math

from .audio import PCMBuffer
from .model import AudioSpan, EvidenceItem, EvidenceKind


PRODUCER = "ears.core.prosody"
PRODUCER_VERSION = "0.2.0"


def _stable_id(*parts: object) -> str:
    joined = "|".join(str(part) for part in parts)
    return "ev:" + sha256(joined.encode("utf-8")).hexdigest()


def _rms(window: tuple[float, ...]) -> float:
    if not window:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in window) / len(window))


def estimate_f0(
    window: tuple[float, ...],
    sample_rate: int,
    *,
    min_hz: float = 70.0,
    max_hz: float = 500.0,
    silence_rms: float = 0.01,
    yin_threshold: float = 0.2,
    min_confidence: float = 0.65,
) -> tuple[float | None, float]:
    """Estimate fundamental frequency with a small YIN-style baseline.

    The cumulative-mean-normalized difference function avoids the strong
    subharmonic preference of a naive global autocorrelation maximum.
    """
    if len(window) < 3 or sample_rate <= 0:
        return None, 0.0
    if _rms(window) < silence_rms:
        return None, 0.0

    min_lag = max(2, int(sample_rate / max_hz))
    max_lag = min(len(window) // 2, int(sample_rate / min_hz))
    if min_lag > max_lag:
        return None, 0.0

    differences = [0.0] * (max_lag + 1)
    for lag in range(1, max_lag + 1):
        differences[lag] = sum(
            (window[index] - window[index + lag]) ** 2
            for index in range(len(window) - lag)
        )

    cmndf = [1.0] * (max_lag + 1)
    running = 0.0
    for lag in range(1, max_lag + 1):
        running += differences[lag]
        cmndf[lag] = differences[lag] * lag / running if running else 1.0

    candidate: int | None = None
    lag = min_lag
    while lag <= max_lag:
        if cmndf[lag] < yin_threshold:
            while lag + 1 <= max_lag and cmndf[lag + 1] < cmndf[lag]:
                lag += 1
            candidate = lag
            break
        lag += 1
    if candidate is None:
        candidate = min(range(min_lag, max_lag + 1), key=cmndf.__getitem__)

    confidence = max(0.0, min(1.0, 1.0 - cmndf[candidate]))
    if confidence < min_confidence:
        return None, round(confidence, 10)
    return round(sample_rate / candidate, 6), round(confidence, 10)


def prosodic_observations(
    buffer: PCMBuffer,
    *,
    frame_ms: float = 40.0,
    hop_ms: float = 10.0,
    min_hz: float = 70.0,
    max_hz: float = 500.0,
) -> list[EvidenceItem]:
    if frame_ms <= 0 or hop_ms <= 0:
        raise ValueError("frame_ms and hop_ms must be positive")
    if min_hz <= 0 or max_hz <= min_hz:
        raise ValueError("invalid pitch range")

    frame_samples = max(1, round(buffer.sample_rate * frame_ms / 1000.0))
    hop_samples = max(1, round(buffer.sample_rate * hop_ms / 1000.0))
    items: list[EvidenceItem] = []

    for channel, samples in enumerate(buffer.samples):
        start = 0
        while start < buffer.frame_count:
            end = min(start + frame_samples, buffer.frame_count)
            window = samples[start:end]
            f0_hz, confidence = estimate_f0(
                window,
                buffer.sample_rate,
                min_hz=min_hz,
                max_hz=max_hz,
            )
            span = AudioSpan(
                buffer.source_id,
                start * 1000.0 / buffer.sample_rate,
                end * 1000.0 / buffer.sample_rate,
                channel=channel,
            )
            items.append(
                EvidenceItem(
                    evidence_id=_stable_id(
                        buffer.source_id,
                        "prosody",
                        channel,
                        start,
                        end,
                        min_hz,
                        max_hz,
                        PRODUCER_VERSION,
                    ),
                    span=span,
                    kind=EvidenceKind.PROSODIC_OBSERVATION,
                    producer=PRODUCER,
                    producer_version=PRODUCER_VERSION,
                    payload={
                        "f0_hz": f0_hz,
                        "voicing_confidence": confidence,
                        "rms": round(_rms(window), 10),
                        "method": "yin_cmndf_baseline",
                        "min_hz": min_hz,
                        "max_hz": max_hz,
                    },
                    derivation=(
                        "PCM samples from source WAV",
                        "deterministic YIN-style pitch baseline",
                    ),
                )
            )
            start += hop_samples
    return items
