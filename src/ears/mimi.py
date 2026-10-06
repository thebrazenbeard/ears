from __future__ import annotations

from hashlib import sha256
import re
from typing import Any

from .adapters import AdapterMetadata
from .audio import PCMBuffer
from .model import AudioSpan, EvidenceItem, EvidenceKind
from .wavlm import ModelPolicyError, OptionalDependencyUnavailable

DEFAULT_MIMI_REVISION = "89091b3e466eb6a9d11e537bf26b144f194978f7"
_IMMUTABLE_REVISION = re.compile(r"^[0-9a-fA-F]{40}$")


class MimiSemanticUnitAdapter:
    """Provider-declared semantic Mimi codebook, preserved as discrete units."""

    metadata = AdapterMetadata(
        name="ears.mimi_semantic",
        version="0.8.0",
        representation="mimi_semantic_codebook_v1",
        learned=True,
        transcript_required=False,
    )

    def __init__(
        self,
        *,
        model_id: str = "kyutai/mimi",
        revision: str = DEFAULT_MIMI_REVISION,
        device: str = "cpu",
        require_immutable_revision: bool = True,
        max_duration_ms: float = 120_000.0,
    ) -> None:
        if require_immutable_revision and not _IMMUTABLE_REVISION.fullmatch(revision):
            raise ModelPolicyError("learned-model revision must be an immutable 40-hex commit")
        if max_duration_ms <= 0:
            raise ValueError("max_duration_ms must be positive")
        self.model_id, self.revision, self.device = model_id, revision, device
        self.max_duration_ms = max_duration_ms
        self._feature_extractor: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None
        self._resolved_revision: str | None = None

    def feature_extractor_load_kwargs(self) -> dict[str, object]:
        return {"revision": self.revision, "trust_remote_code": False}

    def model_load_kwargs(self) -> dict[str, object]:
        return {
            "revision": self.revision,
            "trust_remote_code": False,
            "use_safetensors": True,
        }

    @staticmethod
    def _stable_id(*parts: object) -> str:
        return "ev:" + sha256(
            "|".join(str(part) for part in parts).encode("utf-8")
        ).hexdigest()

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoFeatureExtractor, MimiModel
        except ImportError as exc:
            raise OptionalDependencyUnavailable(
                "MimiSemanticUnitAdapter requires torch and transformers>=4.45"
            ) from exc
        extractor = AutoFeatureExtractor.from_pretrained(
            self.model_id, **self.feature_extractor_load_kwargs()
        )
        model = MimiModel.from_pretrained(self.model_id, **self.model_load_kwargs())
        if int(getattr(model.config, "num_semantic_quantizers", 0)) != 1:
            raise ModelPolicyError("Mimi semantic-unit path requires exactly one provider semantic quantizer")
        model.to(self.device)
        model.eval()
        self._torch, self._feature_extractor, self._model = torch, extractor, model
        self._resolved_revision = getattr(model.config, "_commit_hash", None)

    def process(self, buffer: PCMBuffer) -> list[EvidenceItem]:
        if buffer.sample_rate != 24000:
            raise ValueError(
                "MimiSemanticUnitAdapter requires 24 kHz PCM; "
                "resampling must be explicit and provenance-bound"
            )
        if buffer.duration_ms > self.max_duration_ms:
            raise ValueError("MimiSemanticUnitAdapter input exceeds learned-channel duration limit")
        self._load()
        assert self._torch is not None
        assert self._feature_extractor is not None
        assert self._model is not None
        frame_rate = float(self._model.config.frame_rate)
        if frame_rate <= 0:
            raise ModelPolicyError("Mimi frame_rate must be positive")
        evidence: list[EvidenceItem] = []
        for channel, samples in enumerate(buffer.samples):
            inputs = self._feature_extractor(
                raw_audio=list(samples),
                sampling_rate=24000,
                return_tensors="pt",
            )
            input_values = inputs["input_values"].to(self.device)
            with self._torch.no_grad():
                output = self._model.encode(input_values, num_quantizers=1)
            codebooks = output.audio_codes[0].detach().cpu().tolist()
            if len(codebooks) != 1:
                raise ModelPolicyError("Mimi semantic path returned an unexpected codebook count")
            for frame_index, code in enumerate(codebooks[0]):
                start_ms = frame_index * 1000.0 / frame_rate
                end_ms = min(buffer.duration_ms, (frame_index + 1) * 1000.0 / frame_rate)
                evidence.append(
                    EvidenceItem(
                        evidence_id=self._stable_id(
                            buffer.source_id, self.metadata.name, channel, frame_index,
                            int(code), self.model_id, self.revision,
                            self._resolved_revision, self.metadata.version,
                        ),
                        span=AudioSpan(buffer.source_id, start_ms, end_ms, channel=channel),
                        kind=EvidenceKind.DISCRETE_SPEECH_UNIT,
                        producer=self.metadata.name,
                        producer_version=self.metadata.version,
                        payload={
                            "representation": self.metadata.representation,
                            "code": int(code),
                            "frame_index": frame_index,
                            "frame_rate_hz": frame_rate,
                            "nominal_frame_ms": 1000.0 / frame_rate,
                            "alignment": "NOMINAL_CODEC_FRAME_INTERVAL_NOT_RECEPTIVE_FIELD",
                            "quantizer_role": "PROVIDER_DECLARED_SEMANTIC",
                            "num_quantizers_requested": 1,
                            "num_semantic_quantizers": 1,
                            "codebook_size": int(self._model.config.codebook_size),
                            "model_id": self.model_id,
                            "requested_revision": self.revision,
                            "resolved_revision": self._resolved_revision,
                            "trust_remote_code": False,
                            "safetensors_required": True,
                        },
                        derivation=(
                            "PCM samples from source WAV",
                            "Hugging Face AutoFeatureExtractor",
                            "Mimi encoder",
                            "provider-declared semantic residual vector quantizer",
                            "discrete semantic-codebook index",
                        ),
                    )
                )
        return evidence
