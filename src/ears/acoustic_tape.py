from __future__ import annotations

from hashlib import sha256
import math

import numpy as np

from .adapters import AdapterMetadata
from .audio import PCMBuffer
from .logmel import LogMelAdapter
from .model import EvidenceItem, EvidenceKind


class AcousticTapeAdapter:
    """Deterministic time-ordered discrete acoustic symbols.

    This is deliberately a low-tech control representation, not a learned
    speech tokenizer and not evidence of semantic understanding.
    """

    metadata = AdapterMetadata(
        name="ears.acoustic_tape",
        version="0.6.0",
        representation="discrete_acoustic_tape_v1",
        learned=False,
        transcript_required=False,
    )

    def __init__(
        self,
        *,
        n_bands: int = 8,
        levels: int = 8,
        frame_ms: float = 25.0,
        hop_ms: float = 10.0,
    ) -> None:
        if n_bands <= 0:
            raise ValueError("n_bands must be positive")
        if levels < 2 or levels > 36:
            raise ValueError("levels must be between 2 and 36")
        if frame_ms <= 0 or hop_ms <= 0:
            raise ValueError("frame_ms and hop_ms must be positive")
        self.n_bands = n_bands
        self.levels = levels
        self.frame_ms = frame_ms
        self.hop_ms = hop_ms

    @staticmethod
    def _stable_id(*parts: object) -> str:
        joined = "|".join(str(part) for part in parts)
        return "ev:" + sha256(joined.encode("utf-8")).hexdigest()

    def _quantize(self, value: float) -> int:
        bounded = min(1.0, max(0.0, value))
        return int(round(bounded * (self.levels - 1)))

    @staticmethod
    def _digit(value: int) -> str:
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return alphabet[value]

    def process(self, buffer: PCMBuffer) -> list[EvidenceItem]:
        logmel = LogMelAdapter(
            n_mels=self.n_bands,
            frame_ms=self.frame_ms,
            hop_ms=self.hop_ms,
            fmin_hz=0.0,
        )
        mel_items = logmel.process(buffer)
        evidence: list[EvidenceItem] = []

        for mel_item in mel_items:
            values = np.asarray(mel_item.payload["values"], dtype=np.float64)
            lower = float(values.min())
            upper = float(values.max())
            spread = upper - lower
            if spread <= 1e-12:
                shape = tuple(0 for _ in values)
            else:
                shape = tuple(
                    self._quantize(float((value - lower) / spread))
                    for value in values
                )

            channel = mel_item.span.channel
            start_sample = max(
                0,
                int(round(mel_item.span.start_ms * buffer.sample_rate / 1000.0)),
            )
            end_sample = min(
                buffer.frame_count,
                int(round(mel_item.span.end_ms * buffer.sample_rate / 1000.0)),
            )
            frame = buffer.samples[channel][start_sample:end_sample]
            rms = (
                math.sqrt(sum(sample * sample for sample in frame) / len(frame))
                if frame
                else 0.0
            )
            energy_bin = self._quantize(rms)
            symbol = (
                "E"
                + self._digit(energy_bin)
                + "-S"
                + "".join(self._digit(value) for value in shape)
            )

            evidence.append(
                EvidenceItem(
                    evidence_id=self._stable_id(
                        buffer.source_id,
                        self.metadata.name,
                        channel,
                        start_sample,
                        end_sample,
                        self.n_bands,
                        self.levels,
                        self.frame_ms,
                        self.hop_ms,
                        self.metadata.version,
                    ),
                    span=mel_item.span,
                    kind=EvidenceKind.DISCRETE_ACOUSTIC_SYMBOL,
                    producer=self.metadata.name,
                    producer_version=self.metadata.version,
                    payload={
                        "representation": self.metadata.representation,
                        "symbol": symbol,
                        "energy_bin": energy_bin,
                        "shape_bins": list(shape),
                        "levels": self.levels,
                        "n_bands": self.n_bands,
                        "frame_ms_requested": self.frame_ms,
                        "hop_ms_requested": self.hop_ms,
                        "streaming_global_statistics_required": False,
                    },
                    derivation=(
                        "PCM samples from source WAV",
                        "frame-local log-mel spectral shape",
                        "frame-local min/max normalization",
                        "fixed-level spectral quantization",
                        "fixed-level RMS energy quantization",
                        "time-ordered discrete symbol",
                    ),
                )
            )
        return evidence
