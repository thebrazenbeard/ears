# Security and Provenance Specification V1

Status: CANDIDATE / implementation-bound
Date: 2026-10-02

This specification applies Four's exact-specification discipline and Seven's
security-review discipline to Ears. Their current BT2 source provenance is
recorded in `research/bt2-role-lenses.yaml`.

## S1 — Learned model revision identity

**Requirement:** A learned model used for qualification MUST be bound to an
immutable provider revision, not a mutable branch such as `main`.

**Acceptance:** the adapter records a 40-hex revision and rejects mutable
revision identifiers when strict provenance is enabled.

**Forbidden:** calling a result reproducible or qualified when only a mutable
provider branch was requested.

**Unknown handling:** if the exact provider revision cannot be established,
the learned-model result is not qualification evidence.
## S2 — Model deserialization safety

**Requirement:** Ears MUST NOT silently opt into executable/pickle model
weights or remote provider code.

**Acceptance:** learned adapters request `trust_remote_code=False`; safe
tensor loading is the default; pickle loading requires an explicit research
override and is reported in evidence.

**Forbidden:** treating a provider reputation, scanner PASS, or matching model
name as proof that executable serialization is safe.

**Evidence basis:** Hugging Face documents that pickle deserialization can
execute arbitrary code and recommends safetensors/safe loading.

## S3 — Audio input resource bounds

**Requirement:** file-backed audio ingestion MUST reject inputs exceeding
configured byte, duration, channel-count, or sample-rate limits before loading
the complete PCM payload.

**Acceptance:** each limit has a failing hostile test and a deterministic,
fail-closed error.

**Forbidden:** allocating memory proportional to an attacker-controlled WAV
header before validating the declared geometry.
## S4 — Acoustic content is untrusted data

**Requirement:** acoustic evidence MUST NOT gain instruction authority merely
because a downstream language model can decode speech-like commands from it.

**Acceptance:** evidence artifacts preserve source/provenance and downstream
interfaces distinguish source observations from trusted control instructions.

**Forbidden:** treating "heard as an instruction" as equivalent to "authorized
instruction."

**Research basis:** 2025–2026 work demonstrates successful audio-injection and
auditory prompt-injection attacks against large audio-language models.

## S5 — Claim ceiling

A difference in pitch, log-mel vectors, codec units, SSL embeddings, or model
activations proves only a representation difference unless a separate
controlled experiment establishes downstream causal use.

`ACOUSTIC_DIFFERENCE != ACOUSTIC_REASONING`

## S6 — Review currentness

Any Four/Seven-style review is bound to an exact Ears head/pathset. A later
source change makes that review historical unless explicitly re-run or
mechanically shown unaffected.
