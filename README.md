# Ears — acoustic-perception research seed

**Product direction:** a reusable, model-agnostic acoustic-perception component that represents sounds and phonetic structure without requiring a complete speech-to-text transcript as its primary output.

**Current status: concept and source-safety scaffold, not an implemented audio engine.** The current `main` branch has no microphone capture, audio ingestion, signal processing, phoneme recognizer, inference API, CLI, trained weights, server, installer, or audio-performance evaluation. A repository name and a research objective are not evidence that those capabilities exist.

## Intended problem

Speech-to-text systems optimize for words. Other agent and assistive interfaces may need lower-level acoustic evidence: timing, candidate phonetic structure, non-speech sounds, uncertainty, and contextual cues. Ears is exploring how to expose that kind of evidence as a bounded input to a separate system.

The intended design has three principles:

1. **Preserve the acoustic observation.** Do not silently turn a tentative sound into a definite word or an attributed speaker.
2. **Separate observation from inference.** Phonetic candidates, speaker hypotheses, and meaning require their own provenance and confidence.
3. **Keep integration model-neutral.** A future consumer should be able to use structured evidence without inheriting the identity, permissions, or state of the model that interpreted it.

These are research goals, **not features shipped by the current source**.

## What this repository contains today

| Surface | Verified state on `main` |
| --- | --- |
| Audio/phonetics runtime | **Not present** |
| Public Python/JavaScript package or command | **Not present** |
| Audio datasets, model checkpoints, or listening tests | **Not present** |
| Editor configuration | Tracked `.vscode` configuration with no `folderOpen` task |
| Static source-safety tests | `tests/test_editor_startup_safety.py` |
| Static UI font assets | Files in `public/fonts/`; these are not a working listening UI |

The repository's static font folder has historical documentation referring to a different UI. That text is **not** an Ears application description or evidence of an implemented acoustic frontend.

## Evaluate the current source

From a checkout with Python 3 available, run:

```bash
python -m unittest discover -s tests -v
```

The current tests inspect editor-startup configuration and assert absence of a previously disguised executable-like font path. They **do not** exercise microphones, models, audio processing, network access, or a deployed agent. A pass is only a source-tree safeguard; it cannot establish whether a prior checkout or another host executed an unsafe editor task.

No installation or audio quickstart is provided because there is no corresponding implementation on `main`.

## Qualification needed before making runtime claims

An initial usable acoustic module would need:

- an explicit audio-input interface, supported formats, consent and retention rules;
- deterministic audio fixtures with expected evidence output;
- documented representation of timing, phonetic hypotheses, uncertainty, and provenance;
- measured accuracy, latency, memory use, and failure/abstention behavior against appropriate baselines;
- an integration API with bounded effects and independent host authorization;
- security tests for malicious audio and untrusted metadata.

The presence of experimental branches or historical plans would not by itself satisfy these gates. Until implementation and tests reach `main`, Ears is a research direction, not a ready-to-integrate library.

## Rights and safety

No root project `LICENSE` file was present at this source inspection. Public GitHub visibility does not grant general redistribution or commercial-use rights; check provenance and licenses of any assets separately before reuse.

This README does not assert installed-device safety, consent to capture audio, authority to execute effects, or any model's subjective hearing experience.
