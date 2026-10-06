# Prototype V0.6 - Acoustic Tape

Status: candidate implementation on research branch / not merged
Date: 2026-10-06

## Trigger

Ears needs a deliberately simple answer to a useful architectural question:
can a machine consume a compact, time-ordered representation of sound without
first converting the sound into orthographic text?

The "tape" metaphor is intentionally literal only at the representation level:
audio becomes a sequential machine-readable stream. This is not a claim that
cassette encoding itself provides language understanding.

## Implementation

V0.6 adds AcousticTapeAdapter, a deterministic discrete acoustic baseline.

Each time-aligned frame produces one symbol containing:

- a fixed-level RMS energy bin;
- a fixed-level spectral-shape code derived from frame-local log-mel bands;
- exact source-span provenance through the normal EvidenceItem contract.

The representation uses no transcript and no learned model. It requires no
source-global statistics: spectral normalization is frame-local and energy
quantization uses fixed bounds, so later streaming work does not need future
audio merely to reproduce the symbolization rule.

The default evidence timeline now emits DISCRETE_ACOUSTIC_SYMBOL records
alongside continuous log-mel and prosodic evidence.

## Counterfactual use

The acoustic counterfactual report now includes a linear-time disagreement rate
between corresponding positions in the two time-ordered acoustic-symbol streams,
plus the symbol-count delta. This lets same-lexical-control
experiments ask whether a compact discrete stream preserved an acoustic
difference.

The metric proves representation difference only. It does not establish that a
reasoning model used the difference. It is deliberately alignment-sensitive: a
timing shift can raise disagreement even when local acoustic content is similar.
That limitation is exposed rather than hidden behind an expensive unconstrained
sequence alignment.

## Why this is not the Phase 2 speech-unit path

Acoustic Tape is deliberately a control.

It is not:

- a phone recognizer;
- a HuBERT/Mimi-style learned unit stream;
- a semantic tokenizer;
- a replacement for the planned learned discrete speech-unit condition.

Its value is that it is cheap, deterministic, auditable, streamable in
principle, and capable of falsifying a stronger tokenizer that fails to beat it.

## Hostile review

> **HOSTILE REVIEWER:** This mostly discretizes information already present in
> log-mel and RMS features. It may add no information at all.

**ACCEPTED.** V0.6 is a compression/control representation, not a new sensory
capability. A learned discrete path earns its complexity only if it performs
better on downstream acoustic-required tasks.

> **HOSTILE REVIEWER:** A source-normalized code would quietly use future audio
> and undermine streaming claims.

**ACCEPTED AND AVOIDED.** V0.6 uses frame-local spectral normalization and fixed
energy bounds. It does not use utterance-global min/max statistics.



> **HOSTILE REVIEWER:** Full edit distance over 100 Hz symbol streams is quadratic
> and can become pathological on Ears' multi-hour input ceiling.

**ACCEPTED AND REPLACED.** V0.6 uses an O(n) aligned disagreement rate and
reports stream-length difference separately. More sophisticated time-warped
comparison belongs in the evaluation harness with explicit resource bounds.

## Claim ceiling

DISCRETE_ACOUSTIC_SYMBOL_DIFFERENCE != DISCRETE_SPEECH_UNDERSTANDING

V0.6 supports a low-tech, no-text representation experiment. It does not prove
phonetic recognition, semantic reasoning, hearing, or superiority to existing
audio-language systems.
