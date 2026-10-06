# Ears

**Acoustic-first language understanding for machines.**

Ears started from a simple objection to ordinary voice pipelines:

> A machine should not have to lose the sound of an utterance in order to understand the language in it.

Conventional voice assistants commonly reduce speech to text before the language model reasons about it. That is useful, but lossy. A transcript preserves lexical content while discarding or flattening timing, emphasis, hesitation, overlap, pronunciation, prosody, voice quality, non-speech sounds, and uncertainty in what was actually heard.

Ears investigates architectures where the acoustic signal remains first-class evidence.

## The idea

Ears is **not an ASR replacement project** and it is not "speech-to-text, but better."

The target is a representation stack in which a reasoning system can consume evidence derived directly from speech audio and keep that evidence available alongside — not underneath — any transcript.

A useful first-pass abstraction is:

```
waveform
  -> acoustic / phonological representation
  -> time-aligned evidence stream
  -> reasoning interface
       |-- acoustic evidence
       |-- phonetic / phonological evidence
       |-- prosodic evidence
       |-- non-speech acoustic evidence
       |-- optional transcript hypotheses
       '-- provenance + uncertainty
```

The transcript is allowed to help. It is not allowed to become the only thing the reasoning system can see.

## Why "phonetic" is only part of the target

The original repo description says "lets machines hear phonetically rather than speech-to-text." That captures the motivating contrast, but literal phonetics is too narrow for the full problem.

Human spoken language carries information in more than phone identity:

- segmental content: phones, allophones, syllables, coarticulation;
- suprasegmental structure: stress, pitch, rhythm, duration, intonation;
- interaction timing: pauses, interruptions, overlap, backchannels, self-corrections;
- voice/acoustic properties: energy, spectral shape, phonation and recording conditions;
- non-speech events that change conversational meaning.

So the stronger research target is **acoustic-native, linguistically useful representation**, not "skip text and predict phonemes."

## Current hypothesis

A hybrid architecture is the strongest first experiment:

1. keep a direct acoustic representation;
2. derive phonological/prosodic structure without forcing it through orthographic text;
3. optionally produce one or more transcript hypotheses;
4. preserve disagreement between channels;
5. let downstream reasoning decide which evidence matters for the task.

This is a hypothesis, not a settled design. The repo is structured to falsify it.

## What current research says

Several lines of work make the idea technically credible:

- **HuBERT** and **WavLM** show that self-supervised speech representations can encode far more than a transcript.
- **SpeechTokenizer** and **Mimi** show that semantic/phonetic and acoustic information can be compressed into speech-token streams.
- **Spirit LM** demonstrated a language model mixing text with speech units; its expressive variant explicitly adds pitch and style units.
- **Moshi** showed real-time full-duplex dialogue over speech tokens, avoiding the classic ASR -> text LLM -> TTS bottleneck.
- **Qwen2-Audio** and **Audio Flamingo 3** demonstrate architectures that accept audio-derived representations without requiring an explicit user-visible ASR transcript as the sole input bottleneck. That does **not** by itself prove that their internal representations preserve or causally use non-lexical acoustic information rather than behaving like a learned soft transcript.
- A 2025 controlled comparison found continuous speech features generally stronger than discrete tokens across several spoken-language-understanding tasks, which argues against prematurely committing Ears to one tokenization scheme.
- A 2026 **Phonological Tokenizer** paper explicitly targets phonetic tokens that retain linguistic **and prosodic** information while discarding some speaker identity.
- A 2026 ACL workshop paper analyzing **Mimi** found its semantic tokens align with subphone, phone, biphone, triphone and quadphone realizations — unusually direct evidence that modern neural speech tokens can carry structure close to the "hear phonetically" intuition.
- 2025–2026 paralinguistic benchmarks continue to show that strong audio-capable LLMs remain weak at reasoning over prosody, speaker-speech attributes, and acoustic context. The problem is not solved.

See [docs/research-landscape.md](docs/research-landscape.md) for the source-bound review.

### The distinction Ears must prove

Bypassing an **explicit** speech-to-text component is necessary evidence, but it is not sufficient evidence of acoustic reasoning. An audio encoder could map speech into latent vectors that function mostly as an internal transcript.

