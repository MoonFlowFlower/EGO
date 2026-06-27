# EgoDesktop Joi Real-Loop G-ABLATION Real Source Capture Design v0 Status

- status: `accepted_local_fallback_reviewed`
- task_id: `EGODESKTOP-GABLATION-014`
- parent_task_id: `EGODESKTOP-GABLATION-013`
- claim_ceiling: `real_source_capture_design_only`
- mainline_connected: `false`
- enabled: `false`
- real_trigger_evidence: `none_for_014_design_card`
- runtime_authority: `none`

## Current Readback

- current branch: `main`
- source HEAD before 014 edits: `a9f8b2b87857bb69cbecf35517976c2158a101b0`
- source worktree before 014 edits: clean
- bootstrap current phase: `legacy_pre_operator_mainline_archived_from_current_tree`
- bootstrap current layer: `transition / operator-first`
- highest evidence level: `E3`
- task-board plan-next before 014: `no_ready_task`
- GitHub sync: unavailable via `gh_not_found`

## Decision

The operator authorization is recorded as permission to design a real-source capture path using:

- existing local EgoDesktop/EgoOperator conversation artifacts as source candidates;
- public, license-compatible, non-gated dialogue datasets as source candidates;
- future capture through the real EgoDesktop chat-turn path and existing G-ABLATION trace writer.

This task does not download datasets, capture rows, run baselines, score, compare, or emit a verdict.

## Evidence Produced

- 014 task card: `SPEC.md`
- 014 plan: `PLAN.md`
- 014 review record: `REVIEW.md`
- 014 mutation scope: `MUTATION_SCOPE.yaml`
- local artifact readback covering smoke trace, calibration trace rows, and session-local conversation context sample
- metadata-only public source checks for DailyDialog, EmpatheticDialogues, LMSYS Chat 1M, and Persona-Chat/ParlAI

## Claude Review Readback

Desktop Claude returned `BLOCKING_FINDINGS` for the first 014 draft:

- `B-014-1`: the license/provenance gate was named but did not operationalize `NC`, `BY`, `SA`,
  `gated_or_terms_required`, or `unknown_or_unclear` source tiers, creating risk that non-commercial source text could
  later be reused in product/companion claims.
- `B-014-2`: the card did not explicitly bind the future real-source preregistration to the three 011 failure gates:
  no split/meta leakage, effective independence beyond unique ids, and causal-path/affect/anti-degeneracy coverage.

Advisories accepted:

- `A-014-1`: operator-authored source text has demand-characteristic risk and must be frozen before capture without D
  labels or result hints.
- `A-014-2`: trace-row source text can become evidence artifact content, so future tasks need PII/privacy
  minimization/redaction rules before serialization.

Repair applied in this draft:

- Added a required license/provenance schema and explicit `source_license_tier` meanings for local private, permissive,
  attribution-required, non-commercial, share-alike, NC+SA, gated/terms-required, and unknown/unclear sources.
- Added a required B-011 carry-forward gate section for no split/meta leakage, effective independence, and causal
  path/affect/anti-degeneracy.
- Added operator-authored demand-characteristic and source-text privacy modes.
- Relabeled the preserved `calibration_ui_turn2` artifact as blocked/superseded 009 negative evidence only. It must not
  enter a future source manifest, calibration basis, capture basis, score, or comparison.

## Fallback Reviewer Readback

Desktop Claude automation was unavailable for the repaired re-review in this session:

- computer-use MCP activation returned `404` from the configured endpoint;
- Claude CLI returned `403 coding_plan_subscription_expired`.

A read-only Codex reviewer fallback returned `BLOCKING_FINDINGS` for one provenance issue: the 014 local-data readback
listed the rejected 009 `calibration_ui_turn2` post-hoc positional-selection artifact as ordinary existing data. The
reviewer found that the license/provenance and B-011 carry-forward repairs closed the prior Claude blockers.

Repair applied: `calibration_ui_turn2` is now labeled as blocked/superseded negative evidence only and excluded from
future source manifests, calibration bases, capture bases, scores, and comparisons.

Fallback re-review returned `NO_BLOCKING_FINDINGS`: the prior provenance blocker is repaired within the review scope,
and no new blocker was found. This is fallback reviewer clearance only, not Claude acceptance.

## Current Claim Ceiling

This can prove only that source/capture semantics are specified and bounded after operator authorization.

## Next Minimal Closed-Loop Action

Commit this 014 package locally only. Then open a separate source-manifest/download-boundary task before any public
dataset download, local source cache creation, desktop capture, scoring, or comparison.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.
