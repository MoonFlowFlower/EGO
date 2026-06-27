# EgoDesktop Joi Real-Loop G-ABLATION Wizard Captured Calibration Reference Replay Preflight v0

- task_id: `EGODESKTOP-GABLATION-028`
- parent_task_id: `EGODESKTOP-GABLATION-027`
- status: `task_card_ready_local`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering planning / captured calibration reference replay preflight card`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `task_card_only_no_artifact_run`
- real_trigger_evidence: `planned_reuse_of_009_calibration_row_and_026_wizard_heldout_row`
- claim_ceiling: `wizard_captured_calibration_reference_replay_card_only`
- auto_remote_anchor: `forbidden`

## Objective

Define the separate calibration/reference slice that may follow 027. The future implementation will rebuild a
Wizard-specific captured calibration reference by consuming the accepted 009 predeclared calibration row and checking it
against the accepted 026 Wizard heldout row, then rebuild the Wizard `OFF_STATIC_REPLAY_HELDOUT` row with that captured
reference and rerun replay preflight. This card does not execute the builders, emit artifacts, score, compare,
attribute, or advance the route.

## Bounded Audit

- real objective: replace the 027 synthetic calibration reference caveat with a Wizard-heldout-specific captured
  calibration reference preflight boundary, without upgrading to scoring or attribution.
- problem-definition check: the wrong task would be to reuse the 009 `calibration_reference.json` as-is. Its partition
  manifest was built against the old 006 heldout row, not the 026 Wizard heldout row.
- strongest baseline explanation: even a captured reference remains a static replay floor; it can improve provenance
  but cannot prove candidate advantage, route failure, or mechanism attribution.
- strongest invalidity reason: the accepted 009 predeclared prompt pack records an older heldout path, so 028 must
  clearly report a new heldout rows path and new partition/reference artifacts for the 026 Wizard row. If that cannot be
  done with current callable scripts, implementation must stop instead of papering over the mismatch.
- falsifier: partition disjointness fails against the 026 Wizard row, calibration/heldout source hashes overlap,
  builder silently uses the old 009 reference without a new 028 partition report, selected raw text appears in staged
  artifacts, evaluator authorizes scoring/verdict, or any report claims `CREATURE_ON`.
- insufficient evidence: a card-only package, a reused 009 hash, a synthetic reference replay pass, or a captured
  reference preflight pass alone remains insufficient for same-access comparison, scoring, route verdict, or mechanism
  attribution.
- mechanism-vs-resemblance: this tests replay/reference provenance only; it does not test a mechanism.
- hard-coding/leakage check: do not include raw calibration or Wizard source text in task docs or committed artifacts;
  use hashes and paths.
- local optimum / Zeno check: if the current script contract cannot make a new Wizard-specific captured reference,
  record a blocker and route to contract repair rather than adding another docs-only reference layer.
- schema split / second logic path check: all future evidence must come from existing callable scripts
  `build-joi-g-ablation-calibration-reference.js`, `build-joi-g-ablation-off-static-replay-heldout.js`, and
  `evaluate-joi-g-ablation-replay.js`; no second builder or hand-written report is authorized in 028.
- claim ceiling: `wizard_captured_calibration_reference_replay_card_only` for this card; future implementation ceiling
  remains `wizard_captured_calibration_reference_replay_preflight_only`.
- minimal validation for this card: route convergence, repo fast verifier, diff check, scoped closeout.
- stop condition: any code/artifact execution in this card-only slice, raw text staging, old 009 reference reuse as a
  Wizard-specific pass, scoring/comparison/verdict, default runtime enablement, program-state/evidence-ledger update,
  push, tag, or remote anchor.
- rollback plan: delete this task package, remove `EGODESKTOP-GABLATION-028` from the task board, and regenerate route
  views.
- acceptance signal: a committed task package and task-board entry that cleanly separates the future captured-reference
  implementation from 027 and preserves all claim ceilings.

## Task Card

- problem definition: 027 proved that the 026 Wizard heldout row can pass `OFF_STATIC_REPLAY_HELDOUT` structure with a
  synthetic reference. A separate task is needed before replacing that synthetic reference with captured calibration
  provenance.
- current stage/layer: `engineering planning / captured calibration reference replay preflight card`.
- mainline target: explicit offline artifact scripts only, not default runtime.
- enabled-state requirement: this card is docs/task-board only; future implementation requires explicit local Node
  commands.
- real-trigger evidence requirement for future implementation:
  - calibration row source must be the accepted 009 predeclared single calibration capture:
    `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl`;
  - heldout row source must be the accepted 026 Wizard desktop chat-turn trace:
    `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl`;
  - future partition/reference output must be 028-specific and must not reuse the old 009 partition as final Wizard
    evidence.
- hypothesis: the accepted 009 calibration row is content/provenance disjoint from the accepted 026 Wizard heldout row,
  so current callable scripts can build a Wizard-specific captured calibration reference and a preflight replay row
  without raw text, scoring, or verdict authority.
- strongest baseline: this remains `OFF_STATIC_REPLAY_HELDOUT`, a static replay baseline component.
- ablation requirement: none in 028.
- trace/replay requirement for future implementation:
  - calibration builder writes `captured_calibration_reference_written`;
  - `selection_policy_status=deterministic_predeclared_single_prompt_consumed`;
  - `post_hoc_selection_status=absent`;
  - `partition_disjointness_status=pass`;
  - `content_disjointness_status=pass`;
  - `provenance_distinctness_status=pass`;
  - `overlap_positive_control_status=pass`;
  - `synthetic_fallback_positive_control_status=pass`;
  - rebuilt replay row reports
    `split_contract_status=captured_calibration_reference_distinct_from_heldout_observation`;
  - evaluator reports `replay_integrity_preflight_pass_no_verdict` and
    `d_field_replay_precondition_satisfied=true`.
- computed-evidence provenance gate: all future evidence must be produced by existing callable Node scripts; no literals,
  static verdict dictionaries, or hand-written scores.
- acceptance gate for this card:
  - docs package exists with SPEC/PLAN/IMPLEMENT/STATUS/MUTATION_SCOPE;
  - task board has `EGODESKTOP-GABLATION-028`;
  - route-convergence generated views include the task as reference-only, not active default;
  - repo fast verifier and diff check pass;
  - no artifact builder is run in this card-only slice.
- future implementation acceptance gate:
  - build a new 028 calibration reference using 009 calibration rows and 026 heldout rows;
  - rebuild Wizard heldout OFF_STATIC with the new 028 calibration reference;
  - evaluate replay preflight with scoring/verdict disabled;
  - raw text scan reports no selected source or calibration utterance leakage;
  - route/repo checks and scoped closeout pass.
- claim ceiling: this card proves only a bounded future implementation plan. A future implementation can prove only
  Wizard captured calibration reference replay preflight, not route success.
- stop condition: raw text staging, old 009 reference passed off as Wizard-specific without a new 028 partition report,
  synthetic reference in the accepted 028 replay row, scoring/verdict authorization, same-access baseline execution,
  `CREATURE_ON`, default runtime enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: delete this task package, remove the 028 task-board entry, regenerate route views.
- expected changed files in this card-only slice:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-wizard-captured-calibration-reference-replay-preflight-v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- expected future implementation artifacts:
  - `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/`
- forbidden changes:
  - no raw text staging;
  - no code changes in this card-only slice;
  - no new capture unless a later task explicitly authorizes it;
  - no same-access baseline execution;
  - no scoring, comparison, attribution verdict, or route advancement;
  - no runtime enablement outside explicit offline scripts;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that the next captured calibration/reference replay preflight slice is properly bounded and separately carded.

## What This Does Not Prove

This does not prove the calibration/reference implementation ran, that captured calibration is valid for the Wizard row,
`CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route advancement, product benefit,
runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness,
alive status, or Bar-2 specialness.

## Authority Refs

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-calibration-reference-v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-wizard-selected-source-chat-smoke-v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-wizard-selected-source-off-static-replay-preflight-v0/`
- `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl`
- `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/PREDECLARED_CALIBRATION_PROMPT_PACK.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl`
