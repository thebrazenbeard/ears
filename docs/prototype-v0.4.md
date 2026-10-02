# Prototype V0.4 — Optional Learned WavLM Adapter

Status: source implemented / optional backend not installed or runtime-executed in this work unit
Date: 2026-10-02

## Purpose

V0.4 adds the first learned speech-representation adapter without making learned infrastructure mandatory for Ears.

The adapter targets microsoft/wavlm-base-plus through Hugging Face AutoProcessor and AutoModel. The current model card exposes it as a feature-extraction model, and its preprocessor configuration specifies 16 kHz audio.

Sources:
- https://huggingface.co/microsoft/wavlm-base-plus
- https://huggingface.co/microsoft/wavlm-base-plus/blob/main/preprocessor_config.json

## Behavior

WavLMAdapter is lazy. Importing Ears does not import PyTorch or Transformers. The learned dependencies live behind the optional package extra named learned.

The adapter is opt-in from the CLI through the --wavlm flag and is never part of the default evidence path.

For each channel it produces one utterance-level CONTINUOUS_SPEECH_FEATURE by mean-pooling the model's hidden-state time axis. That is intentionally conservative: the whole utterance is the exact source span, so V0.4 does not fake frame-level alignment it has not yet proved.

The payload records model ID, requested revision, resolved revision when the backend exposes it, pooling method, sampling rate, device, and the learned vector.

Non-16 kHz input is rejected. Ears will not silently resample because resampling is itself a transformation that needs provenance.

## Current runtime observation

On the build machine used for this branch, Python 3.12 had NumPy but did not have torch, torchaudio, transformers, librosa, or soundfile installed. The Hugging Face cache did not contain WavLM weights.

Therefore V0.4 is source-level implementation plus fail-closed tests, not a successful WavLM runtime claim.

## Hostile review

> **HOSTILE REVIEWER:** An adapter that has never loaded its model is scaffolding, not evidence that Ears can extract WavLM representations.

**ACCEPTED.** The claim ceiling remains source implemented / optional backend unexecuted. A future qualification run must install the optional backend, bind an exact model revision, execute on controlled audio, and read back the resulting evidence artifact.

> **HOSTILE REVIEWER:** Mean pooling destroys timing, prosody, and local phonetic structure — exactly the information Ears cares about.

**ACCEPTED.** Mean pooling is only the first provenance-safe learned baseline. It tests whether a learned channel can enter the evidence system without pretending approximate model frames are exact source spans. The next learned iteration should derive and verify model-frame timing before exposing time-local WavLM evidence.

> **HOSTILE REVIEWER:** Using a mutable revision named main undermines reproducibility.

**ACCEPTED.** The adapter records both requested and resolved revisions. Qualification should use an immutable commit revision; main is convenience-only and cannot by itself establish a frozen result.

## Next frontier

Execute WavLM in an isolated environment only when the dependency/model download is intentionally authorized, then add a discrete speech-unit adapter and compare both against log-mel and cheap-prosody controls.
