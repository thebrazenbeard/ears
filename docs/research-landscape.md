# Research Landscape — Native Acoustic Grounding

Status: research synthesis, 2026-10-02  
Scope: speech understanding that preserves non-textual evidence for downstream reasoning

## 1. Problem statement

The ordinary ASR-centered pipeline is:

```
speech -> transcript -> language reasoning
```

That pipeline is excellent when the task is mostly lexical. It is structurally weak when the meaning depends on acoustic evidence discarded by transcription.

Ears is investigating:

```
speech -> acoustic representations -> reasoning
                 |
                 +-> optional transcript
```

The important difference is not whether ASR exists. It is whether text is the **exclusive bottleneck**.

## 2. Relevant research families

### 2.1 Self-supervised speech representations

**HuBERT** (Hsu et al., 2021) learns hidden speech units using masked prediction over clustered targets. Its significance for Ears is methodological: speech can be represented through learned units without a human-written transcript being the only supervisory object.

Source: https://arxiv.org/abs/2106.07447

**WavLM** (Chen et al., 2021/2022) explicitly targets "full stack speech processing" and emphasizes that speech contains speaker identity, paralinguistic information, and spoken content. It combines masked prediction with denoising and is a strong continuous-feature candidate for an Ears baseline.

Source: https://arxiv.org/abs/2110.13900

**Implication:** an Ears prototype should include at least one continuous SSL feature path before inventing a tokenizer.

### 2.2 Discrete speech units and codecs

**SpeechTokenizer** (Zhang et al., 2023) uses residual vector quantization to hierarchically combine semantic and acoustic speech information. The first quantizer is treated as more semantic; later quantizers retain acoustic/timbre information.

Source: https://arxiv.org/abs/2308.16692

**Mimi**, introduced with Moshi, is a low-frame-rate streaming neural audio codec. Its first codebook is trained toward WavLM-derived semantics while other codebooks carry acoustic detail.

Moshi paper: https://arxiv.org/abs/2410.00037  
Implementation: https://github.com/kyutai-labs/moshi

A 2026 ACL workshop study examined Mimi's semantic codebook against TIMIT and reported mappings from its 80 ms semantic tokens to subphone, phone, biphone, triphone, and quadphone realizations.

Source: https://aclanthology.org/2026.brigap-1.7/

**Implication:** discrete codec/semantic units are not merely waveform compression. At least some modern tokenizers encode structure close to phonological categories. That makes them directly relevant to Ears.

### 2.3 Speech-native language models

**Spirit LM** (Nguyen et al., 2024) extends a pretrained text model to interleaved speech and text units. Its expressive variant adds pitch and style units to phonetic HuBERT units.

Source: https://arxiv.org/abs/2402.05755

**Moshi** (Défossez et al., 2024) frames dialogue as speech-to-speech generation and models user/system audio streams in parallel. The authors explicitly motivate the design by information lost through text intermediates, plus latency and turn-segmentation problems.

Source: https://arxiv.org/abs/2410.00037

**Qwen2-Audio** (Chu et al., 2024) accepts audio directly and supports voice-chat and audio-analysis modes without requiring text input from the user.

Source: https://arxiv.org/abs/2407.10759

**Audio Flamingo 3** (Goel et al., 2025) uses a unified audio encoder spanning speech, sound, and music and supports long-audio reasoning and voice interaction.

Source: https://arxiv.org/abs/2507.08128  
Implementation: https://github.com/NVIDIA/audio-flamingo

**Implication:** architectures can bypass an explicit orthographic transcript bottleneck. That is weaker than proving acoustic reasoning. An audio encoder may still compress speech into a latent representation dominated by lexical content — effectively a learned soft transcript. Ears must test what non-lexical acoustic information survives and whether downstream decisions causally depend on it.

### 2.4 Continuous versus discrete representations

Wang et al. (2025) directly compared SSL-based discrete tokens and continuous features for spoken-language understanding under controlled settings. Their reported result: continuous features generally performed better across the evaluated tasks, with distinct efficiency/robustness tradeoffs.

Source: https://arxiv.org/abs/2508.17863

**Implication:** Ears should not equate "real hearing" with "discrete audio tokens." A continuous feature path is a serious contender and must be included in ablations.

### 2.5 Prosody-aware / phonological tokenization

**Phonological Tokenizer** (Onda et al., 2026) argues that conventional acoustic tokens retain too much detail while conventional phonetic tokens discard prosody. Their target is a discrete representation that retains linguistic and prosodic information while reducing speaker identity.

Source: https://arxiv.org/abs/2601.19781

This is unusually close to Ears' target abstraction.

**Implication:** the ideal interface may be neither orthographic text nor reconstruction-perfect codec tokens, but a task-shaped phonological representation.

