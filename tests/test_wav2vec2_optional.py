from __future__ import annotations

import builtins
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ears.audio import PCMBuffer
from ears.wav2vec2 import (
    DEFAULT_WAV2VEC2_REVISION,
    Wav2Vec2Adapter,
)
from ears.wavlm import ModelPolicyError, OptionalDependencyUnavailable


class Wav2Vec2AdapterTests(unittest.TestCase):
    def test_metadata_declares_time_resolved_transcript_free_representation(self) -> None:
        adapter = Wav2Vec2Adapter()
        self.assertTrue(adapter.metadata.learned)
        self.assertFalse(adapter.metadata.transcript_required)
        self.assertEqual(
            adapter.metadata.representation,
            "wav2vec2_window_mean_hidden_state",
        )

    def test_default_revision_is_exact_provider_commit(self) -> None:
        adapter = Wav2Vec2Adapter()
        self.assertEqual(
            adapter.revision,
            "22aad52d435eb6dbaf354bdad9b0da84ce7d6156",
        )
        self.assertEqual(adapter.revision, DEFAULT_WAV2VEC2_REVISION)

    def test_cli_defaults_to_exact_revision_and_bounded_pooling(self) -> None:
        from ears.cli import build_parser
        args = build_parser().parse_args(["inspect", "sample.wav", "--wav2vec2"])
        self.assertEqual(args.wav2vec2_revision, DEFAULT_WAV2VEC2_REVISION)
        self.assertEqual(args.wav2vec2_pool_frames, 5)
        self.assertEqual(args.wav2vec2_max_duration_ms, 120_000.0)

    def test_safe_loader_kwargs_are_fail_closed(self) -> None:
        adapter = Wav2Vec2Adapter()
        self.assertEqual(
            adapter.model_load_kwargs(),
            {
                "revision": DEFAULT_WAV2VEC2_REVISION,
                "trust_remote_code": False,
                "use_safetensors": True,
            },
        )
        self.assertEqual(
            adapter.feature_extractor_load_kwargs(),
            {
                "revision": DEFAULT_WAV2VEC2_REVISION,
                "trust_remote_code": False,
            },
        )

    def test_mutable_revision_is_rejected_by_default(self) -> None:
        with self.assertRaisesRegex(ModelPolicyError, "immutable"):
            Wav2Vec2Adapter(revision="main")

    def test_missing_optional_dependencies_fail_closed(self) -> None:
        adapter = Wav2Vec2Adapter()
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
        with self.assertRaisesRegex(ValueError, "16 kHz"):
            Wav2Vec2Adapter().process(buffer)

    def test_duration_limit_is_rejected_before_model_loading(self) -> None:
        sample_rate = 16000
        frame_count = sample_rate
        buffer = PCMBuffer(
            source_id="sha256:test",
            source_name="test.wav",
            sample_rate=sample_rate,
            channels=1,
            sample_width=2,
            frame_count=frame_count,
            samples=((0.0,) * frame_count,),
        )
        with self.assertRaisesRegex(ValueError, "duration limit"):
            Wav2Vec2Adapter(max_duration_ms=500.0).process(buffer)

    def test_time_resolved_output_preserves_window_spans_and_provenance(self) -> None:
        class FakeInput:
            def to(self, device):
                self.device = device
                return self

        class FakeVector:
            def __init__(self, values):
                self.values = values

            def detach(self):
                return self

            def cpu(self):
                return self

            def tolist(self):
                return list(self.values)

        class FakeWindow:
            def __init__(self, rows):
                self.rows = rows

            def mean(self, dim=0):
                self.assert_dim = dim
                width = len(self.rows[0])
                return FakeVector(
                    [
                        sum(row[index] for row in self.rows) / len(self.rows)
                        for index in range(width)
                    ]
                )

        class FakeHidden:
            shape = (6, 3)

            def __init__(self):
                self.rows = [
                    [0.0, 1.0, 2.0],
                    [2.0, 3.0, 4.0],
                    [4.0, 5.0, 6.0],
                    [6.0, 7.0, 8.0],
                    [8.0, 9.0, 10.0],
                    [10.0, 11.0, 12.0],
                ]

            def __getitem__(self, item):
                if isinstance(item, slice):
                    return FakeWindow(self.rows[item])
                return self.rows[item]

        class FakeBatchHidden:
            def __getitem__(self, item):
                self.batch_index = item
                return FakeHidden()

        class FakeExtractor:
            def __call__(self, samples, *, sampling_rate, return_tensors):
                self.call = (len(samples), sampling_rate, return_tensors)
                return {"input_values": FakeInput()}

        class FakeModel:
            config = SimpleNamespace(
                conv_kernel=[10, 3, 3, 3, 3, 2, 2],
                conv_stride=[5, 2, 2, 2, 2, 2, 2],
            )

            def __call__(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(last_hidden_state=FakeBatchHidden())

        class FakeNoGrad:
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

        class FakeTorch:
            @staticmethod
            def no_grad():
                return FakeNoGrad()

        adapter = Wav2Vec2Adapter(pool_frames=2)
        adapter._torch = FakeTorch()
        adapter._feature_extractor = FakeExtractor()
        adapter._model = FakeModel()
        adapter._resolved_revision = DEFAULT_WAV2VEC2_REVISION
        adapter._load = lambda: None

        frame_count = 3200
        buffer = PCMBuffer(
            source_id="sha256:fake-runtime",
            source_name="fake.wav",
            sample_rate=16000,
            channels=1,
            sample_width=2,
            frame_count=frame_count,
            samples=((0.0,) * frame_count,),
        )
        evidence = adapter.process(buffer)

        self.assertEqual(len(evidence), 3)
        self.assertEqual(
            [(round(item.span.start_ms, 3), round(item.span.end_ms, 3)) for item in evidence],
            [(0.0, 45.0), (40.0, 85.0), (80.0, 125.0)],
        )
        self.assertEqual(evidence[0].payload["values"], [1.0, 2.0, 3.0])
        self.assertEqual(evidence[1].payload["values"], [5.0, 6.0, 7.0])
        self.assertEqual(evidence[2].payload["values"], [9.0, 10.0, 11.0])
        self.assertEqual(evidence[0].payload["model_frame_start"], 0)
        self.assertEqual(evidence[0].payload["model_frame_end"], 2)
        self.assertEqual(evidence[0].payload["resolved_revision"], DEFAULT_WAV2VEC2_REVISION)
        self.assertEqual(evidence[0].payload["revision_binding"], "EXACT_RESOLVED_REVISION")
        self.assertEqual(evidence[0].payload["alignment"], "DERIVED_VALID_CONV_GEOMETRY")
        self.assertEqual(evidence[0].payload["conv_receptive_field_samples"], 400)
        self.assertEqual(evidence[0].payload["conv_stride_samples"], 320)

    def test_observed_provider_conv_geometry_is_25ms_by_20ms(self) -> None:
        config = SimpleNamespace(
            conv_kernel=[10, 3, 3, 3, 3, 2, 2],
            conv_stride=[5, 2, 2, 2, 2, 2, 2],
        )
        receptive_field, stride = Wav2Vec2Adapter._conv_geometry(config)
        self.assertEqual(receptive_field, 400)
        self.assertEqual(stride, 320)


if __name__ == "__main__":
    unittest.main()
