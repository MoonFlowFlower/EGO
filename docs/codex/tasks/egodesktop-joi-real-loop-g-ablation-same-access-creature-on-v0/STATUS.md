# EgoDesktop Joi Real-Loop G-ABLATION Same-Access + CREATURE_ON v0 Status

- status: `card_repaired_claude_no_blocking__preregistration_manifest_next`
- task_id: `EGODESKTOP-GABLATION-010`
- claim_ceiling: `egodesktop_real_loop_g_ablation_same_access_creature_on_task_card_only`
- mainline_connected: `false`
- enabled: `explicit_experiment_flags_only_future_task`
- real_trigger_evidence: `none_for_010_card`
- runtime_authority: `none`

## Current Objective

Create a bounded task card for the future decisive `SAME_ACCESS_REPRODUCER_BATTERY + CREATURE_ON` comparison. This is
card/review work only.

## Current Readback

- Current branch at drafting: `main`.
- Current live HEAD at drafting: `7bb85e96cc24e37d71cc2f4f79b5cf4aedf4937b`.
- Worktree at drafting: clean before edits.
- `EGODESKTOP-GABLATION-009` accepted locally with:
  - captured calibration reference hash `52411a8378e4a258a03f16b606052d9fcc42650af16c655684db07dc94356067`;
  - rebuilt `OFF_STATIC_REPLAY_HELDOUT` row hash
    `95722e9c2be9e29a188e759f4490f75bb8518d99e70fd79c41533f5b60345166`;
  - `d_field_replay_precondition_satisfied=true`;
  - `scoring_run_authorized=false`.
- Bootstrap still reports program state as `legacy_pre_operator_mainline_archived_from_current_tree` /
  `transition / operator-first`, highest evidence `E3`, and GitHub sync unavailable via `gh_not_found`.

## Evidence Produced

- 010 task card: `SPEC.md`
- 010 plan: `PLAN.md`
- 010 mutation scope: `MUTATION_SCOPE.yaml`
- 010 task-board entry in `Tasks/TASK_BOARD.yaml`
- Claude source-limited review record: `REVIEW.md`
- Card repairs now require:
  - pre-capture preregistration manifest with hash-frozen thresholds, prompt packs, baseline battery, epsilon, power,
    minimum n, and verdict matrix;
  - TOST or equivalent equivalence rule with `MDE <= epsilon` before any `baseline_saturated_stop` claim;
  - high-capacity full-public-history steelman baseline or computed low-order Markov upper-bound proof;
  - mechanism-presence positive control;
  - semantic near-duplicate leakage scanner with positive control;
  - explicit clarification that independent means independent callable path, not independent authorship.

No row capture, scoring, comparison, verdict, program-state update, evidence-ledger update, push, tag, or remote anchor
has been performed.

## Claude Review Readback

Desktop Claude returned `BLOCKING_FINDINGS` source-limited for the first card draft:

- `B1`: `baseline_saturated_stop` lacked equivalence boundary, power, minimum sample size, and TOST/equivalent rule.
- `B2`: same-access battery was capped at low-capacity/short-context baselines and needed a full-public-history steelman
  or a computed low-order Markov justification.
- `B3`: threshold/pack/battery/epsilon/min-n freezing needed a separate hash-frozen preregistration review gate before
  any `CREATURE_ON` capture or scoring.

The card was repaired and sent back to desktop Claude. Claude returned `NO_BLOCKING_FINDINGS (source-limited)` for the
repaired card/design only:

- B1 equivalence/power gate accepted as real gating text.
- B2 full-public-history steelman / low-order Markov proof requirement accepted.
- B3 preregistration review gate accepted.
- A1-A4 repairs accepted.
- Task-board status remains `active`, docs-contract/E3/card-only; no implementation is authorized.

Claude's next minimal action: open only a separate preregistration-manifest slice that freezes epsilon, power, MDE,
minimum n, prompt packs, baseline battery, verdict matrix, and hashes, then send that manifest for independent
source-limited review. Do not capture `CREATURE_ON`, score, compare, emit verdict, update program state/evidence ledger,
push, tag, or remote-anchor.

## What This Can Prove

Only that a bounded card exists for a future same-access + `CREATURE_ON` comparison.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Open only a separate preregistration-manifest slice. Do not capture or score `CREATURE_ON` until the frozen manifest
also receives independent source-limited review.
