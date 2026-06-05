# PSPC Sequence Experience Eval v0.1 Status

- status: `pass`
- verdict: `sequence_experience_eval_v0_1_pass__manual_review_packet_ready`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only`
- runtime authority: `none`
- mainline_connected: `false`
- enabled: `false`
- EgoOperator integration: `forbidden`

## Evidence

- Robustness dataset: `docs/codex/tasks/pspc-sequence-experience-eval-v0-1/robustness_dataset_v0_1.jsonl`
- Runner: `scripts/run_pspc_sequence_experience_eval_v0_1.py`
- Tests: `tests/test_pspc_sequence_experience_eval_v0_1.py`
- Artifact report: `artifacts/pspc_sequence_experience_eval_v0_1/SEQUENCE_EXPERIENCE_EVAL_V0_1_REPORT.md`
- Manual review packet: `artifacts/pspc_sequence_experience_eval_v0_1/MANUAL_REVIEW_PACKET.md`
- Machine artifact: `artifacts/pspc_sequence_experience_eval_v0_1/sequence_experience_eval_v0_1.json`

## Result

The v0.1 review passes:

- dominant trigger tendencies stay stable across four trigger paraphrases
- paraphrased histories remove obvious shortcut keywords and remain directionally consistent
- deleting high-salience history shifts trigger profiles more than deleting low-salience history
- mixed histories expose conflict and recency/salience basis rather than neutral collapse
- manual review packet is generated
- runtime-authority fields and side effects remain absent

## What This Proves

This proves the lab/shadow sequence eval is more robust than the clean v0 grouping alone and has an artifact packet suitable for human manual review.

## What This Does Not Prove

It does not prove PSPC is integrated into EgoOperator, live runtime integration safety, adapter readiness, model learning, world/self model causality, planner causality, durable memory efficacy, real user benefit, live autonomy, consciousness, subjective experience, or real emotion. Category labels remain fixture authority, so lexical shortcut risk is reduced but not eliminated.

## Failure Meaning

Failure would mean the current sequence eval is too fragile for any closer runtime-adjacent discussion. PSPC should remain shadow-only while dataset/scoring design is revised.

## Rollback

Delete `docs/codex/tasks/pspc-sequence-experience-eval-v0-1/`, `scripts/run_pspc_sequence_experience_eval_v0_1.py`, `tests/test_pspc_sequence_experience_eval_v0_1.py`, `artifacts/pspc_sequence_experience_eval_v0_1/`, and matching governance/generated-view entries.
