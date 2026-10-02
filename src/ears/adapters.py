from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .audio import PCMBuffer
from .model import EvidenceItem


@dataclass(frozen=True, slots=True)
class AdapterMetadata:
    name: str
    version: str
    representation: str
    learned: bool
    transcript_required: bool


class EvidenceAdapter(Protocol):
    metadata: AdapterMetadata

    def process(self, buffer: PCMBuffer) -> Sequence[EvidenceItem]:
        ...


def run_adapters(
    buffer: PCMBuffer,
    adapters: Sequence[EvidenceAdapter],
) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for adapter in adapters:
        produced = list(adapter.process(buffer))
        evidence.extend(produced)
    return evidence
