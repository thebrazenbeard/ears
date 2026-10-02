from __future__ import annotations

from hashlib import sha256
import re
from typing import Any

from .adapters import AdapterMetadata
from .audio import PCMBuffer
from .model import AudioSpan, EvidenceItem, EvidenceKind


DEFAULT_WAVLM_REVISION = "4c66d4806a428f2e922ccfa1a962776e232d487b"
_IMMUTABLE_REVISION = re.compile(r"^[0-9a-fA-F]{40}$")


class OptionalDependencyUnavailable(RuntimeError):
    """Raised when an optional learned-representation backend is unavailable."""


class ModelPolicyError(ValueError):
    """Raised when learned-model provenance or loading policy is violated."""


class WavLMAdapter:
    """Optional WavLM utterance-level representation adapter.

    The adapter is lazy: importing Ears does not require torch or transformers.
    """

    metadata = AdapterMetadata(
        name="ears.wavlm",
        version="0.5.0",
        representation="wavlm_mean_pooled_hidden_state",
        learned=True,
        transcript_required=False,
    )

    def __init__(
        self,
        *,
        model_id: str = "microsoft/wavlm-base-plus",
        revision: str = DEFAULT_WAVLM_REVISION,
        device: str = "cpu",
        require_immutable_revision: bool = True,
    ) -> None:
        if require_immutable_revision and not _IMMUTABLE_REVISION.fullmatch(revision):
            raise ModelPolicyError(
                "learned-model revision must be an immutable 40-hex commit"
            )
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.require_immutable_revision = require_immutable_revision
        self._processor: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None
        self._resolved_revision: str | None = None

    @property
    def revision_binding(self) -> str:
        if _IMMUTABLE_REVISION.fullmatch(self.revision):
            return "EXACT_IMMUTABLE_REQUESTED_REVISION"
        return "MUTABLE_EXPLORATORY_REVISION"

    def processor_load_kwargs(self) -> dict[str, object]:
        return {
            "revision": self.revision,
            "trust_remote_code": False,
        }

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

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModel, AutoProcessor
        except ImportError as exc:
            raise OptionalDependencyUnavailable(
                "WavLMAdapter requires the optional 'learned' dependencies: "
                "torch and transformers"
            ) from exc

        processor = AutoProcessor.from_pretrained(
            self.model_id,
            **self.processor_load_kwargs(),
        )
        model = AutoModel.from_pretrained(
            self.model_id,
            **self.model_load_kwargs(),
        )
        model.to(self.device)
        model.eval()

        self._torch = torch
        self._processor = processor
        self._model = model
        self._resolved_revision = getattr(model.config, "_commit_hash", None)

    def process(self, buffer: PCMBuffer) -> list[EvidenceItem]:
        if buffer.sample_rate != 16000:
            raise ValueError(
                "WavLMAdapter currently requires 16 kHz PCM; "
                "resampling must be explicit and provenance-bound"
            )
        self._load()
        assert self._torch is not None
        assert self._processor is not None
        assert self._model is not None

        evidence: list[EvidenceItem] = []
        for channel, samples in enumerate(buffer.samples):
            inputs = self._processor(
                list(samples),
                sampling_rate=buffer.sample_rate,
                return_tensors="pt",
            )
            model_inputs = {
                key: value.to(self.device)
                for key, value in inputs.items()
            }
            with self._torch.no_grad():
                output = self._model(**model_inputs)
            hidden = output.last_hidden_state[0]
            pooled = hidden.mean(dim=0).detach().cpu().tolist()
            values = [round(float(value), 8) for value in pooled]

            span = AudioSpan(
                buffer.source_id,
                0.0,
                buffer.duration_ms,
                channel=channel,
            )
            evidence.append(
                EvidenceItem(
                    evidence_id=self._stable_id(
                        buffer.source_id,
                        self.metadata.name,
                        channel,
                        self.model_id,
                        self.revision,
                        self._resolved_revision,
                        self.metadata.version,
                    ),
                    span=span,
                    kind=EvidenceKind.CONTINUOUS_SPEECH_FEATURE,
                    producer=self.metadata.name,
                    producer_version=self.metadata.version,
                    payload={
                        "representation": self.metadata.representation,
                        "values": values,
                        "hidden_size": len(values),
                        "pooling": "mean_over_model_time_axis",
                        "model_id": self.model_id,
                        "requested_revision": self.revision,
                        "resolved_revision": self._resolved_revision,
                        "revision_binding": (
                            "EXACT_RESOLVED_REVISION"
                            if self._resolved_revision
                            else self.revision_binding
                        ),
                        "sampling_rate": buffer.sample_rate,
                        "device": self.device,
                    },
                    derivation=(
                        "PCM samples from source WAV",
                        "Hugging Face AutoProcessor",
                        "pretrained WavLM hidden states",
                        "mean pooling over model time axis",
                    ),
                )
            )
        return evidence
