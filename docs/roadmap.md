# Roadmap

Status: research/build plan  
Date: 2026-10-02

## Phase 0 — Preserve the question

Done in this branch:

- define Ears as acoustic-first rather than transcript-exclusive;
- survey self-supervised speech features, discrete units, speech codecs, speech-native LMs, and current paralinguistic benchmarks;
- define an evidence-preserving candidate architecture;
- define falsification-oriented evaluation.

## Phase 1 — Evidence timeline prototype

Build a local Python package that:

1. loads WAV/FLAC audio;
2. normalizes/resamples while preserving source timing;
3. emits immutable time spans;
4. attaches multiple evidence streams to those spans;
5. serializes a portable artifact.

No LLM is required yet.

Suggested artifact:

```
ears.jsonl
source.wav
manifest.json
```

Each record should identify the producer/model version and source span.

## Phase 2 — Baseline channels

Implement pluggable channels:

- deterministic VAD / silence / overlap timing;
- F0, energy, duration, rate and pause features;
- one continuous SSL encoder;
- one discrete speech-unit path;
- one ASR path.

Avoid hidden global state. Every derived record must be reproducible from the source artifact plus declared model/version.

## Phase 3 — Comparative harness

Run the same tasks under channel masks:

- transcript only;
- transcript + cheap acoustic features;
- continuous only;
- discrete only;
- fused.

This is the point where the repo should earn or reject the hybrid hypothesis.

## Phase 4 — Reasoning adapter

Only after Phase 3:

- project compact acoustic representations into a language-reasoning model;
- preserve source-span references;
- support "rehydration" of richer acoustic evidence for ambiguous spans;
- measure latency and context cost.

## Phase 5 — Streaming

Add causal processing and incremental revision:

- partial speech units/features;
- partial ASR hypotheses;
- turn/overlap events;
- correction/revision semantics;
- bounded buffering.

Target conversational behavior, not offline batch transcription.

## Phase 6 — Representation research

If existing representations are demonstrably inadequate, then investigate an Ears-specific representation objective:

- preserve phonological contrast;
- preserve prosodic contrast;
- minimize irrelevant speaker identity;
- remain streamable;
- minimize sequence rate;
- retain enough acoustic detail to resolve ambiguity;
- support cross-speaker and cross-accent generalization.

Possible research inspiration:
- HuBERT-style masked unit prediction;
- WavLM-style denoising/robustness;
- SpeechTokenizer/Mimi residual quantization;
- 2026 phonological-tokenizer multi-objective training.

## Non-goals for early phases

- training a giant audio foundation model;
- replacing all ASR;
- voice cloning;
- inferring private mental states;
- claiming consciousness or human-equivalent hearing;
- optimizing benchmark scores before the evidence interface is stable.

## Decision gates

**Gate A:** Does acoustic evidence beat transcript-only where it should?  
If no, stop or narrow scope.

**Gate B:** Do learned representations materially beat cheap deterministic prosody features?  
If no, keep the simpler system.

**Gate C:** Do discrete units beat continuous features enough to justify quantization?  
If no, use continuous features.

**Gate D:** Does a custom Ears tokenizer have a measured target that existing encoders cannot satisfy?  
If no, do not train one.

**Gate E:** Can the system operate with conversational latency?  
If no, the live-hearing claim remains unqualified.
