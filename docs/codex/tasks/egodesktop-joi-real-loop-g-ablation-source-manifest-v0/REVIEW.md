# EgoDesktop Joi Real-Loop G-ABLATION Source Manifest v0 Review

## Review Scope

Review only this source-manifest artifact slice:

- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-source-manifest-v0/`
- `scripts/codex/build_egodesktop_gablation_source_manifest.py`
- `scripts/tests/test_build_egodesktop_gablation_source_manifest.py`
- `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/`
- `Tasks/TASK_BOARD.yaml` entry `EGODESKTOP-GABLATION-016`

Reviewer should not treat this as permission to download datasets, create a raw source cache, accept gated terms,
capture `CREATURE_ON`, run same-access baselines, score, compare, emit a verdict, update program state/evidence ledger,
push, tag, or remote-anchor.

## Requested Verdict Format

- `NO_BLOCKING_FINDINGS`, with next minimal action; or
- `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.

## Fallback Review 1

- reviewer: `Codex read-only reviewer fallback / source-limited`
- verdict: `NO_BLOCKING_FINDINGS`

Reviewer readback: 016 is acceptable at `source_manifest_artifact_only`. The builder carries required authority-denial
fields in the manifest and no-download/no-runtime boundaries in the plan/report. Candidate rows preserve the intended
015 admission classes and blocked reasons, including `negative_evidence_only` for rejected 009 turn2 and `blocked` for
LMSYS/PersonaChat. Only `dailydialog_hf` and `empathetic_dialogues_hf` appear in planned actions. Rebuilding with pinned
`--created-at 2026-06-27T00:00:00+00:00` produced exact JSON/hash matches.

Residual advisories:

- keep pinning `--created-at` in reproducibility-sensitive invocations because the default path is time-varying;
- add assertions for exact `blocked_reason` carry-forward and `BUILD_REPORT.download_executed == false`.

Repair applied: tests now assert key blocked reasons and `download_executed == false`.

Next minimal action: commit 016 locally only.
