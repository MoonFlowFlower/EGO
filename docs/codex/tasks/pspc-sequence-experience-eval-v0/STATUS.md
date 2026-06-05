# PSPC Sequence Experience Eval v0 Status

- status: `pass`
- verdict: `sequence_experience_eval_pass__manual_review_still_required`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only`
- runtime authority: `none`
- mainline_connected: `false`
- enabled: `false`
- EgoOperator integration: `forbidden`

## Evidence

- Dataset: `docs/codex/tasks/pspc-sequence-experience-eval-v0/sequence_eval_dataset_v0.jsonl`
- Runner: `scripts/run_pspc_sequence_experience_eval.py`
- Tests: `tests/test_pspc_sequence_experience_eval.py`
- Artifact report: `artifacts/pspc_sequence_experience_eval_v0/SEQUENCE_EXPERIENCE_EVAL_REPORT.md`
- Machine artifact: `artifacts/pspc_sequence_experience_eval_v0/sequence_experience_eval.json`

## Result

The eval records controlled history sequences for gentle interaction, frequent interruption, and late-night care, then applies the same trigger `我回来了。`. The produced shadow-only trigger profiles diverge:

- gentle interaction biases toward approach/trust
- frequent interruption biases toward avoidance/boundary
- late-night care biases toward care/low-interrupt
- no-history remains neutral
- shuffled-history remains mixed and not identical to clean sequence profiles

## What This Proves

This proves a controlled lab/shadow sequence accumulator can record history inputs as proxy relationship/self-state deltas and produce different audit-only trigger observations for the same trigger without runtime authority or EgoOperator side effects.

## What This Does Not Prove

It does not prove PSPC is integrated into EgoOperator, live runtime integration safety, adapter readiness, real user benefit, durable EgoOperator memory efficacy, live autonomy, philosophical consciousness, subjective experience, or that proxy variables are real emotion or real selfhood.

## Failure Meaning

Failure would mean the sequence proxy does not yet demonstrate history-shaped trigger divergence under the bounded lab/shadow contract. The correct response would be `no_go_keep_shadow_only_for_sequence_eval`.

## Rollback

Delete `scripts/run_pspc_sequence_experience_eval.py`, `tests/test_pspc_sequence_experience_eval.py`, `docs/codex/tasks/pspc-sequence-experience-eval-v0/`, `artifacts/pspc_sequence_experience_eval_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.
