"""Ears: evidence-preserving acoustic interfaces."""

from .counterfactual import compare_acoustic_counterfactual
from .model import AudioSpan, EvidenceItem, EvidenceKind, EvidenceTimeline
from .pipeline import inspect_wav
from .serialization import write_artifact

__all__ = [
    "AudioSpan",
    "compare_acoustic_counterfactual",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceTimeline",
    "inspect_wav",
    "write_artifact",
]

__version__ = "0.2.0"