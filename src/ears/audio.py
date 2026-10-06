from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import SpooledTemporaryFile
import wave


class AudioPolicyError(ValueError):
    """Raised when an audio source violates configured ingestion limits."""


@dataclass(frozen=True, slots=True)
class AudioInputLimits:
    max_file_bytes: int = 256 * 1024 * 1024
    max_duration_ms: float = 2 * 60 * 60 * 1000.0
    max_channels: int = 8
    max_sample_rate: int = 192000
    max_decoded_samples: int = 4_000_000


@dataclass(frozen=True, slots=True)
class PCMBuffer:
    source_id: str
    source_name: str
    sample_rate: int
    channels: int
    sample_width: int
    frame_count: int
    samples: tuple[tuple[float, ...], ...]

    @property
    def duration_ms(self) -> float:
        return (self.frame_count / self.sample_rate) * 1000.0


def _decode_pcm(raw: bytes, sample_width: int) -> list[float]:
    if sample_width not in {1, 2, 3, 4}:
        raise ValueError(f"unsupported PCM sample width: {sample_width}")
    values: list[float] = []
    if sample_width == 1:
        values.extend((byte - 128) / 128.0 for byte in raw)
        return values
    scale = float(1 << (sample_width * 8 - 1))
    for offset in range(0, len(raw), sample_width):
        chunk = raw[offset : offset + sample_width]
        value = int.from_bytes(chunk, "little", signed=True)
        values.append(value / scale)
    return values


def read_wav(
    path: str | Path,
    *,
    limits: AudioInputLimits | None = None,
) -> PCMBuffer:
    source = Path(path)
    policy = limits or AudioInputLimits()
    digest_builder = sha256()
    total_bytes = 0

    with SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b") as snapshot:
        with source.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > policy.max_file_bytes:
                    raise AudioPolicyError(
                        f"audio file size exceeds limit {policy.max_file_bytes}"
                    )
                digest_builder.update(chunk)
                snapshot.write(chunk)

        snapshot.seek(0)
        with wave.open(snapshot, "rb") as reader:
            if reader.getcomptype() != "NONE":
                raise ValueError("only uncompressed PCM WAV is supported in V0.1")
            channels = reader.getnchannels()
            sample_rate = reader.getframerate()
            sample_width = reader.getsampwidth()
            frame_count = reader.getnframes()

            if sample_width not in {1, 2, 3, 4}:
                raise ValueError(f"unsupported PCM sample width: {sample_width}")
            if channels > policy.max_channels:
                raise AudioPolicyError(
                    f"audio channel count {channels} exceeds limit {policy.max_channels}"
                )
            if sample_rate > policy.max_sample_rate:
                raise AudioPolicyError(
                    f"audio sample rate {sample_rate} exceeds limit {policy.max_sample_rate}"
                )
            duration_ms = (frame_count / sample_rate) * 1000.0
            if duration_ms > policy.max_duration_ms:
                raise AudioPolicyError(
                    f"audio duration {duration_ms:.3f} ms exceeds limit "
                    f"{policy.max_duration_ms:.3f} ms"
                )
            decoded_samples = frame_count * channels
            if decoded_samples > policy.max_decoded_samples:
                raise AudioPolicyError(
                    f"decoded sample count {decoded_samples} exceeds limit "
                    f"{policy.max_decoded_samples}"
                )
            raw = reader.readframes(frame_count)

    digest = digest_builder.hexdigest()
    interleaved = _decode_pcm(raw, sample_width)
    expected = frame_count * channels
    if len(interleaved) != expected:
        raise ValueError(
            f"decoded sample count mismatch: expected {expected}, got {len(interleaved)}"
        )
    per_channel = tuple(
        tuple(interleaved[channel::channels]) for channel in range(channels)
    )
    return PCMBuffer(
        source_id=f"sha256:{digest}",
        source_name=source.name,
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        frame_count=frame_count,
        samples=per_channel,
    )
