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

**Partially implemented in V0.1.** The current package loads uncompressed PCM WAV audio, assigns content-addressed source identity, emits immutable time-bounded evidence items, computes deterministic frame-level acoustic observations, and serializes a portable manifest plus JSONL evidence stream.

Still open in Phase 1:

1. FLAC and broader audio decoding;
2. resampling/normalization with explicit provenance;
3. streaming/chunked ingestion instead of whole-file loading;
4. multiple learned or phonological evidence streams;
5. explicit revision semantics for incremental observations.

No LLM is required yet.

Current V0.1 artifact:

```
manifest.json
evidence.jsonl
```

The source audio is content-addressed but is **not copied by default**. Each evidence record identifies the producer/version and exact source span.

## Phase 2 — Baseline channels

Implement pluggable channels:

- deterministic VAD / silence / overlap timing;
- F0, energy, duration, rate and pause features;
- one continuous acoustic baseline (**V0.3 log-mel implemented**);
- one continuous SSL encoder (**V0.5 WavLM adapter exact-pinned and hardened; safe runtime blocked by pickle-only upstream artifact**);
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
