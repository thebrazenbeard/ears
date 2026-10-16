# Ears — research and decision record

Last updated: 2026-10-16. Source inspection was conducted against the nine repository URLs supplied by Patrick, using their root metadata, READMEs and recursive tree indexes. This is **not a full line-by-line source audit**.

## Decisions

1. Phonetic hearing is distinct from automatic speech transcription. Acoustic evidence remains inspectable whether or not a linguistic interpretation exists.
2. Adopt harmonic detection as a companion to broadband, formant, transient and frication analysis, not as a gatekeeper.
3. Establish a small runnable NumPy reference before adopting complex backends; this is for numerical comparison and failure-degradation, not an assertion of parity with mature DSP tools.
4. Prefer audioFlux as an optional broad-feature backend; evaluate WORLD for speech-specific envelope/aperiodicity decomposition; use VoiceLab primarily for offline independent reference measurements.
5. Do not force one F0 when multiple voices or tonal sources coexist. FuzzyFrequencies provides a model for comparing multi-F0 outputs but delegates core extraction externally; Basic Pitch can be an optional music/multipitch estimator.
6. Use Harminv and harmonic-retrieval only for fit-for-model stable tonal segments; their GPL constraints require explicit legal/design review before copying code.
7. Evaluate HARP's harmonic-aware codec separately; lossy audio reconstruction must not corrupt or replace raw evidence or phoneme evaluation data without an explicit policy.
8. Crypto10kx's harmonic trading detector has no acoustic algorithm to integrate. General chronological backtesting/no-leakage and signal deduplication ideas transfer abstractly; no finance code copied.
9. Avoid relying on the archived pylon WORLD fork without pinning and qualifying maintenance status and alternatives.
10. No automatic merge or deployment. This work stays in a draft PR until reviewed.

## Unresolved questions and falsification targets
- Does harmonic extraction improve actual phone/phoneme metrics, or only pitch metrics? Compare ablations under identical datasets and compute limits.
- Does the pitch estimator introduce octave/subharmonic ambiguities in noisy or polyphonic mixtures? Measure precision and keep multiple candidates.
- Can envelope estimation track moving formants without destroying transient consonants?
- How will real-time buffering preserve timestamp semantics, enforce bounded memory, and handle clock drift or packet loss?
- Which adapter transitive dependencies and model weights introduce license, platform or security constraints?
- Which features must run on low-power CPU without GPU, and what are acceptable end-to-end latency and power ceilings?

## Source and evidence register
Repository roots inspected:
- https://github.com/crypto10kx/harmonic-pattern-detection
- https://github.com/MirjamVisscher/FuzzyFrequencies
- https://github.com/libAudioFlux/audioFlux
- https://github.com/NanoComp/harminv
- https://github.com/nerdull/harmonic-retrieval
- https://github.com/QiaoyuYang/harp-codec
- https://github.com/spotify/basic-pitch
- https://github.com/Voice-Lab/VoiceLab
- https://github.com/pylon/world-vocoder

See the detailed intake register for source-specific algorithms and suitability. Claims about their implementations are **source-informed**, not runtime-qualified by Ears.

## Readback and qualification vocabulary

SOURCE_PRESENT: committed file verified in Git. TESTED: test executed for named revision, environment, command and result. QUALIFIED: behavior validated on appropriate independent datasets. INSTALLED: integrated in an operating runtime. These are distinct. Never report TESTED/QUALIFIED/INSTALLED based on file creation alone.
