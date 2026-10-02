# Prototype V0.3 — Representation Adapters + Log-Mel Baseline

Status: implemented on research branch / not merged / not a learned-speech claim
Date: 2026-10-02

## Purpose

V0.3 separates the Ears evidence contract from any one acoustic representation and adds the first higher-dimensional continuous acoustic baseline.

## Adapter contract

An EvidenceAdapter declares metadata describing its representation, version, whether it is learned, and whether it requires a transcript. The runner accepts a PCM buffer and returns evidence items that remain bound to source spans.

This prevents a future WavLM, HuBERT, Mimi, or other backend from becoming an implicit authority merely because it produced an embedding.

## Log-mel baseline

The built-in LogMelAdapter emits CONTINUOUS_ACOUSTIC_FEATURE evidence using a Hann window, power spectrum, triangular mel filterbank, and log compression.

The adapter is deterministic and transcript-free. It is not learned and is not credited as a speech-semantic representation.

The counterfactual report now includes an L2 distance between mean continuous acoustic vectors. This gives the same-transcript/different-acoustics program a richer separation metric than pitch or RMS alone.

## What this changes

The project now has three distinct acoustic evidence levels:

- cheap scalar frame observations;
- explicit prosodic hypotheses such as F0;
- higher-dimensional continuous acoustic vectors.

Those channels can disagree without any one of them being promoted to canonical truth.

## Hostile review

> **HOSTILE REVIEWER:** Log-mel features are old signal processing, not the neural representation needed for genuine speech understanding.

**ACCEPTED.** They are a control condition and adapter-contract test. The value is that a learned encoder must now beat a transparent baseline instead of merely existing.

> **HOSTILE REVIEWER:** Making log-mel part of the default pipeline increases artifact size and compute even when a caller only wants provenance.

**PARTIALLY ACCEPTED.** V0.3 keeps the default enabled to exercise the multi-channel architecture, but the pipeline should next expose explicit channel selection so cost is caller-controlled.

## Next frontier

1. make channel selection explicit and machine-readable;
2. add one optional learned continuous speech adapter;
3. add one optional discrete-unit adapter;
4. keep both disabled when dependencies or weights are absent;
5. compare each against transcript-only, cheap prosody, and log-mel controls.
