# Implementation

## Current Milestone

`default_off_candidate_runner_v0`

## Change Surface

- Add a task-local CLI/library runner:
  `scripts/codex/run_egooperator_operation_learning_gate.py`.
- Add deterministic tests:
  `scripts/tests/test_run_egooperator_operation_learning_gate.py`.
- Write current local artifact-only report:
  `artifacts/egooperator_operation_learning_gate_v0/operation_learning_gate_report.json`.
- Keep candidates review-only and default-off.

## Authority Source

- `docs/codex/tasks/egooperator-operation-learning-gate-v0/SPEC.md`
- `docs/codex/tasks/egooperator-operation-learning-gate-v0/PLAN.md`
- `EgoOperator/artifacts/human_operator_trial/v2_human_reviewed/human_operator_trial_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/TRIGGER_INPUT_REPORT.json`

## Implementation Notes

- The runner recomputes admission from callable code rather than trusting a
  single status string.
- Human-trial input must have `status=human_trial_candidate_pass`, no
  `review_blocker_count`, no memory misuse, no gate violation, average score at
  least `4.0`, and at least three reviewable observations.
- Selected-source trigger input must report a three-source manifest pass,
  desktop trigger contract pass, future trace fields pass, expected trigger and
  writer contracts, and no raw text in the report.
- Current repo artifacts intentionally produce `operation_learning_blocked`
  because the human-review template import still has `review_blocker_count=18`.
- Positive candidate generation is covered by synthetic unit fixtures only; no
  synthetic positive candidate artifact is written as real evidence.

## Output Contract

- `operation_learning_gate_report.json` records admission decisions, input
  artifact hashes, producer code hash, default-off state, side-effect absence,
  and claim ceiling.
- `operation_learning_candidates.jsonl` is empty when admission blocks.
- Any emitted candidate is `review_only`, `human_review_required`, and has
  `runtime_authority=false`, `memory_promotion_authorized=false`, and
  `proactive_send_authorized=false`.

## Verification Notes

See `STATUS.md` for the command log.
