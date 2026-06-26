# EgoDesktop Joi Real-Loop G-ABLATION Replay Precondition v0 Status

- status: `active__precondition_abort_gate_written`
- task_id: `EGODESKTOP-GABLATION-007`
- claim_ceiling: `egodesktop_real_loop_g_ablation_replay_precondition_contract_only`
- mainline_connected: `false`
- enabled: `explicit_cli_only`
- real_trigger_evidence: `cli_precondition_abort_over_current_006_row`
- runtime_authority: `none`
- claude_reviewer_status: `NO_BLOCKING_FINDINGS_SOURCE_LIMITED_FOR_006A_NARROW_CLAIM`

## Current Objective

Stop 006 surface repair and make the 007 replay/D-field precondition executable. Current 006 rows remain
`schema_valid_collect_only_snapshot`; they are not replayable and must abort any >=007 scoring request.

## Carry-Forward Gates

- N3: the precondition must be a runtime/evaluator abort gate, not only a `.md` reminder.
- N1: report test totals with a consistent command scope before closeout.
- N4: future blocker-delta evidence should be generated from a git-pinned evaluator run, not constants.
- N2: mutation-scope honesty must be checked with scoped closeout; do not widen the scope to hide unrelated edits.
- B4: current leakage pass is low-signal and does not settle CREATURE_ON privileged-field leakage.
- B5: trace_id/replay_id distinction is deferred, not repaired, until LLM-modulated `D` appears.

## Red Checks

- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_replay_evaluator.test.js` fails because
  `evaluateScoringPreconditions` is absent and the CLI still exits `0` when `--require-007-scoring-precondition` is used.

## Current Result

The executable 007 precondition gate is implemented in the existing replay evaluator/CLI path. Normal collect-only
evaluation remains available. When `--require-007-scoring-precondition` is supplied, current 006 rows abort before any
scoring path with:

- `status: blocked_d_field_replay_precondition_not_satisfied`
- `scoring_authorized: false`
- `required_condition: OFF_STATIC_REPLAY_HELDOUT`
- blockers: `collect_only_replay_policy`, `complete_state_serialized_missing`,
  `complete_observation_serialized_missing`, `condition_not_off_static_replay_heldout`,
  `d_field_freeze_missing`, and `offline_replay_function_unavailable`

Produced artifact:

- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_precondition_v0/evaluation_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_precondition_v0/EVALUATION_REPORT.md`

## Green Checks So Far

- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_replay_evaluator.test.js`: `6 passed`
- CLI over current 006 row with `--require-007-scoring-precondition --required-condition OFF_STATIC_REPLAY_HELDOUT`
  exited `3`; wrapper treated that expected abort as check pass and wrote the artifact above.
- Focused JS regression:
  `node --test EgoDesktop\tests\joi_real_loop_g_ablation_replay_evaluator.test.js EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js EgoDesktop\tests\joi_real_loop_g_ablation_trace_runner.test.js EgoDesktop\tests\joi_real_loop_g_ablation_chat_turn_trace.test.js`:
  `20 passed`
- Focused Python regression:
  `python -m pytest -q tests\test_egodesktop_gablation_review_repair.py tests\test_ego_operator_desktop_trace_snapshot.py`:
  `6 passed`
- `npm test` from `EgoDesktop`: `86 passed`
- Test-count reconciliation: 006A post-commit `npm test` was `84 passed`; 007 adds two replay-precondition tests and
  current `npm test` is `86 passed`. `git diff --numstat -- EgoDesktop\tests` reports `45 / 0` for the edited test file,
  so no test deletion is present in this slice.
- `python scripts\codex\verify_repo.py --mode fast`: passed
- `python scripts\codex\verify_route_convergence.py`: passed
- `git diff --check`: passed
- Scoped closeout with `MUTATION_SCOPE.yaml`: `mutation_scope: loaded`, `unsafe: 0`; blockers are `push_pending`,
  `no_staged_changes`, and `remote_sync_unavailable`.

## Next Minimal Closed-Loop Action

Run focused/broad verification, route-convergence checks, scoped closeout, and local commit. The next implementation
slice after this must produce one actual `OFF_STATIC_REPLAY_HELDOUT` non-LLM `D` replay row with complete serialized
state plus observation and a callable offline adapter recompute function.
