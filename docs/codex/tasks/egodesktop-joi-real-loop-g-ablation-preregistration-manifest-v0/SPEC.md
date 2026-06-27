# EgoDesktop Joi Real-Loop G-ABLATION Preregistration Manifest v0 Spec

- task_id: `EGODESKTOP-GABLATION-011`
- parent_task_id: `EGODESKTOP-GABLATION-010`
- status: `blocked_claude_re_review_synthetic_pack_route_decision_required`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / preregistration design`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_future_experiment_flags_only`
- real_trigger_evidence: `none_for_011_manifest`
- claim_ceiling: `egodesktop_real_loop_g_ablation_preregistration_manifest_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-010` received Claude `NO_BLOCKING_FINDINGS (source-limited)` only at the repaired task-card
layer. It explicitly required a separate preregistration-manifest slice before any `CREATURE_ON` capture, same-access
execution, scoring, comparison, verdict, program-state update, evidence-ledger update, push, tag, or remote anchor.

This slice freezes that manifest for independent review. It does not run the experiment.

## Current Stage / Layer

- current layer: `engineering implementation / preregistration design`
- mainline integration status: `not connected to default EgoDesktop runtime`
- enabled status: `explicit future experiment flags only; no default runtime enablement`
- real trigger evidence: `none for this manifest`
- claim ceiling: `preregistration manifest only`

## Bounded Audit

- real objective: freeze the future comparison design before seeing `CREATURE_ON` heldout outputs.
- strongest baseline explanation: a full-public-history same-access controller may reproduce the output trace from
  public inputs alone.
- strongest invalidity risk: using the historical single-row 009/008 artifacts as if they satisfy future scoring power.
- falsifier for this slice: the manifest lacks frozen prompt packs, equivalence/power design, baseline battery, positive
  controls, or an outcome-blind verdict matrix.
- evidence still insufficient: this manifest, its hashes, and Claude review do not produce any row, score, or verdict.
- mechanism vs resemblance: future task tests bounded output-trace discriminability only.
- hard-coding/leakage check: prompt packs include no expected D labels, target verdicts, heldout answers, or
  creature-state fields.
- weak-baseline check: the manifest requires a full-public-history steelman baseline; omission blocks the run unless an
  accepted low-order Markov upper-bound proof exists before capture.
- claim-inflation check: even a future non-equivalence result remains bounded local attribution candidate evidence only.
- stop condition: any request to capture, score, compare, emit a verdict, or update runtime/program/evidence/remotes
  before Claude accepts this manifest.

## Frozen Files

- `PREREGISTRATION_MANIFEST.json`
- `PREREGISTRATION_MANIFEST.sha256`
- `PROMPT_PACKS.json`
- `PROMPT_PACKS.sha256`

Current frozen hashes:

- preregistration manifest SHA256:
  `25af2cf6644a0c1d4beb37cd3d9dfaae5d9b87d16b90fed0df70d86f4d343b63`
- prompt packs SHA256:
  `cafe9a2336e251c4cd3d4bc0397dde207e3a6ad1d7decb372219dd5f1e9d0199`

Prompt-pack self-check after repair:

- calibration prompts / independent families: `160 / 160`
- heldout prompts / independent families: `160 / 160`
- cross-split exact `user_text_hash` overlap: `0`
- worst cross-split token Jaccard: `0.30434782608695654` against threshold `0.45`
- worst cross-split char-5gram Jaccard: `0.18435754189944134` against threshold `0.25`
- cross-split near-duplicate pairs over either threshold: `0`
- surface-overlap positive control: token `0.5263157894736842`, char-5gram `0.3644067796610169`, triggers as expected
- surface-overlap negative control: token `0.0`, char-5gram `0.0`, passes as expected

## Claude First Review Repair Readback

Claude returned `BLOCKING_FINDINGS` on the first submitted manifest/prompt-pack draft. The repaired v2 boundary
addresses only the preregistration surface:

- B-011-1 repair: prompt packs now use 160 independent prompt families per split, not a 20 family x 8 intent cluster
  structure with aligned calibration/heldout positions.
- B-011-2 repair: the overlap gate is explicitly a surface-template overlap gate, not a semantic embedding-equivalence
  scanner; thresholds are recalibrated so the positive control triggers and the negative control passes.