### 2.6 Paralinguistic reasoning remains weak

**CP-Bench** (Wang et al., 2025) focuses on contextual and paralinguistic reasoning in speech-LLMs and reports a persistent gap in integrating verbal content with emotion/prosody.

Source: https://arxiv.org/abs/2509.16589

**ParaS2S** (Yang et al., 2025) evaluates speech-to-speech systems for paralinguistic-aware interaction and reports that existing S2S systems can perform poorly at responding appropriately to paralinguistic attributes.

Source: https://arxiv.org/abs/2511.08723

**ParA-LLM / ParA-Bench** (Anand et al., 2026) proposes 22 paralinguistic characteristic classes and a 6,000-question benchmark. The authors report very low absolute accuracy for frontier audio models on the benchmark, despite strong ASR.

Source: https://arxiv.org/abs/2609.22771

**Implication:** solving transcription is not solving hearing.

## 3. Representation options for Ears

### Option A — transcript plus hand-engineered prosody

Extract pitch, intensity, speaking rate, pause structure, etc., and attach those features to text.

Advantages:
- cheap;
- interpretable;
- good baseline.

Failure mode:
- hand-selected features become a second lossy bottleneck.

### Option B — continuous SSL embeddings

Feed WavLM-like or other speech encoder features through an adapter into a reasoning model.

Advantages:
- high information retention;
- supported by strong existing encoders;
- no discrete-codebook commitment.

Failure mode:
- long sequences and expensive attention;
- opaque internal representation.

### Option C — discrete semantic / phonological units

Quantize speech to HuBERT-like, SpeechTokenizer-like, Mimi-like, or purpose-trained phonological units.

Advantages:
- compact;
- sequence-model friendly;
- potentially interpretable at phone/allophone scale.

Failure mode:
- quantization destroys useful information;
- representation may overfit reconstruction, ASR, or speaker identity rather than meaning.

### Option D — neural codec tokens

Preserve enough information to reconstruct audio and reason over codec token streams.

Advantages:
- supports generation and full-duplex speech;
- retains rich acoustics.

Failure mode:
- expensive token rate;
- reasoning burden includes irrelevant waveform detail.

### Option E — hybrid multi-resolution evidence

Maintain several synchronized views:

```
audio
 |-- continuous SSL features
 |-- compact phonological/semantic units
 |-- prosodic observables
 |-- optional codec detail
 '-- transcript lattice / hypotheses
```

Downstream reasoning can use a compact path by default and rehydrate richer evidence when ambiguity matters.

**Current Ears hypothesis:** Option E is the strongest starting architecture.

## 4. What "direct" should mean

"Direct audio understanding" should not be defined as "the transformer receives PCM samples."

Human hearing is itself a hierarchy of transformations. A useful technical definition is:

> lexical reasoning can access information causally derived from the source audio that has not been forced through an orthographic transcript bottleneck, with provenance back to time ranges in the source.

That allows cochleagram/mel front ends, learned encoders, continuous embeddings, discrete units, and codecs while excluding transcript-only systems from claiming the same evidence path.

## 5. Risks and unresolved questions

> **HOSTILE REVIEWER:** Ears may be solving a problem that existing audio-language models already solved.

**PARTIALLY ACCEPTED.** Direct audio models exist. The unresolved part is evidence preservation and reliable use: current paralinguistic benchmarks still report major weaknesses, and many systems remain difficult to inspect. Ears should contribute only if it can provide a better representation/evaluation interface or a materially stronger result.

> **HOSTILE REVIEWER:** "Phonetic hearing" is too narrow and could throw away exactly the prosody and timing the project wants.

**ACCEPTED.** Phonetic structure is one channel. The project target is acoustic-native spoken-language evidence.

> **HOSTILE REVIEWER:** Raw/codec audio may make reasoning worse because text is an extraordinarily efficient semantic compression.

**ACCEPTED AS A LIVE HYPOTHESIS.** Ears must benchmark transcript-only against acoustic-only and fused systems. The goal is not to abolish text; it is to remove text as a mandatory information bottleneck.

> **HOSTILE REVIEWER:** Prosody-to-emotion inference is culturally variable, speaker-dependent, and easy to overstate.

**ACCEPTED.** Ears should store observable acoustic features separately from interpretive hypotheses and explicitly score false affect/intent inference.

## 6. Research conclusion

The core idea is technically viable and timely, but the likely winning architecture is not "raw waveform straight into an LLM."

The strongest current direction is a **streaming, multi-resolution acoustic evidence layer** that preserves direct speech representations and optionally derives text, rather than deriving everything from text.

That is concrete enough to build and falsifiable enough to be worth building.
