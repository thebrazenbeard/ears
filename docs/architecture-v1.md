# Ears Architecture V1 — Evidence-Preserving Acoustic Interface

Status: candidate architecture / not implemented  
Date: 2026-10-02

## 1. Objective

Build a machine-hearing interface in which spoken-language reasoning can inspect acoustic evidence without depending on a transcript as the sole intermediate representation.

The V1 architecture is deliberately model-agnostic. It should let us swap WavLM-like continuous features, HuBERT/phonological units, Mimi-style codec tokens, and ASR systems without rewriting the evidence contract.

## 2. Core data model

Every observation must be time-bound to source audio.

```
AudioSpan
  source_id
  start_ms
  end_ms
  sample_rate
  channel

EvidenceItem
  evidence_id
  span
  kind
  representation
  producer
  producer_version
  confidence_or_quality
  derivation
```

Candidate `kind` values:

- `WAVEFORM_REFERENCE`
- `CONTINUOUS_SPEECH_FEATURE`
- `DISCRETE_SPEECH_UNIT`
- `PHONE_HYPOTHESIS`
- `PROSODIC_OBSERVATION`
- `NON_SPEECH_EVENT`
- `SPEAKER_TURN_EVENT`
- `TRANSCRIPT_HYPOTHESIS`
- `INTERPRETIVE_HYPOTHESIS`

The important boundary is:

```
OBSERVABLE_ACOUSTIC_EVIDENCE != INTERPRETIVE_HYPOTHESIS
```

Examples:

- measured F0 contour -> evidence;
- 420 ms pause -> evidence;
- ASR token with posterior/confidence -> evidence/hypothesis from a named producer;
- "speaker is angry" -> interpretation;
- "the pause indicates deception" -> unsupported interpretation unless separately qualified.

## 3. Processing graph

```
                   +----------------------+
mic/file ----------> audio normalization  |
                   +----------+-----------+
                              |
                     immutable span clock
                              |
       +----------------------+-----------------------+
       |                      |                       |
       v                      v                       v
continuous encoder      unit/token path        signal observables
(WavLM/etc.)            (HuBERT/Mimi/etc.)     (F0/energy/timing)
       |                      |                       |
       +------------+---------+-----------------------+
                    |
             evidence timeline
                    |
          +---------+----------+
          |                    |
          v                    v
    optional ASR         non-speech / turn
    hypotheses           event analysis
          |                    |
          +---------+----------+
                    |
             fusion / adapter
                    |
             reasoning client
```

No edge from ASR is allowed to erase the other branches.

## 4. Multi-resolution policy

V1 should preserve a cheap default representation plus richer evidence for selective inspection.

Suggested levels:

- **L0 — timing/event metadata:** speech activity, overlap, silence, gross acoustic events.
- **L1 — compact linguistic-acoustic representation:** continuous pooled features or low-rate semantic/phonological units.
- **L2 — prosodic and phone-level detail:** phone hypotheses, pitch/rhythm contours, local spectral/voice-quality features.
- **L3 — source audio / reconstruction-capable representation:** used only when needed.

This is intentionally analogous to a cache hierarchy: do not force every reasoning step to pay the full waveform/token cost.

## 5. Transcript policy

ASR is an observer, not an authority.

A transcript record should support:

```
{
  "text": "...",
  "span": [start_ms, end_ms],
  "producer": "...",
  "alternatives": [...],
  "confidence": ...,
  "alignment": ...
}
```

If a transcript disagrees with acoustic or phone evidence, record both.

A later reasoning layer may choose text for efficiency. That choice must remain reversible when the task becomes acoustically ambiguous.

## 6. Streaming requirements

For live conversation:

- operate causally or near-causally;
- emit partial evidence before end-of-turn;
- preserve revisions rather than pretending early hypotheses were final;
- represent overlap rather than forcing one-speaker-at-a-time turns;
- support interruption/backchannel events;
- separate capture latency, representation latency, and reasoning latency.

Moshi's full-duplex architecture is an important reference point, but Ears does not assume Moshi's exact codec or model.

## 7. Candidate V1 stack

The first prototype should prefer existing open models:

- continuous representation: WavLM or comparable SSL encoder;
- discrete comparison: HuBERT clustering and/or Mimi-derived units;
- transcript baseline: Whisper-class ASR;
- prosody: deterministic signal features (F0, energy, duration, pause/overlap timing);
- storage: simple time-indexed JSON/Arrow/Parquet artifact;
- evaluator: task-specific harness that can expose or mask channels.

No foundation-model training is required to answer the first architectural questions.

## 8. Privacy and identity boundary

Speech contains biometric and sensitive information.

V1 should support:

- local feature extraction where feasible;
- explicit raw-audio retention policy;
- derived-feature retention independent of raw-audio retention;
- speaker identity disabled by default unless a task requires it;
- provenance for every externally produced embedding/token;
- no inference of protected/sensitive traits merely because a model can attempt it.

A representation that accidentally encodes speaker identity is not automatically disqualified, but the leakage should be measured.

## 9. Falsifiers

The V1 architecture should be abandoned or materially revised if:

1. fused acoustic evidence does not outperform transcript-only baselines on tasks designed to require acoustic information;
2. the useful gain can be matched by a tiny set of deterministic prosody features;
3. latency/compute cost makes streaming interaction impractical;
4. representation instability prevents reproducible downstream behavior;
5. identity leakage or privacy cost is disproportionate to the task gain.

## 10. Current architectural decision

Do **not** begin by training "the Ears tokenizer."

Begin by constructing the evidence timeline and plugging in multiple existing representations. The first job is to learn what information a useful machine-hearing interface actually needs to preserve.
