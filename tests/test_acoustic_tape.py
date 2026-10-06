from __future__ import annotations

import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from ears import AcousticTapeAdapter, EvidenceKind, compare_acoustic_counterfactual, inspect_wav
from ears.audio import read_wav


def write_tone(path: Path, *, frequency_hz: float = 440.0, amplitude: float = 0.4) -> None:
    sample_rate = 16000
    frame_count = sample_rate // 5
    raw = b"".join(
        struct.pack(
            "<h",
            int(amplitude * 32767 * math.sin(2 * math.pi * frequency_hz * index / sample_rate)),
        )
        for index in range(frame_count)
    )
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(raw)


class AcousticTapeTests(unittest.TestCase):
    def test_metadata_is_discrete_nonlearned_and_transcript_free(self) -> None:
        adapter = AcousticTapeAdapter()
        self.assertFalse(adapter.metadata.learned)
        self.assertFalse(adapter.metadata.transcript_required)
        self.assertEqual(adapter.metadata.representation, "discrete_acoustic_tape_v1")

    def test_symbols_are_deterministic_and_time_ordered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tone.wav"
            write_tone(path)
            buffer = read_wav(path)
            adapter = AcousticTapeAdapter()
            left = adapter.process(buffer)
            right = adapter.process(buffer)
            self.assertTrue(left)
            self.assertEqual(
                [item.payload["symbol"] for item in left],
                [item.payload["symbol"] for item in right],
            )
            self.assertTrue(all(item.kind is EvidenceKind.DISCRETE_ACOUSTIC_SYMBOL for item in left))
            self.assertTrue(
                all(
                    left[index].span.start_ms <= left[index + 1].span.start_ms
                    for index in range(len(left) - 1)
                )
            )

    def test_energy_change_changes_acoustic_tape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            quiet = root / "quiet.wav"
            loud = root / "loud.wav"
            write_tone(quiet, amplitude=0.1)
            write_tone(loud, amplitude=0.8)
            adapter = AcousticTapeAdapter()
            quiet_symbols = [item.payload["symbol"] for item in adapter.process(read_wav(quiet))]
            loud_symbols = [item.payload["symbol"] for item in adapter.process(read_wav(loud))]
            self.assertNotEqual(quiet_symbols, loud_symbols)

    def test_default_pipeline_and_counterfactual_include_tape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left_path = root / "left.wav"
            right_path = root / "right.wav"
            write_tone(left_path, frequency_hz=220.0)
            write_tone(right_path, frequency_hz=440.0)
            left = inspect_wav(left_path)
            right = inspect_wav(right_path)
            self.assertIn(EvidenceKind.DISCRETE_ACOUSTIC_SYMBOL.value, left.kind_counts())
            report = compare_acoustic_counterfactual(
                left,
                right,
                lexical_control="same declared words",
            )
            self.assertGreater(
                report["absolute_deltas"]["discrete_acoustic_symbol_disagreement_rate"],
                0.0,
            )
            self.assertEqual(
                report["claim_ceiling"],
                "ACOUSTIC_DIFFERENCE_ONLY_NOT_SEMANTIC_REASONING",
            )
            identical = compare_acoustic_counterfactual(left, left)
            self.assertEqual(
                identical["absolute_deltas"][
                    "discrete_acoustic_symbol_disagreement_rate"
                ],
                0.0,
            )
            self.assertEqual(
                identical["absolute_deltas"]["discrete_acoustic_symbol_count_delta"],
                0,
            )


if __name__ == "__main__":
    unittest.main()
