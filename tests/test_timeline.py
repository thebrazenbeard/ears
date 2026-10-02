from __future__ import annotations

import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from ears import EvidenceKind, inspect_wav, write_artifact


def write_test_wav(path: Path, *, sample_rate: int = 8000) -> None:
    samples: list[int] = []
    for _ in range(sample_rate // 10):
        samples.append(0)
    for index in range(sample_rate // 10):
        value = int(
            0.5
            * 32767
            * math.sin(2 * math.pi * 440 * index / sample_rate)
        )
        samples.append(value)
    raw = b"".join(struct.pack("<h", sample) for sample in samples)
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(raw)


class EvidenceTimelineTests(unittest.TestCase):
    def test_inspection_is_transcript_free_and_time_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_test_wav(path)
            timeline = inspect_wav(path)

            self.assertEqual(timeline.channels, 1)
            self.assertAlmostEqual(timeline.duration_ms, 200.0, places=3)
            self.assertNotIn(
                EvidenceKind.TRANSCRIPT_HYPOTHESIS.value,
                timeline.kind_counts(),
            )
            self.assertTrue(timeline.evidence)
            self.assertTrue(
                all(
                    item.span.end_ms <= timeline.duration_ms
                    for item in timeline.evidence
                )
            )

    def test_acoustic_frames_distinguish_silence_from_signal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_test_wav(path)
            timeline = inspect_wav(
                path,
                frame_ms=20.0,
                hop_ms=20.0,
            )
            frames = [
                item
                for item in timeline.ordered()
                if item.kind is EvidenceKind.ACOUSTIC_FRAME_OBSERVATION
            ]
            first_half = [item.payload["rms"] for item in frames[:5]]
            second_half = [item.payload["rms"] for item in frames[5:]]
            self.assertEqual(max(first_half), 0.0)
            self.assertGreater(min(second_half), 0.3)

    def test_artifact_is_deterministic_and_does_not_copy_audio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.wav"
            write_test_wav(source)
            left = inspect_wav(source)
            right = inspect_wav(source)
            self.assertEqual(left.source_id, right.source_id)

            left_paths = write_artifact(left, root / "left")
            right_paths = write_artifact(right, root / "right")
            for left_path, right_path in zip(left_paths, right_paths):
                self.assertEqual(
                    left_path.read_bytes(),
                    right_path.read_bytes(),
                )

            manifest = json.loads(
                left_paths[0].read_text(encoding="utf-8")
            )
            self.assertFalse(manifest["raw_audio_copied"])
            self.assertFalse(manifest["transcript_required"])

    def test_evidence_payload_is_immutable_after_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_test_wav(path)
            timeline = inspect_wav(path)
            item = timeline.ordered()[0]
            with self.assertRaises(TypeError):
                item.payload["mutated"] = True


if __name__ == "__main__":
    unittest.main()