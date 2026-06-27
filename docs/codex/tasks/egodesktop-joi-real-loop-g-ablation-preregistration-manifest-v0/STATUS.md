# EgoDesktop Joi Real-Loop G-ABLATION Preregistration Manifest v0 Status

- status: `blocked_claude_re_review_synthetic_pack_route_decision_required`
- task_id: `EGODESKTOP-GABLATION-011`
- parent_task_id: `EGODESKTOP-GABLATION-010`
- claim_ceiling: `egodesktop_real_loop_g_ablation_preregistration_manifest_only`
- mainline_connected: `false`
- enabled: `explicit_future_experiment_flags_only`
- real_trigger_evidence: `none_for_011_manifest`
- runtime_authority: `none`

## Current Readback

- current branch: `main`
- source HEAD before 011 edits: `f87379429086bf6227b0bf34d076bd6b14007541`
- source worktree before 011 edits: clean
- bootstrap current phase: `legacy_pre_operator_mainline_archived_from_current_tree`
- bootstrap current layer: `transition / operator-first`
- highest evidence level: `E3`
- GitHub sync: unavailable via `gh_not_found`

## Evidence Produced

- `PREREGISTRATION_MANIFEST.json`
- `PREREGISTRATION_MANIFEST.sha256`
- `PROMPT_PACKS.json`
- `PROMPT_PACKS.sha256`
- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `REVIEW.md`
- `MUTATION_SCOPE.yaml`

Frozen hashes:

- manifest SHA256:
  `25af2cf6644a0c1d4beb37cd3d9dfaae5d9b87d16b90fed0df70d86f4d343b63`
- prompt packs SHA256:
  `cafe9a2336e251c4cd3d4bc0397dde207e3a6ad1d7decb372219dd5f1e9d0199`

## Self-Review Repair

The first generated prompt pack failed its own overlap thresholds under local self-check (`tokenBlock=380`,
`gramBlock=385`). Claude then returned `BLOCKING_FINDINGS` on the first submitted manifest/prompt-pack draft:

- B-011-1: heldout prompts were calibration template/position clones rather than a meaningful generalization split.
- B-011-2: the near-duplicate gate mixed a surface Jaccard scanner with a semantic-duplicate claim, and its positive
  control did not trigger under the original thresholds.
- B-011-3: the row-level binomial design ignored the 20 family x 8 intent cluster structure.

The repaired v2 boundary keeps the same no-capture/no-scoring authority boundary and changes only the manifest/prompt
design:

- calibration prompts: `160`
- heldout prompts: `160`
- calibration independent prompt families: `160`
- heldout independent prompt families: `160`
- exact cross-split `user_text_hash` overlap: `0`
- worst cross-split token Jaccard: `0.30434782608695654` against threshold `0.45`
- worst cross-split char-5gram Jaccard: `0.18435754189944134` against threshold `0.25`
- threshold-violating cross-split pairs: `0`
- surface-overlap positive control: token `0.5263157894736842`, char-5gram `0.3644067796610169`, triggers
- surface-overlap negative control: token `0.0`, char-5gram `0.0`, passes
- equivalence unit: `independent_prompt_family`
- cluster guard: repeated rows per family require family-level collapse or block as
  `blocked_clustered_or_underpowered_equivalence_design`
- anti-degeneracy guard: near-constant expression channel blocks as `blocked_degenerate_expression_channel`
- scored D channel: `adapter_output.expression_name`; `chat_turn.expression_name` is a consistency check, not a second
  independent scored channel

The manifest freezes a future design only. No row capture, same-access execution, scoring, comparison, verdict,
program-state update, evidence-ledger update, push, tag, or remote anchor has been performed.

## Current Claim Ceiling

This can prove only that a preregistration manifest exists and has local file hashes ready for independent
source-limited review.

## Current Blocker

Independent Claude source-limited re-review returned `BLOCKING_FINDINGS` on the repaired v2 boundary:

- B-011-4: prompt text leaks split/meta identity and is not credible desktop-chat user text.
- B-011-5: nominal independent families collapse to a small set of repeated sentence templates, so effective
  independence remains unproven.
- B-011-6: the prompt set is one narrow calm affect band, leaving the tested causal path ambiguous.

This blocks 011 acceptance. It does not prove same-access saturation, `CREATURE_ON` redundancy, or route closure.

## Next Minimal Closed-Loop Action

Draft a separate docs-only route-decision card that records no further synthetic prompt-pack repair in this lane. Do not
capture, score, compare, emit a verdict, update program state/evidence ledger, push, tag, or remote-anchor.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.
