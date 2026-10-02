# Prototype V0.5 — Security and Provenance Hardening

Status: candidate implementation on research branch / not merged
Date: 2026-10-02

## Trigger

BT2 Four and Seven were applied as internal method lenses, with exact current BT2 source provenance recorded in `research/bt2-role-lenses.yaml`. This is not independent review because the same interaction also authors the Ears changes.

Four's lens forced exact provenance and reconstruction questions. Seven's lens attacked model loading, audio ingestion, authority boundaries, and evidence currentness.

## Learned-model hardening

The WavLM default is now pinned to the exact observed Hugging Face revision:

`4c66d4806a428f2e922ccfa1a962776e232d487b`

Mutable revisions such as `main` are rejected by default. An explicit exploratory construction can permit a mutable revision, but that state is labeled `MUTABLE_EXPLORATORY_REVISION` and cannot be qualification evidence.

Learned model loading now requests `trust_remote_code=False` and `use_safetensors=True`.

A live provider read on 2026-10-02 showed that `microsoft/wavlm-base-plus` at the pinned revision publishes `pytorch_model.bin` and does **not** publish `model.safetensors`. Therefore the safe default intentionally blocks runtime loading of that upstream artifact rather than silently falling back to pickle.

That is a real limitation, not a cosmetic warning. Hugging Face documents that pickle deserialization can execute arbitrary code and recommends safer serialization.

## Audio-ingestion hardening

File-backed WAV ingestion now has default limits on file size, duration, channel count, and sample rate before complete PCM decode.

The source bytes are read once through a bounded read, hashed, and parsed from the exact same byte buffer. This closes the prior TOCTOU provenance defect where decoded PCM could come from one path state while the source hash came from a later replacement of that path.

## Control-authority boundary

Serialized Ears artifacts now declare:

- `source_trust: UNTRUSTED_AUDIO_CONTENT`
- `control_authority: NONE`

This does not itself defeat auditory prompt injection. It establishes the minimum machine-readable boundary a downstream reasoner must preserve: speech decoded from audio is still untrusted content unless authority is established through a separate control channel.

## Tests added

The V0.5 hostile tests cover:

- immutable WavLM revision defaults;
- mutable revision rejection;
- safe loader kwargs (`trust_remote_code=False`, safetensors-only);
- CLI exact-revision default and bounded mutable-revision failure;
- file-size, duration, and sample-rate limits;
- deterministic TOCTOU path-replacement regression;
- untrusted-audio/control-authority artifact labels.

## Claim ceiling

V0.5 improves the integrity and security of the research substrate. It does not prove secure machine hearing, resistance to adversarial audio, or safe autonomous action from voice input.

The WavLM source adapter remains not runtime-qualified on the observed build machine, and its current Microsoft upstream artifact is incompatible with Ears' safetensors-only default.
