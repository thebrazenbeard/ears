# Seven Internal Security Follow-up — 783da62

Reviewed subject: `783da622e819e091a25a8e27c7bfb7106b691ed4`
Prior review subject: `ead07574b0519ffdfe8f90734338fe41bb0f1899`
Date: 2026-10-02
Disposition: **PASS_H0_M0 WITH UNRESOLVED FUTURE BOUNDARY**

This is an internal BT2 Seven-method review, not independent acceptance.

## S7-EARS-001 — CLOSED

The reader now streams source bytes through a bounded `SpooledTemporaryFile`, hashes the captured stream, parses the same snapshot, and checks `max_decoded_samples` before `readframes` and Python-float expansion.

Regression evidence:
- decoded-sample limit hostile passes;
- file-size, duration, and sample-rate limit hostiles pass;
- full suite on this exact head: 24/24 PASS.

Claim ceiling: bounded research-tool ingestion, not proof against all resource-exhaustion strategies.

## S7-EARS-002 — CLOSED

The stale `_hash_file` mock was replaced by a live `Path.open` ingestion hostile. It returns original bytes from the first source open while replacing the pathname during the read. The candidate binds source identity and parsing to the captured original bytes.

A transient mutation changed the candidate back to a vulnerable pathname reopen/hash sequence. The hostile failed that mutant with exit 1, then the exact candidate bytes were restored and the hostile passed.

This is stronger evidence that the regression test attacks the intended seam rather than merely remaining green.

## S7-EARS-003 — UNRESOLVED / NOT CURRENT-SCOPE BLOCKER

`source_trust: UNTRUSTED_AUDIO_CONTENT` and `control_authority: NONE` are evidence labels, not enforcement. No downstream action-capable reasoner exists in Ears yet. When one is introduced, auditory prompt injection/confused-deputy hostiles become acceptance-blocking.

## S7-EARS-004 — PASS WITH CEILING

WavLM remains exact-revision-pinned, `trust_remote_code=False`, and safetensors-only. The observed Microsoft upstream artifact is pickle-only, so the learned path fails closed rather than weakening loading policy.

No model runtime was executed or qualified.

## Currentness

This follow-up applies only to `783da622e819e091a25a8e27c7bfb7106b691ed4`. Any later code change requires a new review or an explicit unaffected-path determination.
