"""Ears: evidence-preserving acoustic interfaces."""

from .counterfactual import compare_acoustic_counterfactual
from .model import AudioSpan, EvidenceItem, EvidenceKind, EvidenceTimeline
from .pipeline import inspect_wav
from .serialization import write_artifact
from .wavlm import OptionalDependencyUnavailable, WavLMAdapter

__all__ = [
    "AudioSpan",
    "compare_acoustic_counterfactual",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceTimeline",
    "inspect_wav",
    "OptionalDependencyUnavailable",
    "WavLMAdapter",
    "write_artifact",
]

__version__ = "0.5.1"