from __future__ import annotations

import builtins
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ears.audio import PCMBuffer
from ears.mimi import DEFAULT_MIMI_REVISION, MimiSemanticUnitAdapter
from ears.model import EvidenceKind
from ears.wavlm import ModelPolicyError, OptionalDependencyUnavailable


class MimiSemanticUnitAdapterTests(unittest.TestCase):
    def test_metadata_and_safe_loader_policy(self) -> None:
        adapter = MimiSemanticUnitAdapter()
        self.assertTrue(adapter.metadata.learned)
        self.assertFalse(adapter.metadata.transcript_required)
        self.assertEqual(adapter.revision, DEFAULT_MIMI_REVISION)
        self.assertEqual(
            adapter.model_load_kwargs(),
            {
                "revision": DEFAULT_MIMI_REVISION,
                "trust_remote_code": False,
                "use_safetensors": True,
            },
        )

    def test_cli_defaults_bind_exact_mimi_revision(self) -> None:
        from ears.cli import build_parser
        args = build_parser().parse_args(["inspect", "sample.wav", "--mimi-semantic"])
        self.assertEqual(args.mimi_revision, DEFAULT_MIMI_REVISION)
        self.assertEqual(args.mimi_model, "kyutai/mimi")
        self.assertEqual(args.mimi_max_duration_ms, 120_000.0)

    def test_mutable_revision_is_rejected(self) -> None:
        with self.assertRaisesRegex(ModelPolicyError, "immutable"):
            MimiSemanticUnitAdapter(revision="main")

    def test_missing_optional_dependencies_fail_closed(self) -> None:
        adapter = MimiSemanticUnitAdapter()
        real_import = builtins.__import__

        def blocked(name, *args, **kwargs):
            if name in {"torch", "transformers"}:
                raise ImportError(name)
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocked):
            with self.assertRaises(OptionalDependencyUnavailable):
                adapter._load()

    def test_non_24khz_rejected_before_loading(self) -> None:
        buffer = PCMBuffer(
            source_id="sha256:test",
            source_name="test.wav",
            sample_rate=16000,
            channels=1,
            sample_width=2,
            frame_count=4,
            samples=((0.0, 0.0, 0.0, 0.0),),
        )
        with self.assertRaisesRegex(ValueError, "24 kHz"):
            MimiSemanticUnitAdapter().process(buffer)

    def test_fake_semantic_encode_preserves_codes_and_nominal_spans(self) -> None:
        class FakeInput:
            def to(self, device):
                return self

        class FakeCodes:
            def detach(self):
                return self
            def cpu(self):
                return self
            def tolist(self):
                return [[101, 202, 303]]

        class FakeBatchCodes:
            def __getitem__(self, item):
                self.batch_index = item
                return FakeCodes()

        class FakeExtractor:
            def __call__(self, **kwargs):
                self.kwargs = kwargs
                return {"input_values": FakeInput()}

        class FakeModel:
            config = SimpleNamespace(
                frame_rate=12.5,
                codebook_size=2048,
                num_semantic_quantizers=1,
            )
            def encode(self, input_values, num_quantizers):
                self.requested_quantizers = num_quantizers
                return SimpleNamespace(audio_codes=FakeBatchCodes())

        class FakeNoGrad:
            def __enter__(self):
                return None
            def __exit__(self, exc_type, exc, tb):
                return False

        class FakeTorch:
            @staticmethod
            def no_grad():
                return FakeNoGrad()

        adapter = MimiSemanticUnitAdapter()
        adapter._torch = FakeTorch()
        adapter._feature_extractor = FakeExtractor()
        adapter._model = FakeModel()
        adapter._resolved_revision = DEFAULT_MIMI_REVISION
        adapter._load = lambda: None

        frame_count = 6000
        buffer = PCMBuffer(
            source_id="sha256:fake-mimi",
            source_name="fake.wav",
            sample_rate=24000,
            channels=1,
            sample_width=2,
            frame_count=frame_count,
            samples=((0.0,) * frame_count,),
        )
        evidence = adapter.process(buffer)

        self.assertEqual([item.payload["code"] for item in evidence], [101, 202, 303])
        self.assertEqual(
            [(item.span.start_ms, item.span.end_ms) for item in evidence],
            [(0.0, 80.0), (80.0, 160.0), (160.0, 240.0)],
        )
        self.assertTrue(all(item.kind is EvidenceKind.DISCRETE_SPEECH_UNIT for item in evidence))
        self.assertTrue(
            all(item.payload["quantizer_role"] == "PROVIDER_DECLARED_SEMANTIC" for item in evidence)
        )
        self.assertTrue(
            all(
                item.payload["alignment"]
                == "NOMINAL_CODEC_FRAME_INTERVAL_NOT_RECEPTIVE_FIELD"
                for item in evidence
            )
        )


if __name__ == "__main__":
    unittest.main()
