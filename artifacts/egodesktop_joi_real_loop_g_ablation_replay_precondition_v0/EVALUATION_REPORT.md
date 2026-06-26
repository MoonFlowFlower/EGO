# EgoDesktop Joi Real-Loop G-ABLATION Replay/Leakage Evaluator Report

- status: `blocked_d_field_replay_precondition_not_satisfied`
- claim_ceiling: `egodesktop_real_loop_g_ablation_replay_leakage_evaluator_contract_only`
- rows_evaluated: `1`
- leakage_scan_status: `pass`
- leakage_positive_control_status: `pass`

## Current Meaning

This is replay/leakage evaluator contract only. It can check row hash integrity and leakage scanner positive
controls, but the listed replay blockers prevent verdicts: no real replay, baseline, or attribution claim is authorized.

## Blockers

- `collect_only_replay_policy`
- `complete_observation_serialized_missing`
- `complete_state_serialized_missing`
- `condition_not_off_static_replay_heldout`
- `d_field_freeze_missing`
- `missing_llm_replay_id`
- `offline_replay_function_unavailable`

## What This Does Not Prove

This does not prove real-loop effect, baseline superiority, route advancement, product benefit, stable user
benefit, durable memory efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness,
alive status, or Bar-2 specialness.
