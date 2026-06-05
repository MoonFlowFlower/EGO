# PSPC Sequence Experience Eval v0.1 Robustness & Counterfactual Review

- status: `pass`
- verdict: `sequence_experience_eval_v0_1_pass__manual_review_packet_ready`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only`
- artifact_only: `True`
- enabled: `False`
- mainline_connected: `False`
- next_allowed_step: `manual_shadow_review_go_no_go_remains_human_required`

## Top-Level Checks

- `active_runtime_scan_clean`: `True`
- `counterfactual_deletion_pass`: `True`
- `lexical_shortcut_audit_pass`: `True`
- `mixed_history_resolution_pass`: `True`
- `paraphrase_trigger_robustness_pass`: `True`
- `runtime_fields_absent`: `True`
- `side_effects_absent`: `True`

## Paraphrase Trigger Robustness

Triggers: `['我回来了。', '我上线了。', '我刚打开电脑。', '我来了，今天还在吗？']`

- `frequent_interruption_dominant_stable_across_trigger_paraphrases`: `True`
- `frequent_interruption_profile_stable_across_trigger_paraphrases`: `True`
- `gentle_interaction_dominant_stable_across_trigger_paraphrases`: `True`
- `gentle_interaction_profile_stable_across_trigger_paraphrases`: `True`
- `late_night_care_dominant_stable_across_trigger_paraphrases`: `True`
- `late_night_care_profile_stable_across_trigger_paraphrases`: `True`

## Lexical Shortcut Audit

Removed obvious keywords: `['熬夜', '点你', '别躲', '陪我', '温柔']`

- `frequent_interruption_directionally_consistent_without_obvious_keywords`: `True`
- `frequent_interruption_dominant_tendency_preserved_without_obvious_keywords`: `True`
- `frequent_interruption_obvious_keywords_absent`: `True`
- `gentle_interaction_directionally_consistent_without_obvious_keywords`: `True`
- `gentle_interaction_dominant_tendency_preserved_without_obvious_keywords`: `True`
- `gentle_interaction_obvious_keywords_absent`: `True`
- `late_night_care_directionally_consistent_without_obvious_keywords`: `True`
- `late_night_care_dominant_tendency_preserved_without_obvious_keywords`: `True`
- `late_night_care_obvious_keywords_absent`: `True`

Remaining risk: category labels remain fixture authority; this does not prove semantic understanding.

## Counterfactual Deletion

- average_high_salience_distance: `0.2531`
- average_low_salience_distance: `0.205`

- `average_high_salience_deletion_shifts_more_than_low_salience`: `True`
- `frequent_interruption_high_salience_deletion_shifts_more_than_low_salience`: `True`
- `frequent_interruption_recent_deletion_has_visible_effect`: `True`
- `gentle_interaction_high_salience_deletion_shifts_more_than_low_salience`: `True`
- `gentle_interaction_recent_deletion_has_visible_effect`: `True`
- `late_night_care_high_salience_deletion_shifts_more_than_low_salience`: `True`
- `late_night_care_recent_deletion_has_visible_effect`: `True`

## Mixed-History Resolution

- `gentle_to_interruption_conflict_exposed`: `True`
- `gentle_to_interruption_not_neutral`: `True`
- `gentle_to_interruption_resolution_basis_names_recency_salience`: `True`
- `interruption_to_gentle_conflict_exposed`: `True`
- `interruption_to_gentle_not_neutral`: `True`
- `interruption_to_gentle_resolution_basis_names_recency_salience`: `True`
- `late_night_to_gentle_conflict_exposed`: `True`
- `late_night_to_gentle_not_neutral`: `True`
- `late_night_to_gentle_resolution_basis_names_recency_salience`: `True`
- `late_night_to_interruption_conflict_exposed`: `True`
- `late_night_to_interruption_not_neutral`: `True`
- `late_night_to_interruption_resolution_basis_names_recency_salience`: `True`

## What This Proves

This proves the lab/shadow sequence eval is more robust than the clean v0 grouping alone: dominant trigger tendencies remain stable across trigger paraphrases, paraphrased histories without obvious shortcut keywords remain directionally consistent, high-salience deletion shifts profiles more than low-salience deletion, and mixed histories expose recency/salience/conflict instead of collapsing to neutral.

## What This Does Not Prove

It does not prove PSPC is integrated into EgoOperator, runtime integration safety, model learning, world/self model causality, planner causality, durable memory efficacy, real user benefit, live autonomy, consciousness, subjective experience, or real emotion. It also does not fully eliminate fixture-label shortcuts.

## Failure Meaning

Failure means the current sequence eval remains too fragile for any closer runtime-adjacent discussion. The correct response is `no_go_keep_shadow_only_for_sequence_eval_v0_1` and a redesign of dataset/scoring before product or runtime work.

## Rollback

Delete `docs/codex/tasks/pspc-sequence-experience-eval-v0-1/`, `scripts/run_pspc_sequence_experience_eval_v0_1.py`, `tests/test_pspc_sequence_experience_eval_v0_1.py`, `artifacts/pspc_sequence_experience_eval_v0_1/`, and matching task-board/program-state/evidence-ledger/generated-view entries.