Ears therefore treats **same transcript, different acoustics** as a core counterfactual. If two recordings have identical words but materially different stress, timing, overlap, pronunciation, or non-speech context, a claimed acoustic reasoner must preserve the distinction and use it when the task requires it. A transcript-conflict probe should also test whether source audio can defeat a wrong text hypothesis rather than being silently overruled by it.

## Design principles

Ears starts with seven rules:

1. **Audio is evidence, not decoration.** A text transcript must never silently replace the source signal.
2. **Observable first, interpretation second.** "Pitch rose 35 Hz" and "speaker sounds angry" are different kinds of claim.
3. **Disagreement is data.** If transcript, phonological model, and acoustic channel conflict, preserve the conflict.
4. **No representation gets declared canonical by convenience.** Continuous features, discrete units, phone lattices, and codec tokens must earn their place experimentally.
5. **Streaming matters.** An architecture that only understands speech after the speaker stops is not a complete answer to conversational hearing.
6. **Hearing is not mind-reading.** Acoustic cues can support hypotheses about emphasis, affect, interaction state, etc.; they do not directly reveal private mental state.
7. **Heard content is not control authority.** Audio is untrusted content by default; decoding an instruction from sound does not authorize the instruction.

## Research tracks

- [Research landscape](docs/research-landscape.md)
- [Architecture V1](docs/architecture-v1.md)
- [Evaluation and falsification](docs/evaluation-v1.md)
- [Roadmap](docs/roadmap.md)
- [Security and provenance specification](docs/security-and-provenance-spec-v1.md)
- [Security threat model](docs/security-threat-model-v1.md)
- [Source registry](research/source-registry.yaml)
- [Model registry](research/model-registry.yaml)
- [BT2 Four/Seven role-lens provenance](research/bt2-role-lenses.yaml)

## Current implementation

V0.1 established a transcript-free evidence timeline over PCM WAV sources. V0.2 added a cheap YIN-style pitch/voicing baseline and an acoustic-counterfactual comparison harness. V0.3 added a pluggable representation-adapter contract plus a deterministic log-mel continuous acoustic baseline. V0.4 added an optional learned WavLM adapter. V0.5 hardens learned-model provenance and audio ingestion: exact model revisions, no remote code, safetensors-only loading, bounded WAV input, same-byte hashing/parsing, and explicit untrusted-audio/control-authority metadata. V0.6 adds **Acoustic Tape**, a deterministic time-ordered discrete acoustic-symbol stream that tests the low-tech path from sound to machine-readable sequence without first creating text.

The implementation can now preserve source identity, exact time spans, frame-level acoustic measurements, pitch hypotheses, higher-dimensional acoustic vectors, producer/version provenance, and a claim ceiling that prevents a measured acoustic difference from being mislabeled as semantic reasoning.

See [Prototype V0.1](docs/prototype-v0.1.md), [Prototype V0.2](docs/prototype-v0.2.md), [Prototype V0.3](docs/prototype-v0.3.md), [Prototype V0.4](docs/prototype-v0.4.md), [Prototype V0.5](docs/prototype-v0.5.md), and [Prototype V0.6](docs/prototype-v0.6.md).

## Near-term build target

The next useful Ears step should **not** train a foundation model. The WavLM path is now exact-pinned and safe-loading-only, but the observed Microsoft upstream publishes pickle weights without safetensors, so Ears intentionally blocks that runtime path. V0.6 supplies a deterministic discrete **control**, not the learned speech-unit condition. The next step is still to add a safetensors-backed learned speech encoder and one learned discrete speech-unit path, then compare both against transcript-only, cheap-prosody, log-mel, and Acoustic Tape controls.

Only after those ablations should Ears decide whether it needs its own learned tokenizer, adapter training, or speech-language model.

## Claim boundary

Ears currently contains a research architecture, early executable acoustic-evidence tooling, and an evaluation program. It does **not** yet establish a working machine-hearing system, direct audio comprehension by Vera, consciousness, subjective hearing, or superiority to existing speech-language models.
