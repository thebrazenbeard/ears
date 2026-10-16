# Ears — auditory architecture

Ears' stated purpose is to enable phonetic hearing rather than force audio directly into speech-to-text. This is an evolving engineering design, **not evidence of deployed functionality**.

## Signal route

PCM capture with clock, channel and provenance -> synchronized time/frequency features -> harmonic and broadband evidence -> competing acoustic events -> phonetic candidate trajectories -> optional downstream interpretation.

**Hard invariants**
- An acoustic feature is not a phoneme; a phoneme candidate is not a word, physical-source identity, or authorization.
- Never discard fricatives, stops, impulses, silence and noise simply because they lack harmonics.
- Preserve frame timing, signal sample rate, algorithms, versions and competing interpretations.
- Keep actual observation separate from derived estimates, confidence, runtime resource health and downstream semantic inference.
- A model's agreement with another model is not independent ground truth.
- Do not require external inference for essential raw-signal analysis; optional backends must degrade predictably.

## Component seams
- `capture`: acquisition, gain/clipping diagnostics, channel information, timestamps, streaming buffer bounds.
- `transforms`: STFT, frequency-scaled and optionally multiresolution views.
- `acoustics`: synchronized tonal/nonharmonic observations, F0 hypothesis tracking, envelope/aperiodicity, voiced/unvoiced evidence.
- `scene`: competing sources and acoustic events with birth/decay/ambiguity.
- `phonetics`: time-conditioned phoneme features, place/manner/voicing hypotheses, phones rather than text.
- `memory`: optional bounded acoustic representations, with compression provenance and raw-preservation policy.
- `evaluation`: synthetic fixtures and recordings, held-out listeners/voices/environment, latency, calibration, and ablation.

Only the NumPy baseline in `ears/acoustics.py` and its draft tests exist. The other components are design boundaries, not implemented directories/services.

## Integration principles

See [HARMONIC_ARCHITECTURE_INTAKE.md](HARMONIC_ARCHITECTURE_INTAKE.md) for the nine upstream sources, expected components, licenses and exclusions. Prefer an adapter interface that reports capabilities and hardware requirements, validates inputs, and emits typed observations with stable provenance. Never make an upstream research program a nonoptional runtime dependency merely because it provides a useful algorithm.

## Security

Review existing `.vscode/tasks.json` before enabling editor tasks: an auto-run configuration invoking a WOFF2 file using Node.js is anomalous. Do not invoke it during setup. Treat media, codecs and external model weights as untrusted inputs; impose size/duration/resource limits.

## Status

Architecture: PROPOSED. NumPy baseline: SOURCE_PRESENT on draft branch. Tests: SOURCE_PRESENT, EXECUTION_NOT_VERIFIED. Upstream adapters: NOT_IMPLEMENTED. Phonetic accuracy: UNKNOWN. Merge/deployment: NOT_PERFORMED.
