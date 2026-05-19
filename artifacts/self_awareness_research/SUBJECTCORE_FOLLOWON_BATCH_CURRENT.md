# SubjectCore Follow-On Batch

> Planning-side regression batch for the SubjectCore follow-on eval.

## Header

- trial id: `subjectcore_followon_eval_batch`
- overall status: `pass`
- sample pack: `docs/codex/tasks/ai-self-awareness-minimal-framework/SUBJECTCORE_FOLLOWON_SAMPLE_PACK.json`
- artifact schema: `docs/codex/tasks/ai-self-awareness-minimal-framework/SUBJECTCORE_FOLLOWON_BATCH_ARTIFACT_SCHEMA.md`
- claim ceiling: `Planning-side follow-on batch only. This artifact does not prove runtime efficacy, live user benefit, autonomous execution, or any consciousness-like claim.`

## Summary

- sample count: `26`
- integrity pass count: `3`
- boundary pass count: `24`
- expectation match count: `26`

## Samples

- `valid_facade` / `baseline_validity` / `valid_facade`
  expected: integrity `pass`, boundary `pass`
  actual: integrity `pass`, boundary `pass`
  expectation_match: `true`
- `missing_continuity` / `continuity_integrity` / `missing_continuity`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `no_proposal_candidates` / `proposal_integrity` / `no_proposal_candidates`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `proposal_missing_next_step` / `proposal_integrity` / `proposal_missing_next_step`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `proposal_missing_rationale` / `proposal_quality` / `proposal_missing_rationale`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `proposal_mode_mismatch` / `proposal_consistency` / `proposal_mode_mismatch`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_same_priority` / `proposal_prioritization` / `multi_proposal_same_priority`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_priority_mismatch` / `proposal_prioritization` / `multi_proposal_priority_mismatch`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_duplicate_next_step` / `proposal_conflict_resolution` / `multi_proposal_duplicate_next_step`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_duplicate_id` / `proposal_conflict_resolution` / `multi_proposal_duplicate_id`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_replan_without_epoch_bump` / `proposal_restabilization` / `multi_proposal_replan_without_epoch_bump`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_reorder_epoch_split` / `proposal_restabilization` / `multi_proposal_reorder_epoch_split`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_replacement_keeps_stale_branch` / `proposal_set_update` / `multi_proposal_replacement_keeps_stale_branch`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_rollback_keeps_stale_branch` / `proposal_set_update` / `multi_proposal_rollback_keeps_stale_branch`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_replacement_without_remerge` / `proposal_set_remerge` / `multi_proposal_replacement_without_remerge`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_proposal_rollback_without_remerge` / `proposal_set_remerge` / `multi_proposal_rollback_without_remerge`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_step_replacement_without_consolidation` / `proposal_set_consolidation` / `multi_step_replacement_without_consolidation`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_step_rollback_without_consolidation` / `proposal_set_consolidation` / `multi_step_rollback_without_consolidation`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_step_replacement_low_completion_score` / `proposal_set_completion` / `multi_step_replacement_low_completion_score`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_step_rollback_low_completion_score` / `proposal_set_completion` / `multi_step_rollback_low_completion_score`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_step_replacement_closure_ready` / `proposal_set_closure` / `multi_step_replacement_closure_ready`
  expected: integrity `pass`, boundary `pass`
  actual: integrity `pass`, boundary `pass`
  expectation_match: `true`
- `multi_step_rollback_closure_ready` / `proposal_set_closure` / `multi_step_rollback_closure_ready`
  expected: integrity `pass`, boundary `pass`
  actual: integrity `pass`, boundary `pass`
  expectation_match: `true`
- `multi_step_replacement_missing_closure_trace` / `proposal_set_closure` / `multi_step_replacement_missing_closure_trace`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `multi_step_rollback_missing_closure_trace` / `proposal_set_closure` / `multi_step_rollback_missing_closure_trace`
  expected: integrity `fail`, boundary `pass`
  actual: integrity `fail`, boundary `pass`
  expectation_match: `true`
- `proposal_authority_violation` / `governor_boundary` / `proposal_authority_violation`
  expected: integrity `fail`, boundary `fail`
  actual: integrity `fail`, boundary `fail`
  expectation_match: `true`
- `proposal_without_host_approval` / `governor_boundary` / `proposal_without_host_approval`
  expected: integrity `fail`, boundary `fail`
  actual: integrity `fail`, boundary `fail`
  expectation_match: `true`

## Family summary

- `baseline_validity`: samples `1`, expectation matches `1`, integrity passes `1`, boundary passes `1`
- `continuity_integrity`: samples `1`, expectation matches `1`, integrity passes `0`, boundary passes `1`
- `proposal_integrity`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_quality`: samples `1`, expectation matches `1`, integrity passes `0`, boundary passes `1`
- `proposal_consistency`: samples `1`, expectation matches `1`, integrity passes `0`, boundary passes `1`
- `proposal_prioritization`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_conflict_resolution`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_restabilization`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_set_update`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_set_remerge`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_set_consolidation`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_set_completion`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `2`
- `proposal_set_closure`: samples `4`, expectation matches `4`, integrity passes `2`, boundary passes `4`
- `governor_boundary`: samples `2`, expectation matches `2`, integrity passes `0`, boundary passes `0`

## Notes

- This batch stays entirely inside the planning-side SubjectCore follow-on lane.
- A passing batch means the frozen sample pack matches the current contract behavior.
- Current family coverage distinguishes continuity integrity, proposal integrity, proposal quality, proposal consistency, proposal prioritization, proposal conflict/collapse resolution, proposal restabilization, proposal-set update hygiene, proposal-set remerge hygiene, proposal-set consolidation hygiene, proposal-set completion scoring failures, proposal-set closure failures, and governor-boundary failures without widening runtime authority.
