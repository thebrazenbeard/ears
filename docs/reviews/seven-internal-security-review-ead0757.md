# Seven Internal Security Review — ead0757

Reviewed subject: `ead07574b0519ffdfe8f90734338fe41bb0f1899`
Predecessor: `2b72150be4ef8660c3054d83f9b33d2691c827fb`
Date: 2026-10-02
Disposition: **CHANGES_REQUESTED (2 MEDIUM, 0 HIGH)**

This review applies BT2 Seven v1.0.0 as an internal method lens. It is **not independent review**: the same interaction also authored the candidate.

## S7-EARS-001 — MEDIUM — decoded-sample memory amplification

Family: resource exhaustion / untrusted input.

Invariant: configured audio limits must bound material memory consumption before full PCM decoding.

Observed: `read_wav` reads up to 256 MiB into one bytes object and then `_decode_pcm` expands every sample into Python floats/lists/tuples. A file that satisfies the byte cap can therefore consume many times the configured limit during decode.

Impact basis: untrusted audio can cause avoidable local memory exhaustion before Ears produces an artifact.

Minimum correction oracle:
- snapshot input without holding the full configured maximum in RAM;
- introduce a decoded-sample/PCM-memory bound checked before `readframes`/float expansion;
- add hostile tests that exceed the decoded bound while remaining under file-size limit.

What is not proven: remote exploitability, code execution, or a production denial of service. Ears is currently research tooling.

## S7-EARS-002 — MEDIUM — TOCTOU regression test no longer attacks production seam

Family: validation integrity / stale oracle.

Invariant: the path-replacement hostile must fail if source identity and parsed bytes can diverge.

Observed: the test patches `ears.audio._hash_file` with `create=True`, but `_hash_file` was removed when same-buffer parsing was implemented. The patch is therefore inert; the test passes without triggering path replacement.

Impact basis: green tests currently overstate evidence for the specific TOCTOU regression hostile.

Minimum correction oracle:
- exercise a live ingestion seam that deterministically changes the pathname after the original source is opened/read;
- prove returned `source_id` and decoded metadata still bind the exact same captured bytes;
- demonstrate RED against a deliberately vulnerable reopen/hash sequence or equivalent regression fixture.

## S7-EARS-003 — UNRESOLVED — downstream auditory-instruction authority enforcement

Family: prompt injection / confused deputy.

The artifact now declares `UNTRUSTED_AUDIO_CONTENT` and `control_authority: NONE`. That is the correct evidence label, but no downstream reasoning/action boundary exists yet to enforce it. Keep this unresolved until such a consumer exists; do not call the metadata a mitigation by itself.

## S7-EARS-004 — PASS WITH CEILING — learned-model supply chain

The exact WavLM revision is pinned, mutable revisions fail closed by default, remote code is disabled, and safetensors-only loading prevents silent fallback to the currently observed pickle-only upstream artifact.

Claim ceiling: source-level loading policy only; no WavLM runtime qualification occurred.

## Mechanical review notes

- exact reviewed head recorded above;
- changed pathset is 18 files from predecessor to subject;
- Four reconstruction manifest exists and labels Four/Seven use as non-independent;
- 23/23 tests were green on the candidate, but S7-EARS-002 means that green state does not validate the intended TOCTOU hostile;
- no merge/deploy/install authority is inferred.

## Acceptance rule

Re-run the two MEDIUM hostiles on a new exact head. This review does not transfer PASS to changed bytes. S7-EARS-003 remains an explicit future-system requirement rather than a reason to pretend a nonexistent downstream action layer is already secure.
