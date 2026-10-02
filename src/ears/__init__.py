"""Ears: evidence-preserving acoustic interfaces."""

from .model import AudioSpan, EvidenceItem, EvidenceKind, EvidenceTimeline
from .pipeline import inspect_wav
from .serialization import write_artifact

__all__ = [
    "AudioSpan",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceTimeline",
    "inspect_wav",
    "write_artifact",
]

__version__ = "0.1.0"