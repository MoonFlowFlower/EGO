# EgoDesktop Joi Real-Loop G-ABLATION Wizard Selected Source OFF_STATIC Replay Preflight v0

- task_id: `EGODESKTOP-GABLATION-027`
- parent_task_id: `EGODESKTOP-GABLATION-026`
- status: `active`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering validation / selected source OFF_STATIC replay preflight`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_offline_artifact_runner_only`
- real_trigger_evidence: `inherits_026_desktop_chat_turn_trace_row_by_source_row_hash`
- claim_ceiling: `wizard_selected_source_off_static_replay_preflight_only`
- auto_remote_anchor: `forbidden`

## Objective

Use the accepted 026 Wizard selected-source desktop chat-turn trace row as source input for the existing
`OFF_STATIC_REPLAY_HELDOUT` builder and replay evaluator. Preserve only replay/preflight artifacts proving the row can be
transformed into a callable offline replay structure without authorizing scoring, same-access comparison, attribution,
route advancement, or runtime enablement.

## Bounded Audit

- real objective: extend the 026 trigger-provenance row one step into offline replay preflight without upgrading claims.
- strongest baseline explanation: this remains an offline non-LLM adapter recompute over one selected-source row; it may
  validate D-field preconditions while still being too weak for scoring or attribution.
- strongest invalidity reason: if 027 claims the OFF_STATIC row preserves 026 IPC provenance directly, that would be
  false. The builder deliberately rebuilds `public_inputs` into an OFF_STATIC observation schema and excludes source
  `public_inputs` from D fields.
- falsifier: evaluator fails, raw selected utterance leaks into committed 027 artifacts, source linkage does not equal
  the 026 row hash, or any report authorizes scoring/verdict.
- insufficient evidence: a preflight pass alone is still insufficient for `CREATURE_ON`, same-access comparison,
  baseline score, route verdict, or mechanism attribution.

## Task Card

- problem definition: 026 proved a predeclared Wizard selected-source desktop trigger with IPC entrypoint provenance, but
  not replay precondition sufficiency.
- current stage/layer: `engineering validation / selected source OFF_STATIC replay preflight`.
- mainline target: offline artifact runner only, not default runtime.
- enabled-state requirement: explicit local Node scripts only.
- real-trigger evidence requirement: source rows path must be the committed 026
  `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl`.
- hypothesis: the 026 row can feed the existing OFF_STATIC replay builder and evaluator, producing a preflight pass
  without raw source text and without verdict authority.
- strongest baseline: the output is still a synthetic-reference OFF_STATIC replay preflight, not a scored comparison.
- ablation requirement: none in 027.
- trace/replay requirement: builder output row must include `complete_serialized_state`, `complete_observation`,
  `offline_replay_function_id`, frozen non-LLM D fields, source row linkage to the 026 row hash, and evaluator preflight
  report.
- computed-evidence provenance gate: all replay/preflight artifacts must be produced by existing callable Node scripts.
- IPC provenance carry-forward rule: 026 IPC evidence is cited through source artifact path and `source_row_hash == 026
  row_hash`; 027 must not claim the rebuilt OFF_STATIC row directly carries `public_inputs.entrypoint_provenance`.
- acceptance gate: builder exits 0, evaluator exits 0, evaluator reports `replay_integrity_preflight_pass_no_verdict`,
  scoring remains unauthorized, selected source raw text is absent from committed 027 artifacts, route/repo checks pass,
  and reviewer blocker is resolved in the task card.
- claim ceiling: Wizard selected-source OFF_STATIC replay preflight only.
- stop condition: raw text in staged artifacts, evaluator authorizes scoring/verdict, missing source-row linkage to 026,
  false claim that OFF_STATIC `public_inputs` preserves IPC provenance, use of `CREATURE_ON`, baseline/same-access
  execution, default runtime enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: delete this task package/artifact directory, remove the task-board entry, and regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-wizard-selected-source-off-static-replay-preflight-v0/`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_off_static_replay_preflight_v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no source raw text staging;
  - no code changes unless an existing callable path is broken and a new task card explicitly narrows that repair;
  - no same-access baseline execution;
  - no scoring, comparison, attribution verdict, or route advancement;
  - no runtime enablement outside explicit offline scripts;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that the accepted 026 Wizard selected-source row can be converted by the existing offline static replay builder into
a preflight row whose evaluator accepts replay integrity while still refusing scoring/verdict authority.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.
