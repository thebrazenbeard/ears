# Prototype V0.2 — Cheap Prosody + Acoustic Counterfactuals

Status: implemented on research branch / not merged / not a machine-hearing claim
Date: 2026-10-02

## Why V0.2 exists

The conversation exposed a critical distinction: bypassing explicit ASR does not prove that a model reasons from acoustic information. A learned audio encoder can still act like a soft transcript.

V0.2 turns that objection into executable structure.

## Added evidence channel

Ears now emits PROSODIC_OBSERVATION records in addition to waveform references and frame-level signal measurements.

The current pitch path is deliberately cheap and transparent: a small YIN-style cumulative-mean-normalized difference estimator over PCM windows. It emits fundamental-frequency hypotheses, voicing confidence, and RMS energy with exact source spans.

This is a baseline, not a production pitch tracker.

## Added counterfactual harness

The new compare path takes two audio sources and summarizes measurable acoustic differences while preserving the epistemic status of any claimed lexical equivalence.

If a caller supplies the same words as a lexical control, the report marks them USER_DECLARED_UNVERIFIED. Ears does not silently convert that annotation into proof that the recordings contain the same transcript.

The report is explicitly capped at ACOUSTIC_DIFFERENCE_ONLY_NOT_SEMANTIC_REASONING.

This gives the project a place to run the central experiment later:

1. hold lexical content constant;
2. vary stress, timing, pitch, overlap, pronunciation, or non-speech context;
3. verify that the acoustic representation preserves the difference;
4. then test whether a downstream reasoner causally uses that difference.

Only step 4 begins to support a claim of acoustic reasoning.

## Hostile review

> **HOSTILE REVIEWER:** Detecting a pitch difference between two sine waves is trivial and says nothing about speech understanding.

**ACCEPTED.** The synthetic tests qualify the plumbing and estimator only. They are not evidence that Ears understands speech. Real spoken counterfactuals with held-out speakers and lexical controls remain required.

> **HOSTILE REVIEWER:** A hand-built pitch channel could bias the project toward features humans already know to look for and miss useful latent acoustics.

**ACCEPTED.** The cheap channel is a control condition, not the intended ceiling. Learned continuous and discrete representations must be compared against it. If they add nothing measurable, their extra complexity loses.

## Next frontier

Add a pluggable representation-adapter contract, then integrate one continuous self-supervised speech encoder and one discrete-unit path without allowing either to erase source-span provenance.
