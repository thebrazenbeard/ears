"""Dependency-light, evidence-preserving acoustic feature extraction for Ears.

No transcription, language inference, source identity, or ground-truth phoneme
classification occurs here. Frame timestamps refer to centers of analysis windows.
"""
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass(frozen=True)
class AcousticFrame:
    time_seconds: float
    rms: float
    spectral_centroid_hz: float
    spectral_flatness: float
    spectral_flux: float
    zero_crossing_rate: float
    f0_hz: Optional[float]
    harmonic_ratio: Optional[float]
    voiced_candidate: bool
    spectrum_hz: np.ndarray
    spectrum_magnitude: np.ndarray
    f0_candidates_hz: tuple[float, ...]
    source: str = "ears.numpy_stft.v1"


def _pitch_candidates(magnitude, frequencies, low_hz, high_hz, count=3):
    """Rank distinct candidate F0 values by a normalized harmonic summation.

    This is an intentionally simple baseline, not a trained pitch tracker.
    """
    delta = frequencies[1] - frequencies[0]
    if high_hz <= low_hz or delta <= 0:
        return ()
    # Evaluate at actual FFT bins and avoid zero-frequency candidates.
    indices = np.flatnonzero((frequencies >= low_hz) & (frequencies <= high_hz))
    scored = []
    floor = float(np.max(magnitude)) * 1e-12 + 1e-15
    for k in indices:
        f = frequencies[k]
        harmonic_bins = np.rint(np.arange(1, 7) * f / delta).astype(int)
        harmonic_bins = harmonic_bins[harmonic_bins < len(magnitude)]
        if len(harmonic_bins) < 2:
            continue
        # Geometric mean discourages an isolated, high-energy single bin.
        values = magnitude[harmonic_bins] + floor
        score = float(np.mean(np.log(values)))
        scored.append((score, float(f)))
    scored.sort(reverse=True)
    chosen = []
    for _, f in scored:
        if all(abs(12 * np.log2(f / previous)) > 1.0 for previous in chosen):
            chosen.append(f)
        if len(chosen) == count:
            break
    return tuple(chosen)


def analyze_pcm(
    samples,
    sample_rate: int,
    *,
    frame_size: int = 2048,
    hop_size: int = 512,
    min_f0_hz: float = 65.0,
    max_f0_hz: float = 600.0,
) -> list[AcousticFrame]:
    """Analyze a mono PCM signal into synchronized acoustic observations.

    A Voiced candidate is a heuristic, not an asserted speech or phoneme label.
    The last incomplete frame is discarded; no invented padded observations.
    """
    if sample_rate <= 0 or frame_size < 32 or hop_size <= 0:
        raise ValueError("invalid analysis parameters")
    if not (0 < min_f0_hz < max_f0_hz < sample_rate / 2):
        raise ValueError("pitch range must fit the Nyquist frequency")
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim != 1 or not np.all(np.isfinite(x)):
        raise ValueError("samples must be finite mono PCM")
    if len(x) < frame_size:
        return []
    win = np.hanning(frame_size)
    hz = np.fft.rfftfreq(frame_size, 1 / sample_rate)
    previous = None
    out = []
    for start in range(0, len(x) - frame_size + 1, hop_size):
        frame = x[start:start + frame_size]
        spectrum = np.abs(np.fft.rfft(frame * win))
        total = float(np.sum(spectrum))
        rms = float(np.sqrt(np.mean(frame * frame)))
        centroid = float(np.dot(hz, spectrum) / total) if total > 1e-12 else 0.0
        flatness = float(np.exp(np.mean(np.log(spectrum + 1e-12))) /
                         (np.mean(spectrum) + 1e-12))
        flatness = max(0.0, min(1.0, flatness))
        normalized = spectrum / (total + 1e-12)
        flux = float(np.linalg.norm(np.maximum(normalized - previous, 0))) if previous is not None else 0.0
        previous = normalized
        zcr = float(np.mean(np.signbit(frame[:-1]) != np.signbit(frame[1:])))
        candidates = _pitch_candidates(spectrum, hz, min_f0_hz, max_f0_hz) if rms > 1e-8 else ()
        f0 = candidates[0] if candidates else None
        ratio = None
        if f0 is not None:
            # Fraction of spectral energy in +/- one-bin harmonic neighborhoods.
            marks = np.zeros(len(spectrum), dtype=bool)
            for n in range(1, int(hz[-1] // f0) + 1):
                k = int(round(n * f0 / (hz[1] - hz[0])))
                marks[max(0, k-1):min(len(marks), k+2)] = True
            ratio = float(np.sum(spectrum[marks] ** 2) / (np.sum(spectrum ** 2) + 1e-12))
        voiced = bool(rms > 1e-5 and ratio is not None and ratio > 0.65 and flatness < 0.45)
        out.append(AcousticFrame(
            (start + frame_size / 2) / sample_rate,
            rms, centroid, flatness, flux, zcr,
            f0, ratio, voiced, hz.copy(), spectrum.copy(), candidates,
        ))
    return out
