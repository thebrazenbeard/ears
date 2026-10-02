from __future__ import annotations

from hashlib import sha256
import math

import numpy as np

from .adapters import AdapterMetadata
from .audio import PCMBuffer
from .model import AudioSpan, EvidenceItem, EvidenceKind


class LogMelAdapter:
    metadata = AdapterMetadata(
        name="ears.log_mel",
        version="0.3.0",
        representation="continuous_log_mel",
        learned=False,
        transcript_required=False,
    )

    def __init__(
        self,
        *,
        n_mels: int = 40,
        frame_ms: float = 25.0,
        hop_ms: float = 10.0,
        fmin_hz: float = 50.0,
        fmax_hz: float | None = None,
    ) -> None:
        if n_mels <= 0:
            raise ValueError("n_mels must be positive")
        if frame_ms <= 0 or hop_ms <= 0:
            raise ValueError("frame_ms and hop_ms must be positive")
        if fmin_hz < 0:
            raise ValueError("fmin_hz must be non-negative")
        self.n_mels = n_mels
        self.frame_ms = frame_ms
        self.hop_ms = hop_ms
        self.fmin_hz = fmin_hz
        self.fmax_hz = fmax_hz

    @staticmethod
    def _hz_to_mel(hz: float | np.ndarray) -> float | np.ndarray:
        return 2595.0 * np.log10(1.0 + np.asarray(hz) / 700.0)

    @staticmethod
    def _mel_to_hz(mel: float | np.ndarray) -> float | np.ndarray:
        return 700.0 * (np.power(10.0, np.asarray(mel) / 2595.0) - 1.0)

    def _filterbank(
        self,
        sample_rate: int,
        n_fft: int,
    ) -> np.ndarray:
        nyquist = sample_rate / 2.0
        fmax = nyquist if self.fmax_hz is None else min(self.fmax_hz, nyquist)
        if self.fmin_hz >= fmax:
            raise ValueError("fmin_hz must be below Nyquist/fmax")

        mel_min = float(self._hz_to_mel(self.fmin_hz))
        mel_max = float(self._hz_to_mel(fmax))
        mel_points = np.linspace(mel_min, mel_max, self.n_mels + 2)
        hz_points = np.asarray(self._mel_to_hz(mel_points), dtype=np.float64)
        bins = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)
        bins = np.clip(bins, 0, n_fft // 2)

        bank = np.zeros((self.n_mels, n_fft // 2 + 1), dtype=np.float64)
        for index in range(self.n_mels):
            left, center, right = bins[index : index + 3]
            if center <= left:
                center = min(left + 1, n_fft // 2)
            if right <= center:
                right = min(center + 1, n_fft // 2)
            if center > left:
                bank[index, left:center] = np.linspace(
                    0.0,
                    1.0,
                    center - left,
                    endpoint=False,
                )
            if right > center:
                bank[index, center:right] = np.linspace(
                    1.0,
                    0.0,
                    right - center,
                    endpoint=False,
                )
        return bank

    @staticmethod
    def _stable_id(*parts: object) -> str:
        joined = "|".join(str(part) for part in parts)
        return "ev:" + sha256(joined.encode("utf-8")).hexdigest()

    def process(self, buffer: PCMBuffer) -> list[EvidenceItem]:
        frame_samples = max(
            1,
            round(buffer.sample_rate * self.frame_ms / 1000.0),
        )
        hop_samples = max(
            1,
            round(buffer.sample_rate * self.hop_ms / 1000.0),
        )
        n_fft = 1
        while n_fft < frame_samples:
            n_fft *= 2
        window_fn = np.hanning(frame_samples)
        bank = self._filterbank(buffer.sample_rate, n_fft)
        evidence: list[EvidenceItem] = []

        for channel, channel_samples in enumerate(buffer.samples):
            samples = np.asarray(channel_samples, dtype=np.float64)
            start = 0
            while start < buffer.frame_count:
                end = min(start + frame_samples, buffer.frame_count)
                frame = samples[start:end]
                padded = np.zeros(frame_samples, dtype=np.float64)
                padded[: len(frame)] = frame
                spectrum = np.fft.rfft(padded * window_fn, n=n_fft)
                power = np.abs(spectrum) ** 2
                mel_power = bank @ power
                values = np.log1p(mel_power)
                values = np.round(values, 8)

                span = AudioSpan(
                    buffer.source_id,
                    start * 1000.0 / buffer.sample_rate,
                    end * 1000.0 / buffer.sample_rate,
                    channel=channel,
                )
                evidence.append(
                    EvidenceItem(
                        evidence_id=self._stable_id(
                            buffer.source_id,
                            self.metadata.name,
                            channel,
                            start,
                            end,
                            self.n_mels,
                            self.frame_ms,
                            self.hop_ms,
                            self.fmin_hz,
                            self.fmax_hz,
                            self.metadata.version,
                        ),
                        span=span,
                        kind=EvidenceKind.CONTINUOUS_ACOUSTIC_FEATURE,
                        producer=self.metadata.name,
                        producer_version=self.metadata.version,
                        payload={
                            "representation": self.metadata.representation,
                            "n_mels": self.n_mels,
                            "values": values.tolist(),
                            "frame_ms_requested": self.frame_ms,
                            "hop_ms_requested": self.hop_ms,
                            "fmin_hz": self.fmin_hz,
                            "fmax_hz": (
                                self.fmax_hz
                                if self.fmax_hz is not None
                                else buffer.sample_rate / 2.0
                            ),
                        },
                        derivation=(
                            "PCM samples from source WAV",
                            "Hann window",
                            "power spectrum",
                            "triangular mel filterbank",
                            "log1p compression",
                        ),
                    )
                )
                start += hop_samples
        return evidence
