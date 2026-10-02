from __future__ import annotations

import builtins
from contextlib import redirect_stderr
from io import BytesIO, StringIO
from pathlib import Path
from hashlib import sha256
import struct
import tempfile
import unittest
from unittest.mock import patch
import wave

from ears.audio import AudioInputLimits, AudioPolicyError, read_wav
from ears.cli import build_parser, main
from ears.wavlm import (
    DEFAULT_WAVLM_REVISION,
    ModelPolicyError,
    WavLMAdapter,
)


def write_wav(path: Path, *, seconds: float = 0.2, sample_rate: int = 8000) -> None:
    frame_count = int(seconds * sample_rate)
    raw = b"".join(struct.pack("<h", 0) for _ in range(frame_count))
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(raw)


class LearnedModelPolicyTests(unittest.TestCase):
    def test_default_wavlm_revision_is_exact_provider_commit(self) -> None:
        adapter = WavLMAdapter()
        self.assertEqual(
            adapter.revision,
            "4c66d4806a428f2e922ccfa1a962776e232d487b",
        )
        self.assertEqual(adapter.revision, DEFAULT_WAVLM_REVISION)

    def test_cli_defaults_to_exact_wavlm_revision(self) -> None:
        args = build_parser().parse_args(["inspect", "sample.wav", "--wavlm"])
        self.assertEqual(args.wavlm_revision, DEFAULT_WAVLM_REVISION)

    def test_cli_rejects_mutable_revision_without_traceback(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr):
            result = main(
                [
                    "inspect",
                    "sample.wav",
                    "--wavlm",
                    "--wavlm-revision",
                    "main",
                ]
            )
        self.assertEqual(result, 2)
        self.assertIn("immutable", stderr.getvalue())

    def test_mutable_revision_is_rejected_by_default(self) -> None:
        with self.assertRaisesRegex(ModelPolicyError, "immutable"):
            WavLMAdapter(revision="main")

    def test_safe_model_loader_kwargs_are_fail_closed(self) -> None:
        adapter = WavLMAdapter()
        self.assertEqual(
            adapter.model_load_kwargs(),
            {
                "revision": DEFAULT_WAVLM_REVISION,
                "trust_remote_code": False,
                "use_safetensors": True,
            },
        )
        self.assertEqual(
            adapter.processor_load_kwargs(),
            {
                "revision": DEFAULT_WAVLM_REVISION,
                "trust_remote_code": False,
            },
        )

    def test_mutable_revision_can_be_explicitly_marked_exploratory(self) -> None:
        adapter = WavLMAdapter(
            revision="main",
            require_immutable_revision=False,
        )
        self.assertEqual(adapter.revision_binding, "MUTABLE_EXPLORATORY_REVISION")


class AudioInputPolicyTests(unittest.TestCase):
    def test_file_size_limit_rejects_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_wav(path)
            limits = AudioInputLimits(max_file_bytes=32)
            with self.assertRaisesRegex(AudioPolicyError, "file size"):
                read_wav(path, limits=limits)

    def test_source_id_binds_bytes_that_were_parsed_under_path_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_wav(path, seconds=0.2, sample_rate=8000)
            original_bytes = path.read_bytes()
            replacement = Path(directory) / "replacement.wav"
            write_wav(replacement, seconds=0.1, sample_rate=16000)
            replacement_bytes = replacement.read_bytes()
            real_path_open = Path.open
            open_count = 0

            class ReplacingStream(BytesIO):
                replaced = False

                def read(self, size: int = -1) -> bytes:
                    data = super().read(size)
                    if not self.replaced:
                        with builtins.open(path, "wb") as target:
                            target.write(replacement_bytes)
                        self.replaced = True
                    return data

            def open_with_replacement(source: Path, *args, **kwargs):
                nonlocal open_count
                mode = args[0] if args else kwargs.get("mode", "r")
                if source == path and mode == "rb" and open_count == 0:
                    open_count += 1
                    return ReplacingStream(original_bytes)
                return real_path_open(source, *args, **kwargs)

            with patch.object(Path, "open", new=open_with_replacement):
                buffer = read_wav(path)

            self.assertEqual(path.read_bytes(), replacement_bytes)
            self.assertEqual(
                buffer.source_id,
                "sha256:" + sha256(original_bytes).hexdigest(),
            )
            self.assertEqual(buffer.sample_rate, 8000)

    def test_decoded_sample_limit_rejects_before_float_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_wav(path, seconds=0.2, sample_rate=8000)
            limits = AudioInputLimits(
                max_file_bytes=1024 * 1024,
                max_decoded_samples=100,
            )
            with self.assertRaisesRegex(AudioPolicyError, "decoded sample"):
                read_wav(path, limits=limits)

    def test_duration_limit_rejects_input_before_pcm_decode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_wav(path, seconds=0.2)
            limits = AudioInputLimits(max_duration_ms=100.0)
            with self.assertRaisesRegex(AudioPolicyError, "duration"):
                read_wav(path, limits=limits)

    def test_sample_rate_limit_rejects_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            write_wav(path, sample_rate=48000)
            limits = AudioInputLimits(max_sample_rate=16000)
            with self.assertRaisesRegex(AudioPolicyError, "sample rate"):
                read_wav(path, limits=limits)


if __name__ == "__main__":
    unittest.main()
