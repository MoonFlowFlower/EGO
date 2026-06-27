# EgoDesktop Joi Real-Loop G-ABLATION Selected Source OFF_STATIC Replay Preflight v0

- task_id: `EGODESKTOP-GABLATION-023`
- parent_task_id: `EGODESKTOP-GABLATION-022`
- status: `active`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering validation / selected source replay preflight`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_offline_artifact_runner_only`
- real_trigger_evidence: `inherits_022_desktop_chat_turn_trace_row`
- claim_ceiling: `selected_source_off_static_replay_preflight_only`
- auto_remote_anchor: `forbidden`

## Objective

Use the accepted 022 selected-source desktop chat-turn trace row as source input for the existing
`OFF_STATIC_REPLAY_HELDOUT` builder and replay evaluator. Preserve only replay/preflight artifacts that prove the row can
be transformed into a callable offline replay structure without authorizing scoring, same-access comparison, attribution,
route advancement, or runtime enablement.

## Task Card

- problem definition: 022 proved selected-source desktop trigger capture, but not replay precondition sufficiency.
- current stage/layer: `engineering validation / selected source replay preflight`.
- mainline target: offline artifact runner only, not default runtime.
- enabled-state requirement: explicit local Node scripts only.
- real-trigger evidence requirement: source rows path must be the committed 022 `trace/trace_rows.jsonl`.
- hypothesis: the 022 collect-only row can feed the existing OFF_STATIC replay builder and evaluator, producing a
  preflight pass without raw source text and without verdict authority.
- strongest baseline: 022 remains collect-only; a failed preflight means the next step is schema/trace repair, not scoring.
- ablation requirement: none in 023.
- trace/replay requirement: builder output row must include `complete_serialized_state`, `complete_observation`,
  `offline_replay_function_id`, frozen non-LLM D fields, and evaluator preflight report.
- computed-evidence provenance gate: all replay/preflight artifacts must be produced by existing callable Node scripts.
- acceptance gate: builder exits 0, evaluator exits 0, evaluator reports `replay_integrity_preflight_pass_no_verdict`,
  scoring remains unauthorized, selected source raw text is absent from committed 023 artifacts, local checks pass, and
  source-limited review has no blockers.
- claim ceiling: selected-source OFF_STATIC replay preflight only.
- stop condition: raw text in staged artifacts, evaluator authorizes scoring/verdict, missing source-row linkage to 022,
  use of `CREATURE_ON`, baseline/same-access execution, default runtime enablement, program-state/evidence-ledger update,
  push, tag, or remote anchor.
- rollback plan: delete this task package/artifact directory, remove the task-board entry, and regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-selected-source-off-static-replay-preflight-v0/`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_off_static_replay_preflight_v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no source raw text staging;
  - no new downloader/cache writes;
  - no code changes unless an existing callable path is broken and a new task card explicitly narrows that repair;
  - no same-access baseline execution;
  - no scoring, comparison, attribution verdict, or route advancement;
  - no runtime enablement outside explicit offline scripts;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that the accepted 022 selected-source collect-only row can be converted by the existing offline static replay builder
into a preflight row whose evaluator accepts replay integrity while still refusing scoring/verdict authority.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.