- B-011-3 repair: the equivalence gate's unit is `independent_prompt_family`; repeated rows per family require
  family-level collapse or block as `blocked_clustered_or_underpowered_equivalence_design`.
- Advisory repair: anti-degeneracy reports and the `adapter_output.expression_name` / `chat_turn.expression_name`
  relationship are predeclared, and any future saturation claim is narrowed to this single expression-name channel and
  distribution.

Claude re-review of this repaired v2 boundary returned `BLOCKING_FINDINGS`. The statistical framework and surface
scanner repairs were accepted at the design layer, but the repaired prompt packs remain invalid as a future capture
basis:

- B-011-4: prompt text leaks split/meta identity through `Calibration`, `Heldout`, `Evaluation`, and `Review split`
  wording and is not credible desktop-chat user text.
- B-011-5: the nominal 160 independent prompt families per split collapse to a small set of repeated sentence
  templates, so family IDs do not establish effective independence.
- B-011-6: all prompts sit in the same low-intensity calm affect band, leaving the manifest ambiguous between
  prompt-affect generalization and internal-state trajectory testing.

No third synthetic prompt-pack repair is authorized in this slice. The next minimal action is a separate docs-only
route-decision card that closes or downgrades the synthetic prompt-pack preregistration path without claiming saturation
or authorizing capture/scoring.

## Live Input Readback

This manifest uses current 009 captured-calibration artifacts as prior evidence only:

- captured calibration reference hash:
  `52411a8378e4a258a03f16b606052d9fcc42650af16c655684db07dc94356067`
- rebuilt 009 `OFF_STATIC_REPLAY_HELDOUT` row path:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/trace/trace_rows.jsonl`
- rebuilt 009 row hash:
  `95722e9c2be9e29a188e759f4490f75bb8518d99e70fd79c41533f5b60345166`
- 009 replay precondition:
  `d_field_replay_precondition_satisfied=true`, `scoring_run_authorized=false`, `verdict_authorized=false`

The older 008 synthetic-reference row under
`artifacts/egodesktop_joi_real_loop_g_ablation_off_static_replay_heldout_v0/` is historical reference only and is not
the frozen 011 scoring basis.

## Manifest Contents

The JSON manifest freezes:

- 160 calibration prompts and 160 heldout prompts, each with one independent prompt family, in `PROMPT_PACKS.json`;
- split protocol and disjointness policy;
- D-field whitelist and metric definitions;
- exact-binomial equivalence/power gate over `independent_prompt_family` with `epsilon=0.05`, `alpha=0.05`,
  minimum independent families `160`, critical mismatch count `3`, computed power `0.9221584908704471` at mismatch
  rate `0.01`, and a cluster guard that blocks underpowered or uncollapsed repeated-family scoring;
- same-access baseline battery, including a required
  `full_public_history_steelman_regularized_multinomial_sequence_model_v0`;
- mechanism-presence, structural leakage, surface-template overlap, renderer-idle, anti-degeneracy, and LLM replay
  controls;
- outcome-blind verdict matrix;
- provenance requirements for every future score, baseline, ablation, leakage scan, replay metric, and verdict.

## Acceptance Gate

This slice is accepted only if:

- manifest and prompt-pack SHA files match current file bytes;
- YAML/JSON parse checks pass;
- route-convergence view generation passes;
- repository fast verification passes;
- Claude returns `NO_BLOCKING_FINDINGS (source-limited)` on the frozen manifest;
- no capture, scoring, comparison, verdict, default runtime enablement, program-state update, evidence-ledger update,
  push, tag, or remote anchor occurs.

## Forbidden Changes

- No `CREATURE_ON` row capture.
- No same-access baseline execution.
- No scoring, comparison, `baseline_saturated_stop`, attribution verdict, or route advancement.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No push, tag, or remote anchor.

## Rollback Plan

Delete `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-preregistration-manifest-v0/`, remove
`EGODESKTOP-GABLATION-011` from `Tasks/TASK_BOARD.yaml`, regenerate route-convergence views, and leave 009/010
artifacts unchanged.

## What This Can Prove

Only that a bounded preregistration manifest exists and is hash-frozen for independent source-limited review.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Preserve the Claude v2 `BLOCKING_FINDINGS`, then draft a separate docs-only route-decision card. Do not repair another
synthetic prompt pack in 011, and do not start capture or scoring in this slice.
