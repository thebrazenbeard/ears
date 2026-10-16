# Ears — engineering backlog from upstream architecture intake

Priority ordered, not a claim that tasks have been executed.

1. **P0 — security**: inspect anomalous auto-run `.vscode/tasks.json`, its provenance and unexpected payload. Do not execute it or activate automatic folder tasks. Remediate separately with inspection evidence.
2. **P0 — validate baseline**: run `python -m unittest discover -s tests -v` with NumPy installed; record exact revision, interpreter, dependencies and output. Correct any failed heuristic/spectral tests before declaring green.
3. **P0 — numeric fidelity**: test expected F0 at common sample rates, octave errors, silence, missing-fundamental, noise and multi-sines; reject overflow and malformed samples. Do not mislabel spectral harmonic ratio as measured HNR.
4. **P1 — streaming**: add stateful buffering and multi-channel policy, frame-center and acquisition-clock metadata, backpressure, discontinuities and bounded working set.
5. **P1 — phonetic cues**: add independently testable LPC/formant candidates, spectral slope and envelope, voicing, onset, stop bursts and frication with time trajectories.
6. **P1 — reference tests**: compare pitch/envelope/noise measurements with pinned VoiceLab/Praat and WORLD on reproducible test clips; expose method disagreement.
7. **P1 — DSP adapters**: optional audioFlux transform/feature backend; explicit provenance and configuration; reference parity tests and profile overhead.
8. **P2 — multi-F0**: implement candidate tracking and evaluate Basic Pitch + approaches referenced by FuzzyFrequencies on overlapping sources and speech, preserving ambiguity.
9. **P2 — precision harmonic modes**: assess narrowband methods from harminv and harmonic-retrieval with independent, license-compatible alternatives; reject on transient/broadband input.
10. **P2 — compressed archive experiment**: HARP codec preservation tests for consonant bursts, phone discrimination and waveform timing across bitrate tiers.
11. **P2 — end-to-end model**: evaluate phoneme likelihoods on held-out speakers and environments without promoting guesses to facts; measure word-free phonetic representation quality.
12. **P2 — adversarial qualification**: ablate each optional subsystem and benchmark latency, CPU, failure isolation, licensing and reproducibility.

Every task requires source revision, implementation tests, failure observations, metrics and explicit residual risk in the PR before acceptance.
