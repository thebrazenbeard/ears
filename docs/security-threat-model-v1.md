# Ears Security Threat Model V1

Status: CANDIDATE HOSTILE MODEL
Date: 2026-10-02
Method: BT2 Seven threat-modeling discipline, applied internally

## Assets and trust boundaries

Assets include source audio, acoustic evidence artifacts, model weights,
adapter code, model/provider revision identity, downstream reasoning context,
user authority, privacy-sensitive voice characteristics, and evaluation
results.

Primary trust boundaries:
1. external audio -> decoder;
2. decoded PCM -> evidence producers;
3. evidence -> downstream reasoner;
4. model registry/provider -> local learned adapter;
5. research result -> qualification claim.

Audio is untrusted content by default. Model repositories are external
supply-chain inputs. A model response is not authority.
## Hostile families

### H1 — Oversized WAV / memory exhaustion
Invariant: declared input geometry is bounded before full-frame allocation.
Oracle: oversized byte/duration/channel/rate input fails closed.

### H2 — Malformed geometry
Invariant: impossible or contradictory PCM geometry is rejected.
Oracle: no partial artifact is emitted as valid evidence.

### H3 — Mutable model revision drift
Invariant: qualification binds an immutable provider commit.
Oracle: `main`, tags, or unresolved aliases fail strict provenance.

### H4 — Executable model serialization
Invariant: pickle/executable weights are denied by default.
Oracle: a model repo lacking safetensors cannot silently downgrade to pickle.

### H5 — Remote-code widening
Invariant: provider-defined Python is not trusted implicitly.
Oracle: learned loaders set `trust_remote_code=False`.
### H6 — Auditory prompt injection
Invariant: acoustic content does not acquire control authority.
Oracle: malicious spoken/imperceptible instructions remain tainted input,
not privileged control.

### H7 — Transcript laundering
Invariant: a transcript hypothesis cannot overwrite contradictory acoustic
evidence or provenance.
Oracle: conflict remains inspectable.

### H8 — Representation claim inflation
Invariant: measurable representation separation is not called reasoning.
Oracle: reports retain an explicit claim ceiling.

### H9 — Speaker/privacy leakage
Invariant: learned/acoustic features are treated as potentially biometric.
Oracle: retention/export policy records whether raw audio or speaker-bearing
features persist.

### H10 — Model identity substitution
Invariant: model ID, requested revision, resolved revision, and artifact format
remain bound together.
Oracle: mismatched revision/artifact metadata blocks qualification.
### H11 — TOCTOU provider mutation
Invariant: provider metadata checked before download cannot authorize different
bytes fetched later.
Oracle: qualification hashes/pins the downloaded artifact or immutable commit.

### H12 — Self-attested security
Invariant: implementation authorship is not independent security acceptance.
Oracle: internal Seven/Four lenses are labeled non-independent.

### H13 — Adversarial acoustic perturbation
Invariant: hidden/imperceptible perturbations are within the threat model.
Oracle: evaluation includes injected audio that alters downstream behavior
without obvious lexical change.

### H14 — Backdoored learned prompt/adapter
Invariant: adapter/prompt artifacts are versioned supply-chain subjects.
Oracle: unbound learned prompts cannot be accepted solely because the base
model is trusted.

## External research basis

- Hou et al., EMNLP 2025, "Evaluating Robustness of Large Audio Language
  Models to Audio Injection": https://aclanthology.org/2025.emnlp-main.1303/
- Chen et al., 2026, "Hijacking Large Audio-Language Models via
  Context-Agnostic and Imperceptible Auditory Prompt Injection":
  https://arxiv.org/abs/2604.14604
- Hanif et al., EMNLP 2025, "TrojanWave":
  https://aclanthology.org/2025.emnlp-main.940/
- OWASP LLM01:2025 Prompt Injection:
  https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Hugging Face Pickle Scanning / model-load safety:
  https://huggingface.co/docs/hub/security-pickle
  https://huggingface.co/docs/transformers/models

## Good-enough boundary

This threat model does not claim perfect security. Ears should block known
HIGH/MEDIUM findings on the exact candidate, preserve unresolved findings as
unresolved, and keep security evidence bound to the exact reviewed head.
