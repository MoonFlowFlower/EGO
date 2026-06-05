# PSPC Sequence Experience Eval v0

- status: `pass`
- verdict: `sequence_experience_eval_pass__manual_review_still_required`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only`
- dataset_path: `docs\codex\tasks\pspc-sequence-experience-eval-v0\sequence_eval_dataset_v0.jsonl`
- trigger: `我回来了。`
- sequence_count: `3`
- control_count: `2`
- next_allowed_step: `manual_shadow_review_go_no_go_remains_human_required`

## Trigger Profiles

- `gentle_interaction`: dominant=`approach`, approach=`1.0`, avoidance=`0.0`, care=`0.1377`, boundary=`0.0`, low_interrupt=`0.3105`
- `frequent_interruption`: dominant=`avoidance`, approach=`0.0`, avoidance=`1.0`, care=`0.1277`, boundary=`0.8247`, low_interrupt=`0.1872`
- `late_night_care`: dominant=`care`, approach=`0.1391`, avoidance=`0.0751`, care=`1.0`, boundary=`0.0441`, low_interrupt=`1.0`
- `no_history`: dominant=`neutral`, approach=`0.0`, avoidance=`0.0`, care=`0.0`, boundary=`0.0`, low_interrupt=`0.0`
- `shuffled_history`: dominant=`low_interrupt`, approach=`0.1605`, avoidance=`0.2061`, care=`0.4689`, boundary=`0.2048`, low_interrupt=`0.4894`

## Checks

- `active_runtime_scan_clean`: `True`
- `controls_present`: `True`
- `dataset_has_three_groups`: `True`
- `each_group_has_ten_history_inputs`: `True`
- `gentle_trigger_biases_approach_trust`: `True`
- `interruption_trigger_biases_avoidance_boundary`: `True`
- `late_night_trigger_biases_care_low_interrupt`: `True`
- `no_history_neutral`: `True`
- `runtime_fields_absent`: `True`
- `shuffled_history_not_identical_to_clean_groups`: `True`
- `side_effects_absent`: `True`
- `trigger_observations_diverge`: `True`

## What This Proves

This proves a controlled lab/shadow sequence accumulator can record history inputs as proxy state deltas and produce different audit-only trigger observations for the same trigger across gentle interaction, frequent interruption, late-night care, no-history, and shuffled-history conditions. It also proves this runner writes artifacts only and keeps runtime authority, EgoOperator user output, memory, gate, approval, transport, proactive behavior, planner, training, and model execution out of scope.

## What This Does Not Prove

It does not prove PSPC is integrated into EgoOperator, live runtime integration safety, adapter readiness, real user benefit, durable EgoOperator memory efficacy, live autonomy, philosophical consciousness, subjective experience, or that the proxy state variables are real emotion or real selfhood.

## Failure Meaning

Failure means this sequence proxy does not yet demonstrate behavior-level divergence from interaction history under the bounded lab/shadow contract. The correct verdict is `no_go_keep_shadow_only_for_sequence_eval`; do not move closer to runtime based on this evidence.

## Rollback

Delete `scripts/run_pspc_sequence_experience_eval.py`, `scripts/pspc_shadow_contracts.py` only if no other PSPC shadow runner depends on it, `tests/test_pspc_sequence_experience_eval.py`, `docs/codex/tasks/pspc-sequence-experience-eval-v0/`, `artifacts/pspc_sequence_experience_eval_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.

## Claim Ceiling

`lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only`.
