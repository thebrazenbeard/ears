# Harmonic and phonetic auditory architecture — source-informed integration register

Status: initial source inspection and minimal executable baseline. **Not** a complete source audit, adoption of all components, or phonetic performance qualification. Target: Ears phonetic perception rather than mandatory speech-to-text. Source trees inspected 2026-10-16; individual component behavior still requires tests.

## Boundaries
- The input is PCM with sample rate, channel policy, sample time, clock domain, and microphone provenance.
- An acoustic observation is not a phoneme, word, physical-source identity, or action authorization.
- Separate tonal/voiced and broadband/transient paths. Preserve competing F0 hypotheses and uncertainty; do not convert heuristic scores into calibrated probabilities.
- Maintain timestamp alignment, algorithm provenance and version, sample-rate and frame-hop metadata; do not rewrite raw sensory observations after downstream interpretation.
- Optional dependencies must fail closed or degrade to baseline without suppressing nonharmonic sensing.
- Record license, pinned revision, throughput, CPU/memory budget, sample-rate limits, reliability, and task-specific ablation before enabling any adapter.

## Source-by-source architectural intake
| Upstream | Inspectable component | Ears treatment | Restrictions |
|---|---|---|---|
| crypto10kx/harmonic-pattern-detection | Vectorized temporal pattern generation, strict ordering, deduplication, realistic backtest bias checks | Transfer **only generic event-pipeline design ideas** (temporal causality / event dedup / no future leakage). Its Fibonacci trading patterns are not acoustic harmonics. | Do not import financial detectors or claim it recognizes sound. MIT stated upstream. |
| MirjamVisscher/FuzzyFrequencies | Multi-F0 *analysis of outputs*, pitch-class and tonal profiles, cross-estimator comparison, distribution distances, clustering, time-varying cycles | Optional hypothesis evaluation and ensemble diagnostics; preserve multiple pitch tracks until source evidence disambiguates. | Upstream explicitly says large multiple-F0 estimators are external. Music-specific tonal assumptions are not phonetic truth. MIT stated upstream. |
| libAudioFlux/audioFlux | Data-stream modular transforms (BFT/NSGT/CWT/PWT), FFT/STFT/mel/bark/ERB/CQT, pitch algorithms (YIN/CEP/PEF/NCF/HPS/LHS/FFP), spectral/temporal features, HPSS, onsets, harmonics | Preferred optional fast DSP backend; parity-test against minimal numpy baseline, do not make it the only executor. | Select only needed transform combinations and profile runtime cost. MIT stated upstream. |
| NanoComp/harminv | Filter diagonalization for few damped sinusoidal modes, frequency/decay/amplitude/phase | Experimental narrow-band stationary tonal refinement; activate only when signal model fits. | GPL; not general speech front end; avoid direct bundled code. |
| nerdull/harmonic-retrieval | Narrowband frequency-domain state-space harmonic retrieval with complex FFT data and noise/model-count inputs | Experimental candidate refinement for stable tones with explicit precondition confidence. | GPLv3; method may fail on arbitrary broadband/rapidly evolving speech. |
| QiaoyuYang/harp-codec | Harmonic-aware, frequency-partitioned residual vector quantization with progressive bitrate groups, audio codec metrics | Optional future compact sensory archive/transmission; train and evaluate acoustic feature retention and reconstruction error before use. | Lossy reconstructions may erase consonant transients; never replace raw observations for evidence. MIT stated upstream. |
| spotify/basic-pitch | Lightweight music AMT, multi-pitch inference, pitch bends, model formats for ONNX/TFLite/CoreML/TF | Auxiliary multi-F0 reference for musical or complex harmonic scenes, not general phoneme decoding. | Instrument-oriented; verify channel mixing, 22050 Hz resampling and window boundaries. Apache 2.0 stated upstream. |
| Voice-Lab/VoiceLab | Reproducible batch voice measures using Parselmouth/Praat; pitch, HNR, jitter/shimmer, formants/LPC, subharmonics, RMS corrections | Offline reference and calibration suite for Ears spectral envelope, pitch and perturbation measurements. | The project warns its API is unsupported; use validation fixtures and pinned versions rather than a mandatory runtime API. MIT stated upstream. |
| pylon/world-vocoder | WORLD: DIO/Harvest F0, StoneMask refinement, CheapTrick envelope, D4C aperiodicity, voiced/unvoiced synthesis | Optional speech-focused analysis: independent F0, envelope, aperiodicity paths; prove benefit by phoneme-task ablation. | Linked fork is archived; find and qualify actively maintained binding before production adoption. Modified BSD stated upstream. |

## Proposed layered contract
1. **Capture**: bounded PCM frames, channel identity, observed timestamps, no implicit downmix or resampling.
2. **Parallel time-frequency analysis**: STFT + perceptual filterbanks (mel/ERB/Bark), optionally multiresolution CQT/NSGT/wavelets. Choose transform based on task, not every transform simultaneously.
3. **Acoustic extraction**: RMS, ZCR, spectral centroid, flatness and flux, spectral envelope, formant candidates, voicing/HNR, F0 candidates and trajectories, harmonic peaks, subharmonics, jitter/shimmer, onset and frication detection.
4. **Scene hypotheses**: competing tonal sources, temporal tracking with birth/decay, harmonic/noise partition, source-separation proposals. Uncertain multimodal F0 is not coerced into one.
5. **Phonetic hypotheses**: learnable mappings from acoustics and time transitions to phone-level candidates; no mandatory text generation.
6. **Optional compression and replay**: codec experiments gated by reversibility/evidence needs; preserve raw capture or record destructive-loss policy.
7. **Evaluation**: no-future-lookahead streaming constraints, synthetic mixtures, held-out voices and environments, vowel/formant, unvoiced consonant, transient, missing-fundamental, polyphonic, latency and calibration tests.

## Implemented now
`ears/acoustics.py`: dependency-light mono PCM STFT frames, RMS, centroid, flatness, positive spectral flux, zero-crossing, harmonic-summation pitch *candidates*, provisional harmonic-energy ratio and provisional voiced flag. No claims of calibrated pitch confidence, true HNR, formant extraction, noise robust source separation, or phoneme accuracy.

`tests/test_acoustics.py`: synthetic smoke tests for silence, harmonic tone, transient, malformed inputs. No full test-suite PASS until executed and reported.

## Acceptance gates for subsequent source adaptation
- Review representative implementation and public API files, licenses and tests at pinned commits for each selected upstream; check dependency and transitive license boundaries.
- Ensure silence and broad-spectrum noise do not become confidently labeled as voiced speech.
- Compare feature parity and runtime against independent reference, including 8/16/44.1/48 kHz, small windows, and partial streamed frames.
- Evaluate timestamp drift, resampling anti-aliasing, cross-frame continuity, disjoint frequency masks, rapid F0 jumps, simultaneous sources and microphone clipping.
- Benchmark each candidate with and without component on held-out phonetic corpora; retain only measurable improvements under bounded cost.
- Hostile check: increased harmonic resolution could reduce consonant intelligibility. Ensure full-band, nonharmonic features survive every transform/codec.
- Preserve licensing attribution for optional integrations; never paste GPL source into a permissively licensed core without explicit licensing decision.
