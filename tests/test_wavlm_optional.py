from __future__ import annotations

import builtins
import unittest
from unittest.mock import patch

from ears.audio import PCMBuffer
from ears.wavlm import OptionalDependencyUnavailable, WavLMAdapter


class WavLMAdapterTests(unittest.TestCase):
    def test_metadata_declares_learned_transcript_free_representation(self) -> None:
        adapter = WavLMAdapter()
        self.assertTrue(adapter.metadata.learned)
        self.assertFalse(adapter.metadata.transcript_required)
        self.assertEqual(adapter.model_id, "microsoft/wavlm-base-plus")

    def test_missing_optional_dependencies_fail_closed(self) -> None:
        adapter = WavLMAdapter()
        real_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name in {"torch", "transformers"}:
                raise ImportError(f"blocked test import: {name}")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocked_import):
            with self.assertRaises(OptionalDependencyUnavailable):
                adapter._load()

    def test_non_16khz_audio_is_rejected_before_model_loading(self) -> None:
        buffer = PCMBuffer(
            source_id="sha256:test",
            source_name="test.wav",
            sample_rate=8000,
            channels=1,
            sample_width=2,
            frame_count=4,
            samples=((0.0, 0.1, -0.1, 0.0),),
        )
        adapter = WavLMAdapter()
        with self.assertRaisesRegex(ValueError, "16 kHz"):
            adapter.process(buffer)


if __name__ == "__main__":
    unittest.main()
