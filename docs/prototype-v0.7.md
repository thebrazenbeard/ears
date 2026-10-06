# Prototype V0.7 - Safe Time-Resolved Wav2Vec2 Baseline

Status: candidate implementation on research branch / not merged
Date: 2026-10-06

## Trigger

V0.5 left the learned continuous baseline blocked: the pinned
microsoft/wavlm-base-plus provider revision exposes pytorch_model.bin but no
safetensors artifact, while Ears deliberately refuses silent pickle fallback.

A fresh provider read on 2026-10-06 found that
facebook/wav2vec2-base-960h at exact revision
22aad52d435eb6dbaf354bdad9b0da84ce7d6156 publishes both model.safetensors
and pytorch_model.bin. Ears can therefore request the safetensors artifact
explicitly without weakening the V0.5 loading policy.

## Implementation

V0.7 adds Wav2Vec2Adapter as an optional learned continuous channel.

The adapter:

- pins the provider revision to a 40-hex commit;
- requests trust_remote_code=False;
- requests use_safetensors=True;
- uses AutoFeatureExtractor rather than a tokenizer;
- requires 16 kHz input rather than silently resampling;
- applies a separate learned-channel duration ceiling;
- preserves model time instead of mean-pooling the entire utterance.

The observed provider config declares convolution kernels
[10, 3, 3, 3, 3, 2, 2] and strides [5, 2, 2, 2, 2, 2, 2]. Under the
Wav2Vec2 valid-convolution geometry this gives a 400-sample receptive field
(25 ms at 16 kHz) and a 320-sample stride (20 ms). Ears derives source spans
from those config values at runtime rather than hard-coding the geometry.

By default, five adjacent model frames are mean-pooled into each evidence item.
That reduces sequence rate while retaining time-local evidence; it is not the
utterance-wide mean pooling used by the earlier WavLM baseline.

## Provider evidence boundary

The provider observation establishes that an exact current revision advertises
a safetensors artifact. It does not prove that:

- the model has been downloaded locally;
- torch or transformers are installed in the Ears environment;
- the safetensors path executes successfully;
- the hidden states improve an acoustic-required task.

Those remain separate qualification steps.

## Hostile review

> **HOSTILE REVIEWER:** wav2vec2-base-960h is ASR-fine-tuned. Its hidden states
> may be strongly lexical and behave like a soft transcript.

**ACCEPTED.** That makes it a useful baseline, not proof of acoustic-native
reasoning. Same-lexical acoustic counterfactuals still decide whether useful
non-textual information survives and is used.

> **HOSTILE REVIEWER:** Window means still destroy detail.

**ACCEPTED.** V0.7 narrows the loss to short contiguous windows instead of the
entire utterance. Pool size is explicit and adjustable. Later ablations should
compare unpooled and differently pooled streams.

> **HOSTILE REVIEWER:** A safetensors filename is not runtime qualification.

**ACCEPTED.** V0.7 is source-implemented and provider-source-bound only until an
exact local runtime run succeeds and is recorded.

## Claim ceiling

SAFE_PROVIDER_ARTIFACT_OBSERVED + SOURCE_ADAPTER_IMPLEMENTED

does not imply

LEARNED_RUNTIME_QUALIFIED or ACOUSTIC_REASONING.
