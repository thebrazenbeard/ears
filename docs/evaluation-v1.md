# Evaluation V1 — Does Ears Hear Anything Text Loses?

Status: candidate falsification suite  
Date: 2026-10-02

## 1. Main experimental question

Does direct acoustic evidence improve reasoning on tasks where a transcript is incomplete, ambiguous, wrong, or structurally incapable of carrying the relevant information?

A system is not credited merely for having an audio encoder. It must demonstrate a measured benefit attributable to the acoustic channel.

## 2. Required ablations

Every core benchmark should compare, where technically possible:

- **T:** transcript only;
- **P:** transcript + deterministic prosodic/timing features;
- **C:** continuous speech representation without transcript;
- **D0:** deterministic discrete acoustic symbols without transcript (Acoustic Tape control);
- **D1:** learned discrete speech units without transcript;
- **F:** fused acoustic representation + transcript;
- **A:** richer/raw or reconstruction-capable audio path where feasible.

This prevents "audio model" from becoming a label rather than evidence.

## 3. Test families

### Phonetic discrimination

Use minimal pairs, reduced speech, coarticulation, accents, disfluencies, and noisy speech.

Measure:
- segment/word discrimination;
- calibrated alternatives;
- robustness under degradation.

### Prosody-sensitive meaning

Construct utterances whose lexical transcript stays constant while stress, boundary tone, timing, or emphasis changes.

Example family:

```
"I didn't say she stole the money."
```

Shift emphasis across words and ask questions that depend on the contrast.

Do not treat a single scripted sentence as sufficient evidence; generate multiple speakers, phrasings, and contexts.

### Turn-taking and interaction

Evaluate:
- interruption;
- overlap;
- backchannel;
- abandoned starts;
- self-correction;
- long hesitation;
- rapid turn handoff.

Transcript-only baselines may receive identical words but not the original timing unless timing is explicitly part of that condition.

### Transcript contradiction

Intentionally provide an incorrect or low-confidence transcript while preserving the original audio.

Ask whether the system:
- notices conflict;
- requests/uses acoustic evidence;
- avoids laundering the transcript into fact.

### Non-speech context

Test laughter, sighs, coughs, alarms, door knocks, engine/noise context, and other events only where they are relevant to the task.

### Paralinguistic reasoning

Use CP-Bench / ParaS2S / ParA-Bench-style tasks where licensing and benchmark conditions permit.

Separate:
- directly observable acoustic attributes;
- conventional labels;
- inferred affect/intent.

Score false inferences explicitly.

### Adversarial acoustic ambiguity

Include:
- clipping;
- reverberation;
- background speech;
- packet loss;
- codec degradation;
- adversarially plausible ASR alternatives.

The desired behavior is calibrated uncertainty, not forced certainty.

## 4. Metrics

At minimum:

- task accuracy / F1 as appropriate;
- calibration error or Brier-style score for uncertain outputs;
- contradiction-detection rate;
- false acoustic/affective inference rate;
- abstention quality;
- word/phone error where relevant;
- end-to-end and per-stage latency;
- real-time factor;
- representation frame/token rate;
- discrete-stream disagreement/compression behavior under controlled acoustic changes;
- representation storage/bitrate;
- compute/memory footprint;
- speaker-identity leakage where measurable.

## 5. Anti-gaming rules

- Keep held-out speakers and recording conditions.
- Preserve failed attempts.
- Do not tune on the final hidden acoustic contrasts.
- Track source/license/provenance for every test set.
- Keep transcript and audio conditions paired exactly.
- Do not let one condition receive timing metadata that another condition is supposed to lack.
- Report confidence intervals where sample size permits.
- Report negative results.

## 6. Success criteria

Ears V1 earns a positive result only if a non-transcript acoustic path produces a reproducible improvement on at least one task family where:

1. transcript-only performance is meaningfully bounded by information loss;
2. the gain survives speaker/environment holdout;
3. the gain is not explained by leaked labels or benchmark contamination;
4. latency and compute are reported;
5. the failure cases remain visible.

This is deliberately weaker than a claim of general "hearing."

## 7. Hostile review

> **HOSTILE REVIEWER:** If the benchmark is designed so text must fail, Ears can "win" by construction without becoming broadly useful.

**ACCEPTED.** The suite needs two categories: acoustic-required tasks and ordinary conversational tasks. Ears must gain where acoustic information matters without materially degrading lexical reasoning where text is sufficient.

> **HOSTILE REVIEWER:** Prosody labels are subjective.

**ACCEPTED.** Prefer physically measurable contrasts and task outcomes over subjective affect labels; when human judgment is required, use multiple raters and preserve disagreement.

> **HOSTILE REVIEWER:** A giant proprietary audio model could dominate every comparison and teach us nothing about the representation.

**ACCEPTED.** Separate system-level performance from representation-level ablations. The V1 question is architectural, not a leaderboard contest.
