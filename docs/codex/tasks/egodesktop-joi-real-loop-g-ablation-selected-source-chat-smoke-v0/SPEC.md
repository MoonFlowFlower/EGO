# EgoDesktop Joi Real-Loop G-ABLATION Selected Source Chat Smoke v0

- task_id: `EGODESKTOP-GABLATION-022`
- parent_task_id: `EGODESKTOP-GABLATION-021`
- status: `active`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering validation / selected source desktop trigger smoke`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_smoke_flags_only`
- real_trigger_evidence: `valid_direct_node_smoke_trace_hash_match`
- claim_ceiling: `selected_source_desktop_trigger_smoke_only`
- auto_remote_anchor: `forbidden`

## Objective

Run one explicit EgoDesktop smoke using one userText materialized from a 021 selected source row, through the real
`window.egoDesktop.sendChatTurn(...)` path and existing trace writer. Preserve only hash/provenance reports and trace
artifacts; do not score, compare, or claim `CREATURE_ON`.

## Task Card

- problem definition: connect a selected public source row to the real desktop chat-turn trigger without promoting it to
  mechanism evidence.
- current stage/layer: `engineering validation / selected source desktop trigger smoke`.
- mainline target: explicit local Electron smoke only, not default runtime.
- enabled-state requirement: explicit smoke flags only.
- real-trigger evidence requirement: renderer smoke report must show `joiRealLoopChatSmoke.status=chat_turn_trace_smoke_pass`;
  trace row count must be positive; trace row `public_inputs.user_text_hash` must match the trigger input report.
- hypothesis: an ignored raw-cache source row can be materialized into userText and routed through the existing
  EgoDesktop chat-turn seam while preserving hash-only committed provenance.
- strongest baseline: current shim/backend behavior; this run has no same-access comparison.
- ablation requirement: none in 022.
- trace/replay requirement: existing `joiRealLoopGAblationTraceRunner` must write `trace_rows.jsonl`.
- computed-evidence provenance gate: trigger input report is produced by
  `scripts/codex/materialize_egodesktop_selected_source_trigger_input.py`, and trace row hash is produced by the
  existing EgoDesktop trace writer.
- acceptance gate: smoke exits successfully, trace row hash aligns with source-trigger hash, local checks pass, and
  source-limited review no blockers.
- claim ceiling: selected source desktop trigger smoke only.
- stop condition: smoke failure, trace row absent, hash mismatch, raw text committed, scoring/comparison attempt,
  runtime enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: delete 022 docs/artifacts/task-board entry and regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-selected-source-chat-smoke-v0/`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_chat_smoke_v0/`
  - `scripts/codex/materialize_egodesktop_selected_source_trigger_input.py`
  - `scripts/tests/test_materialize_egodesktop_selected_source_trigger_input.py`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no raw text staging;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no runtime enablement outside explicit smoke flags;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that one selected source row can be materialized into userText, sent through the real EgoDesktop chat-turn smoke
path, and serialized by the existing trace writer with matching source-trigger hash provenance.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, replay validity, D-provenance sufficiency, same-access saturation, baseline
score, candidate attribution, route advancement, product benefit, runtime integration safety, stable user benefit,
durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.
