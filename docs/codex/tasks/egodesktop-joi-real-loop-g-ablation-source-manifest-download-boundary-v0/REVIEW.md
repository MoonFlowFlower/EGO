# EgoDesktop Joi Real-Loop G-ABLATION Source Manifest Download Boundary v0 Review

## Review Scope

Review only this docs-only source-manifest/download-boundary design:

- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-source-manifest-download-boundary-v0/`
- `Tasks/TASK_BOARD.yaml` entry `EGODESKTOP-GABLATION-015`
- route link from `EGODESKTOP-GABLATION-014`

Reviewer should not treat this as permission to download datasets, create a source cache, accept gated terms, capture
`CREATURE_ON`, run same-access baselines, score, compare, emit a verdict, update program state/evidence ledger, push,
tag, or remote-anchor.

## Requested Verdict Format

- `NO_BLOCKING_FINDINGS`, with next minimal action; or
- `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.

## Local Reviewer Notes

- 015 is a boundary card only.
- It preserves 014's separation between real source text, real desktop trigger, and replayable capture row.
- It classifies candidate sources before any download.
- It blocks gated, unknown-license, local-private-without-privacy-mode, and negative-evidence-only sources.
- It does not implement `SOURCE_MANIFEST.json` or a source cache.

## Fallback Review 1

- reviewer: `Codex read-only reviewer fallback / source-limited`
- verdict: `NO_BLOCKING_FINDINGS`

Reviewer readback: 015 stays on the intended docs-only boundary. It forbids download, cache creation, gated access,
capture, scoring, verdicts, program-state/evidence-ledger mutation, and remotes; it classifies candidate sources into
metadata-only, conditional-download, blocked, and negative-evidence-only; and it preserves the license/privacy/raw-cache
and B-011 gates.

Residual advisory accepted: manifest-level required fields denied capture/scoring/product-claim authority, while runtime,
program-state, evidence-ledger, and remote authority denials were only enforced at task/plan/scope level. `SPEC.md` now
adds `no_runtime_authority`, `no_program_state_authority`, `no_evidence_ledger_authority`, and `no_remote_authority` as
required manifest-level fields.

Next minimal action: commit the scoped 015 docs/task-board package locally only.
