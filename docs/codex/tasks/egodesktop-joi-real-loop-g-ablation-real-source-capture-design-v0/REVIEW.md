# EgoDesktop Joi Real-Loop G-ABLATION Real Source Capture Design v0 Review

## Review Scope

Claude should review only this docs-only source/capture design:

- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-real-source-capture-design-v0/`
- `Tasks/TASK_BOARD.yaml` entry `EGODESKTOP-GABLATION-014`
- route links from `EGODESKTOP-GABLATION-010` and `EGODESKTOP-GABLATION-013`

Claude should not treat this as permission to download datasets, accept gated terms, create another synthetic prompt
pack, capture `CREATURE_ON`, run same-access baselines, score, compare, emit a verdict, update program state/evidence
ledger, push, tag, or remote-anchor.

## Requested Verdict Format

- `NO_BLOCKING_FINDINGS`, with next minimal action; or
- `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.

## Local Reviewer Notes

- User authorization is recorded, but still bounded by license/provenance gates.
- "Real" is split into source text, desktop trigger, and replayable capture row.
- Existing local data is classified as source/capture-smoke/calibration material, not final heldout `CREATURE_ON`
  evidence.
- Public data candidates are not downloaded in 014.

## Claude Review 1

- reviewer: `desktop Claude / source-limited`
- verdict: `BLOCKING_FINDINGS`

Blocking findings:

- `B-014-1`: license/provenance gate was named but not operationalized. `source_license_tier` was listed as a future
  serialized field, but the meanings of `NC`, `BY`, `SA`, gated access, and unknown-license sources were not defined.
  This is blocking because the EGO repo has companion/product-oriented lanes, and non-commercial source text must not
  later support product/companion claims or broader user-benefit claims.
- `B-014-2`: the card correctly avoids synthetic pack repair, but it did not bind future real-source preregistration to
  the 011 failure gates: split/meta leakage, effective independence beyond unique ids, and affect/causal-path
  anti-degeneracy.

Advisories:

- `A-014-1`: operator-authored source text has demand-characteristic risk. It must be frozen before capture and must not
  contain D labels, expected expression labels, scoring hints, or result prompts.
- `A-014-2`: local/public source text serialized into trace rows becomes evidence artifact content. Future tasks need
  PII/privacy handling such as redaction, exclusion, hash-only storage, or local-only raw text.

Next minimal action from reviewer: only edit the card to add the license rules, B-011 carry-forward gates, and the two
advisories; then resend for source-limited review. Do not download, capture, score, update program state/evidence ledger,
push, tag, remote-anchor, accept gated terms, or upload local data.

## Claude Re-Review Availability

The attempted repaired re-review could not be sent to desktop Claude in this session:

- computer-use MCP activation returned `404` from the configured endpoint;
- Claude CLI returned `403 coding_plan_subscription_expired`.

This is recorded as reviewer-channel unavailable, not as Claude acceptance.

## Fallback Review 2

- reviewer: `Codex read-only reviewer fallback / source-limited`
- verdict: `BLOCKING_FINDINGS`

Blocking finding:

- `B-014-FB-1`: `SPEC.md` listed
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_turn2/selected_calibration_trace_rows.jsonl`
  as ordinary local data. That artifact is the rejected/superseded 009 post-hoc positional-selection attempt, so treating
  it as admissible source/calibration material weakens the provenance boundary.

Reviewer readback: the license/provenance operationalization and B-011 carry-forward gates close the prior Claude
blockers. No second blocker was found.

Required repair: relabel the `calibration_ui_turn2` artifact as blocked/superseded negative evidence only, or remove it
from admitted readback entirely.

Repair applied: `SPEC.md` now labels `calibration_ui_turn2` as blocked/superseded negative evidence only and excludes it
from future source manifests, calibration bases, capture bases, scores, and comparisons.

## Fallback Review 3

- reviewer: `Codex read-only reviewer fallback / source-limited`
- verdict: `NO_BLOCKING_FINDINGS`

Reviewer readback: the prior fallback blocker is repaired. `SPEC.md` keeps `calibration_ui_turn2` only as
blocked/superseded negative evidence, excludes blocked/superseded post-hoc artifacts from future source manifests and
capture/calibration bases, and records the blocker/repair consistently in `STATUS.md`, `REVIEW.md`, and
`Tasks/TASK_BOARD.yaml`.

Residual advisories:

- Keep reviewer-channel wording honest: Claude re-review remained unavailable, so do not rewrite this as Claude
  acceptance.
- Do not let 014 acceptance upgrade into capture, scoring, runtime-effect, or future source-manifest authority for the
  rejected 009 `calibration_ui_turn2` artifact beyond preserved negative evidence.

Next minimal action: commit the scoped 014 docs/task-board package locally only.
