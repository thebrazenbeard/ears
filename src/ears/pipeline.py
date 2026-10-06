from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .acoustic_tape import AcousticTapeAdapter
from .adapters import EvidenceAdapter, run_adapters
from .audio import read_wav
from .features import frame_observations, waveform_references
from .logmel import LogMelAdapter
from .model import EvidenceTimeline
from .prosody import prosodic_observations


def inspect_wav(
    path: str | Path,
    *,
    frame_ms: float = 20.0,
    hop_ms: float = 10.0,
    extra_adapters: Sequence[EvidenceAdapter] = (),
) -> EvidenceTimeline:
    """Create a transcript-free evidence timeline from a PCM WAV source."""
    buffer = read_wav(path)
    timeline = EvidenceTimeline(
        source_id=buffer.source_id,
        source_name=buffer.source_name,
        sample_rate=buffer.sample_rate,
        channels=buffer.channels,
        duration_ms=buffer.duration_ms,
    )
    for item in waveform_references(buffer):
        timeline.add(item)
    for item in frame_observations(buffer, frame_ms=frame_ms, hop_ms=hop_ms):
        timeline.add(item)
    for item in prosodic_observations(buffer, hop_ms=hop_ms):
        timeline.add(item)
    for item in LogMelAdapter(hop_ms=hop_ms).process(buffer):
        timeline.add(item)
    for item in AcousticTapeAdapter(hop_ms=hop_ms).process(buffer):
        timeline.add(item)
    for item in run_adapters(buffer, extra_adapters):
        timeline.add(item)
    return timeline