# Prototype V0.1 — Evidence Timeline

Status: implemented on research branch / not merged / not a machine-hearing claim
Date: 2026-10-02

## Purpose

V0.1 establishes the first executable Ears invariant:

> Acoustic evidence can be serialized, time-aligned, and inspected without requiring a transcript.

The implementation intentionally uses only Python's standard library. It is not an ASR system and it is not yet a learned audio representation.

## What it does

The CLI command ears inspect INPUT.wav --out OUTPUT reads an uncompressed PCM WAV file and writes:

- manifest.json — source hash, timing, channel count, and representation counts;
- evidence.jsonl — time-bound evidence items.

V0.1 emits two evidence kinds:

- WAVEFORM_REFERENCE;
- ACOUSTIC_FRAME_OBSERVATION.

Each frame records deterministic RMS energy, absolute peak, zero-crossing rate, sample count, and exact source span.

## What it proves

It proves only that Ears now has an executable provenance and timing substrate on which richer acoustic representations can be attached.

It does not prove speech recognition, phone recognition, prosody understanding, audio-language reasoning, machine hearing, or subjective hearing.

## Why start this low

A learned encoder can always be added later. A bad evidence boundary is much harder to repair after every model adapter assumes transcripts or opaque embeddings are canonical.

The V0.1 timeline therefore makes source identity, span identity, producer identity, and derivation explicit before adding WavLM, HuBERT, Mimi, Whisper, or another model.

## Hostile review

> **HOSTILE REVIEWER:** RMS and zero-crossing rate are toy signal features. Calling this "Ears" could create an illusion of progress toward actual speech understanding.

**ACCEPTED.** These features are deliberately not credited as hearing. Their only job is to prove that the evidence substrate preserves time-bound acoustic information without a transcript. The next stage must add learned or phonological representations and then beat transcript-only baselines on acoustic-required tasks.

> **HOSTILE REVIEWER:** The current reader loads the whole WAV into memory, which is incompatible with the project's eventual live-streaming goal.

**ACCEPTED.** V0.1 is an offline contract probe. Streaming ingestion is a required later phase; no live-hearing claim attaches to this implementation.

## Next probe

The next implementation should add one cheap acoustic/prosodic channel and one learned speech representation behind adapters while preserving the same timeline contract.

The first real falsification experiment is same transcript, different acoustics: paired utterances with identical lexical content but different stress or timing must remain distinguishable before any language-reasoning stage is credited.
