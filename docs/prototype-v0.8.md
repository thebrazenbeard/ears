# Prototype V0.8 - Mimi Semantic Discrete Units

Status: candidate implementation on research branch / not merged
Date: 2026-10-06

## Trigger

Phase 2 still needs a learned discrete speech-unit condition that does not
silently collapse back into text.

A fresh provider read on 2026-10-06 found that kyutai/mimi at exact revision
89091b3e466eb6a9d11e537bf26b144f194978f7 publishes model.safetensors with
no pickle weight artifact. The exact provider config declares 24 kHz mono
input, a 12.5 Hz token frame rate, a 2048-entry codebook, and one semantic
quantizer. Transformers first exposes MimiModel in the v4.45.0 source tree.

## Implementation

V0.8 adds MimiSemanticUnitAdapter.

The adapter:

- pins the provider revision to a 40-hex commit;
- requests trust_remote_code=False and use_safetensors=True;
- requires Transformers >= 4.45;
- requires 24 kHz PCM rather than silently resampling;
- requests exactly one quantizer from Mimi.encode;
- verifies the loaded config declares exactly one semantic quantizer;
- emits one DISCRETE_SPEECH_UNIT evidence item per semantic-codebook frame.

Mimi's provider architecture calls this first codebook semantic. Ears preserves
that provider classification in payload metadata as
PROVIDER_DECLARED_SEMANTIC. It does not promote the label into evidence of
semantic understanding.

At 12.5 Hz, each emitted item receives a nominal 80 ms interval. This is a
codec-frame interval, not a measured receptive field, so the alignment field is
explicitly NOMINAL_CODEC_FRAME_INTERVAL_NOT_RECEPTIVE_FIELD.

## Why only the semantic codebook?

Mimi is a residual vector-quantized neural codec. Its additional codebooks carry
acoustic reconstruction detail. Feeding all residual codebooks into the D1
condition would make "discrete speech unit" mean "full codec representation."

V0.8 therefore uses only the provider-declared semantic quantizer. Full Mimi
codec tokens can be evaluated later as a richer discrete acoustic condition.

## Evidence boundary

Provider/source evidence now supports:

- exact provider revision identity;
- safetensors artifact presence at that revision;
- provider config values;
- Transformers source availability from v4.45.0 onward;
- source-level adapter behavior;
- dependency-free fake-model execution of the code-to-timeline path.

It does not yet support:

- local real-model execution;
- downloaded weight integrity beyond provider revision/artifact identity;
- phonological accuracy;
- semantic accuracy;
- improvement on an acoustic-required benchmark.

## Hostile review

> **HOSTILE REVIEWER:** The word "semantic" is doing too much work. It is a
> provider architecture label, not proof that the resulting integers correspond
> to human semantic units.

**ACCEPTED.** The evidence payload preserves the label as
PROVIDER_DECLARED_SEMANTIC and the claim ceiling forbids upgrading it.

> **HOSTILE REVIEWER:** Nominal 80 ms codec frames are not exact acoustic
> receptive fields.

**ACCEPTED.** V0.8 marks them as nominal codec-frame intervals. Exact
receptive-field reconstruction is not claimed.

> **HOSTILE REVIEWER:** A safe provider artifact still does not prove the local
> runtime works.

**ACCEPTED.** Runtime qualification remains open and separate from this source
implementation.

## Claim ceiling

PROVIDER_DECLARED_SEMANTIC_DISCRETE_UNIT != SEMANTIC_UNDERSTANDING

and

SOURCE_ADAPTER_IMPLEMENTED != LEARNED_RUNTIME_QUALIFIED
