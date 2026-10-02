from __future__ import annotations

import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from ears import EvidenceKind, inspect_wav
from ears.adapters import AdapterMetadata, run_adapters
from ears.audio import read_wav
from ears.logmel import LogMelAdapter


def write_sine(path: Path, *, frequency_hz: float = 440.0) -> None:
    sample_rate = 16000
    frame_count = sample_rate // 5
    samples = [
        int(
            0.4
            * 32767
            * math.sin(2 * math.pi * frequency_hz * index / sample_rate)
        )
        for index in range(frame_count)
    ]
    raw = b"".join(struct.pack("<h", sample) for sample in samples)
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(raw)


class LogMelAdapterTests(unittest.TestCase):
    def test_default_pipeline_emits_continuous_acoustic_features(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tone.wav"
            write_sine(source)
            timeline = inspect_wav(source)
            items = [
                item
                for item in timeline.evidence
                if item.kind is EvidenceKind.CONTINUOUS_ACOUSTIC_FEATURE
            ]
            self.assertTrue(items)
            self.assertEqual(items[0].payload["n_mels"], 40)
            self.assertEqual(len(items[0].payload["values"]), 40)
            self.assertTrue(
                all(math.isfinite(value) for value in items[0].payload["values"])
            )

    def test_adapter_metadata_declares_no_transcript_requirement(self) -> None:
        adapter = LogMelAdapter()
        self.assertIsInstance(adapter.metadata, AdapterMetadata)
        self.assertFalse(adapter.metadata.learned)
        self.assertFalse(adapter.metadata.transcript_required)

    def test_adapter_runner_preserves_evidence_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tone.wav"
            write_sine(source)
            buffer = read_wav(source)
            evidence = run_adapters(buffer, [LogMelAdapter(n_mels=24)])
            self.assertTrue(evidence)
            self.assertTrue(
                all(
                    item.kind is EvidenceKind.CONTINUOUS_ACOUSTIC_FEATURE
                    for item in evidence
                )
            )
            self.assertTrue(
                all(len(item.payload["values"]) == 24 for item in evidence)
            )


if __name__ == "__main__":
    unittest.main()
