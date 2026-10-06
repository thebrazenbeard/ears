"""Ears: evidence-preserving acoustic interfaces."""

from .acoustic_tape import AcousticTapeAdapter
from .counterfactual import compare_acoustic_counterfactual
from .model import AudioSpan, EvidenceItem, EvidenceKind, EvidenceTimeline
from .pipeline import inspect_wav
from .serialization import write_artifact
from .wav2vec2 import Wav2Vec2Adapter
from .wavlm import OptionalDependencyUnavailable, WavLMAdapter

__all__ = [
    "AcousticTapeAdapter",
    "AudioSpan",
    "compare_acoustic_counterfactual",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceTimeline",
    "inspect_wav",
    "OptionalDependencyUnavailable",
    "Wav2Vec2Adapter",
    "WavLMAdapter",
    "write_artifact",
]

__version__ = "0.7.0"