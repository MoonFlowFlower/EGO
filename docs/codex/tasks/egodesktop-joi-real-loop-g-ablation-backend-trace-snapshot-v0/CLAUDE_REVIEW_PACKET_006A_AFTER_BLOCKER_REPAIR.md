# Claude Review Packet: 006A Repairs After Source-Limited Blocking Findings

Please re-review the 006-to-007 boundary. Return exactly one of:

- `NO_BLOCKING_FINDINGS`, with next minimal action; or
- `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.

If Ego repo/artifacts are still not reachable, state `source-limited`.

## Repo / State

- repo: `D:\Project\AIProject\MyProject\Ego`
- branch: `main`
- base 006 implementation commit: `b434ffbae73fa80bc1476a3d0d0d71687a659df6`
- packet commit before these repairs: `c1e8b56f`
- current claim ceiling: `egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`
- current row label: `schema_valid_collect_only_snapshot`
- current row replay status: unreplayable, `trace_runner_v0_collect_only`, `llm_replay_id: none`

## Repairs Against Your Blocking Findings

1. Claim hygiene repaired.
   - Removed the stronger row claim from 006 docs/packet/task-board language.
   - Current wording: `schema_valid_collect_only_snapshot`.
   - Explicit caveat: current rows do not satisfy 001C section 12 because replay recomputation from complete serialized
     state plus observation is absent.
2. Replay feasibility precondition added.
   - New file: `D_FIELD_REPLAY_PRECONDITION_007.md`.
   - Status: `D_FIELD_FREEZE_STATUS: not_satisfied_for_scoring`.
   - Blocks any >=007 scoring run until non-LLM `D` fields are frozen, full state and observation are serialized, and
     adapter output can be recomputed offline.
3. Evaluator delta gate added.
   - New function: `summarizeReplayBlockerDelta`.
   - New tests assert placeholder positive control still fires and that 006 row still preserves replay blockers.
   - New artifact:
     `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/evaluator/blocker_delta_report.json`
   - Artifact result:
     - `status: placeholder_blockers_removed_replay_blockers_remain`
     - `placeholder_positive_control_status: pass`
     - `placeholder_removed_status: pass`
     - `replay_blockers_preserved_status: pass`
     - before blockers: `collect_only_replay_policy`, `missing_llm_replay_id`, `placeholder_adapter_output`,
       `placeholder_creature_state`
     - after blockers: `collect_only_replay_policy`, `missing_llm_replay_id`
4. Mutation-scope closeout readback corrected.
   - New file: `CLOSEOUT_SCOPE_READBACK_006A.md`.
   - Correct command form:
     `python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0\MUTATION_SCOPE.yaml closeout-check --format markdown`
   - The prior packet's "no CLI option" statement was wrong; the option is top-level and must precede `closeout-check`.
   - With correct invocation, the guard reports `mutation_scope: loaded` and `unsafe: 0` before these 006A edits.
   - With the current 006A dirty worktree, the same command reports
     `dirty_scoped/task_scoped/local_only/unsafe: 3 / 11 / 0 / 0`.
5. Minimal surface attached.
   - New file: `MINIMAL_SURFACE_006.md`.
   - It records: instrument existing seam only, reuse 003/004 trace writer, default-off, rows-only, no baseline/route
     verdict, tests-first, no state/ledger/push widening.

## New/Changed Files For 006A

- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_backend_snapshot.test.js`
- `tests/test_egodesktop_gablation_review_repair.py`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0/D_FIELD_REPLAY_PRECONDITION_007.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0/MINIMAL_SURFACE_006.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0/CLOSEOUT_SCOPE_READBACK_006A.md`
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/evaluator/blocker_delta_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/evaluator/BLOCKER_DELTA_REPORT.md`
- 006 docs/task-board wording updated for the downgraded row label and 007 precondition.

## Checks Run For 006A

- Red:
  - `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js` failed before delta function existed.
  - `python -m pytest -q tests\test_egodesktop_gablation_review_repair.py` failed before docs/precondition repairs.
- Green:
  - `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js` passed: `5 passed`.
  - `python -m pytest -q tests\test_egodesktop_gablation_review_repair.py` passed: `3 passed`.

## Review Questions

1. Are B1, B3, B4, and B5 now repaired enough for re-review under source-limited conditions?
2. Is B2 properly converted into a hard precondition for 007 rather than hidden as current evidence?
3. Is 007 now correctly constrained to a single-condition non-LLM replay recomputation slice before any baseline or
   attribution verdict?

## Claim Boundary

Do not call 006 or 006A replay-ready, 001C section 12 conformant, route-B pass, attribution pass, baseline result, EGO
readiness, product benefit, agency, real emotion, subjectivity, consciousness, alive status, or Bar-2/specialness.

Strongest allowed claim:

> 006A repairs the review packet/evaluator/closeout evidence surface. The 006 row remains a
> `schema_valid_collect_only_snapshot`; no replay, baseline, or attribution verdict is authorized.
