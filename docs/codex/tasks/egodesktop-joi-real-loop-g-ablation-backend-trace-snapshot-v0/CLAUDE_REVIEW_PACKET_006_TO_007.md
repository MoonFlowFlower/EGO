# Claude Review Packet: EGODESKTOP-GABLATION-006 to 007

Please review this as an external EGO-side reviewer. Return exactly one of:

- `NO_BLOCKING_FINDINGS`, with the next minimal action; or
- `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and the next minimal action.

If you cannot directly read the repo/artifacts, state that the review is source-limited.

## Repo / State

- repo: `D:\Project\AIProject\MyProject\Ego`
- branch: `main`
- current commit: `b434ffbae73fa80bc1476a3d0d0d71687a659df6`
- git status at packet creation: clean, `main...origin/main [ahead 8]`
- current lane: EgoDesktop Joi real-loop G-ABLATION evidence-hygiene slice
- current layer: engineering implementation / backend trace snapshot wiring
- mainline integration status: not connected to default runtime
- enabled status: default-off, explicit `JOI_REAL_LOOP_*` flags only
- claim ceiling: `egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`

Repo-level bootstrap still says global EGO highest evidence is E3 and the repo-level next minimal action remains human
operator trial review. This G-ABLATION lane must not update `PROGRAM_STATE_UNIFIED.yaml` or evidence ledger.

## 006 Commit Summary

Commit: `b434ffba feat: add egodesktop backend trace snapshot`

Changed surfaces:

- `scripts/ego_operator_desktop_turn.py`
  - Adds flag-gated `JsonlTraceStore` tap only when `JOI_REAL_LOOP_G_ABLATION=1` and `JOI_REAL_LOOP_TRACE_DIR` exists.
  - Reads back the same backend turn's last trace record after `runtime.handle_user_message(...)`.
  - Builds a sanitized snapshot with hashes / state digest / viability state / side-effect boundary.
  - Does not fabricate `llm_replay_id`; only emits `joi_real_loop_llm_replay_id` if an explicit replay id exists in `llm_meta`.
- `EgoDesktop/src/main.js`
  - At the existing `ipcMain.handle("ego-desktop:chat-turn", ...)` result boundary, passes `backend.joi_real_loop_trace_snapshot`,
    `buildJoiRealLoopBackendAdapterOutput(...)`, and `backend.joi_real_loop_llm_replay_id` into the existing
    `joiTraceRunner.recordChatTurn(...)`.
- `EgoDesktop/src/joiRealLoopGAblationTraceRunner.js`
  - Adds `buildJoiRealLoopBackendAdapterOutput(...)` as source-limited adapter output.
  - No second trace writer or second chat-turn path.
- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`
  - Report wording now describes listed blockers generically instead of assuming placeholder state.
- tests:
  - `tests/test_ego_operator_desktop_trace_snapshot.py`
  - `EgoDesktop/tests/joi_real_loop_g_ablation_backend_snapshot.test.js`
- docs/artifacts:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0/`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/`

## Evidence

006 row path:

- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/trace/trace_rows.jsonl`

Key row facts:

- `trace_row_count: 1`
- `condition_id: CURRENT_SHIM`
- `llm_replay_id: none`
- `creature_state.state_source: ego_operator_runtime_trace_store`
- `adapter_output.adapter_status: connected_real_backend_trace_snapshot`
- `replay_inputs.replay_policy: trace_runner_v0_collect_only`
- evidence label: `schema_valid_collect_only_snapshot`; this does not satisfy 001C section 12 because replay
  recomputation from complete serialized state plus observation is not implemented
- `renderer_idle_excluded: true`

Evaluator path:

- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/evaluator/evaluation_report.json`

Evaluator result:

- `status: blocked_unreplayable_runtime_trace`
- `rows_evaluated: 1`
- `hash_integrity_status: pass`
- `leakage_scan_status: pass`
- `leakage_positive_control_status: pass`
- blockers: `collect_only_replay_policy`, `missing_llm_replay_id`
- no `placeholder_creature_state` blocker
- no `placeholder_adapter_output` blocker
- `verdict_authorized: false`

Verification run:

- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js ...` focused G-ABLATION suite:
  `16 passed`
- focused Python desktop context/snapshot suite: `59 passed`
- `npm test` from `EgoDesktop`: `82 passed`
- Electron smoke with explicit `JOI_REAL_LOOP_*` flags: exited `0`, `joiRealLoopChatSmoke.status=chat_turn_trace_smoke_pass`
- `python scripts\codex\verify_route_convergence.py`: pass
- `python scripts\codex\verify_repo.py --mode fast`: pass
- `git diff --check`: pass
- strict secret-pattern scan over 006 docs/tests/artifacts: no API keys found

Closeout note:

- `python scripts\codex_session_guard.py closeout-check --format markdown` has no CLI option for loading this task's
  mutation scope. It reports `mutation_scope: not_configured` and keeps classifying the new 006 docs/tests/artifacts as
  unsafe even when staged. This was documented as a closeout tooling limitation, not hidden as pass.

## Review Questions

1. Does 006 satisfy the minimal surface from your previous review: instrument existing real chat-turn result boundary,
   reuse trace_rows.jsonl, default-off, no second chat-turn logic path, no fabricated LLM replay id, no baseline verdict?
2. Is the next minimal action correctly constrained to `EGODESKTOP-GABLATION-007`: real replay recomputation from
   serialized state plus observation, or a true LLM replay contract?
3. Are there blockers that must be repaired before 007, especially around:
   - whether the snapshot is still too lossy to support replay recomputation;
   - whether `viability_state`/state digest is enough to call serialized state;
   - whether the backend trace-store tap changes default behavior when flags are absent;
   - whether `llm_trace_id` could be misread as replay id despite `llm_replay_id=none`;
   - whether evaluator wording still risks overclaim.

## Claim Boundary

Do not call this a route-B pass, attribution pass, replay-ready row, baseline result, EGO readiness signal, product
benefit, agency, real emotion, subjectivity, consciousness, alive status, or Bar-2/specialness result.

The strongest allowed claim is:

> Under explicit flags, EgoDesktop can collect `schema_valid_collect_only_snapshot` rows through the existing chat-turn
> path; the current rows remain unreplayable, do not satisfy 001C section 12, and no verdict is authorized.

## Requested Verdict Format

Return one:

```text
NO_BLOCKING_FINDINGS
next minimal action: ...
claim ceiling: ...
```

or:

```text
BLOCKING_FINDINGS
1. ...
required repair: ...
next minimal action: ...
claim ceiling: ...
```
