from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import wave


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


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def read_wav(path: str | Path) -> PCMBuffer:
    source = Path(path)
    digest = _hash_file(source)
    with wave.open(str(source), "rb") as reader:
        if reader.getcomptype() != "NONE":
            raise ValueError("only uncompressed PCM WAV is supported in V0.1")
        channels = reader.getnchannels()
        sample_rate = reader.getframerate()
        sample_width = reader.getsampwidth()
        frame_count = reader.getnframes()
        raw = reader.readframes(frame_count)

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