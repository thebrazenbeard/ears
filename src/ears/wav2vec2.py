from __future__ import annotations

from hashlib import sha256
import re
from typing import Any

from .adapters import AdapterMetadata
from .audio import PCMBuffer
from .model import AudioSpan, EvidenceItem, EvidenceKind
from .wavlm import ModelPolicyError, OptionalDependencyUnavailable

DEFAULT_WAV2VEC2_REVISION = "22aad52d435eb6dbaf354bdad9b0da84ce7d6156"
_IMMUTABLE_REVISION = re.compile(r"^[0-9a-fA-F]{40}$")


class Wav2Vec2Adapter:
    """Safetensors-only, time-resolved learned speech baseline."""

    metadata = AdapterMetadata(
        name="ears.wav2vec2",
        version="0.7.0",
        representation="wav2vec2_window_mean_hidden_state",
        learned=True,
        transcript_required=False,
    )

    def __init__(
        self,
        *,
        model_id: str = "facebook/wav2vec2-base-960h",
        revision: str = DEFAULT_WAV2VEC2_REVISION,
        device: str = "cpu",
        require_immutable_revision: bool = True,
        pool_frames: int = 5,
        max_duration_ms: float = 120_000.0,
    ) -> None:
        if require_immutable_revision and not _IMMUTABLE_REVISION.fullmatch(revision):
            raise ModelPolicyError("learned-model revision must be an immutable 40-hex commit")
        if pool_frames <= 0 or max_duration_ms <= 0:
            raise ValueError("pool_frames and max_duration_ms must be positive")
        self.model_id, self.revision, self.device = model_id, revision, device
        self.require_immutable_revision = require_immutable_revision
        self.pool_frames, self.max_duration_ms = pool_frames, max_duration_ms
        self._feature_extractor: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None
        self._resolved_revision: str | None = None

    @property
    def revision_binding(self) -> str:
        return (
            "EXACT_IMMUTABLE_REQUESTED_REVISION"
            if _IMMUTABLE_REVISION.fullmatch(self.revision)
            else "MUTABLE_EXPLORATORY_REVISION"
        )

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
        joined = "|".join(str(part) for part in parts)
        return "ev:" + sha256(joined.encode("utf-8")).hexdigest()

    @staticmethod
    def _conv_geometry(config: Any) -> tuple[int, int]:
        kernels = list(getattr(config, "conv_kernel", ()) or ())
        strides = list(getattr(config, "conv_stride", ()) or ())
        if not kernels or len(kernels) != len(strides):
            raise ModelPolicyError("invalid Wav2Vec2 convolution geometry")
        if any(int(x) <= 0 for x in kernels + strides):
            raise ModelPolicyError("Wav2Vec2 convolution values must be positive")
        receptive_field, jump = 1, 1
        for kernel, stride in zip(kernels, strides):
            receptive_field += (int(kernel) - 1) * jump
            jump *= int(stride)
        return receptive_field, jump

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoFeatureExtractor, AutoModel
        except ImportError as exc:
            raise OptionalDependencyUnavailable(
                "Wav2Vec2Adapter requires torch and transformers"
            ) from exc
        extractor = AutoFeatureExtractor.from_pretrained(
            self.model_id, **self.feature_extractor_load_kwargs()
        )
        model = AutoModel.from_pretrained(self.model_id, **self.model_load_kwargs())
        model.to(self.device)
        model.eval()
        self._torch, self._feature_extractor, self._model = torch, extractor, model
        self._resolved_revision = getattr(model.config, "_commit_hash", None)

    def process(self, buffer: PCMBuffer) -> list[EvidenceItem]:
        if buffer.sample_rate != 16000:
            raise ValueError(
                "Wav2Vec2Adapter currently requires 16 kHz PCM; "
                "resampling must be explicit and provenance-bound"
            )
        if buffer.duration_ms > self.max_duration_ms:
            raise ValueError("Wav2Vec2Adapter input exceeds learned-channel duration limit")
        self._load()
        assert self._torch is not None
        assert self._feature_extractor is not None
        assert self._model is not None
        receptive, stride = self._conv_geometry(self._model.config)
        evidence: list[EvidenceItem] = []
        for channel, samples in enumerate(buffer.samples):
            inputs = self._feature_extractor(
                list(samples), sampling_rate=16000, return_tensors="pt"
            )
            model_inputs = {key: value.to(self.device) for key, value in inputs.items()}
            with self._torch.no_grad():
                hidden = self._model(**model_inputs).last_hidden_state[0]
            frame_count, hidden_size = int(hidden.shape[0]), int(hidden.shape[1])
            for start in range(0, frame_count, self.pool_frames):
                end = min(start + self.pool_frames, frame_count)
                values = [
                    round(float(value), 8)
                    for value in hidden[start:end].mean(dim=0).detach().cpu().tolist()
                ]
                start_sample = start * stride
                end_sample = min(buffer.frame_count, (end - 1) * stride + receptive)
                span = AudioSpan(
                    buffer.source_id,
                    start_sample * 1000.0 / 16000,
                    end_sample * 1000.0 / 16000,
                    channel=channel,
                )
                evidence.append(
                    EvidenceItem(
                        evidence_id=self._stable_id(
                            buffer.source_id, self.metadata.name, channel,
                            start, end, self.model_id, self.revision,
                            self._resolved_revision, self.pool_frames,
                            self.metadata.version,
                        ),
                        span=span,
                        kind=EvidenceKind.CONTINUOUS_SPEECH_FEATURE,
                        producer=self.metadata.name,
                        producer_version=self.metadata.version,
                        payload={
                            "representation": self.metadata.representation,
                            "values": values,
                            "hidden_size": hidden_size,
                            "pool_frames": self.pool_frames,
                            "model_frame_start": start,
                            "model_frame_end": end,
                            "conv_receptive_field_samples": receptive,
                            "conv_stride_samples": stride,
                            "alignment": "DERIVED_VALID_CONV_GEOMETRY",
                            "model_id": self.model_id,
                            "requested_revision": self.revision,
                            "resolved_revision": self._resolved_revision,
                            "revision_binding": (
                                "EXACT_RESOLVED_REVISION"
                                if self._resolved_revision
                                else self.revision_binding
                            ),
                            "sampling_rate": 16000,
                            "device": self.device,
                            "trust_remote_code": False,
                            "safetensors_required": True,
                        },
                        derivation=(
                            "PCM samples from source WAV",
                            "Hugging Face AutoFeatureExtractor",
                            "pretrained Wav2Vec2 hidden states",
                            "contiguous time-window mean pooling",
                            "span derived from convolution geometry",
                        ),
                    )
                )
        return evidence
