# EgoOperator Functional Subject Post-Native Memory Gate Real-Provider Rerun

## Goal

Run the Functional Subject 20-case trial through the real EgoOperator CLI-compatible entry after EGO-FS-048, then compare transcript-level effects against the previous real-provider and local smoke evidence.

This is a positive mechanism/eval task: it verifies whether native memory/initiative gate strengthening changes observable Functional Subject behavior under a real provider.

## Source

- EGO-FS-048 accepted local candidate evidence.
- `/tmp/ego_fs048_local_trial_smoke_final/functional_subject_trial_report.json`
- Previous real-provider baseline: `/tmp/ego_fs_010_after_fs046_20260523_131112/functional_subject_trial_report.json`

## Stage Card

### Boundary Contract

- Owner: `EgoOperator` trial/eval harness.
- Change surface: task metadata and report/evidence packet only.
- Canonical record: `Tasks/TASK_BOARD.yaml` plus this task evidence file.
- Allowed action: run real-provider scripted trial and GPT-5.5 judge.
- Forbidden action: runtime code changes, memory promotion, program state/evidence ledger update, legacy code changes, GitHub Project mutation.
- Secret handling: read provider key only from local environment or user-authorized local key file; never record the key in task docs, trace, commits, or reports.

### Mainline E2E

`scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5`

The runner uses the same CLI-compatible EgoOperator path used by prior Functional Subject experiments and writes transcript/report artifacts outside the repo.

### Evidence Report

Closeout evidence must record:

- command shape without secrets
- report path
- provider mode and judge status
- response attribution summary after EGO-FS-048
- comparison to EGO-FS-047 where useful
- remaining blocker classes and next ready task, if any

## Acceptance Gate

- Real-provider run completes with a JSON/Markdown report.
- GPT-5.5 judge completes or returns a structured unavailable/partial status.
- Report scorecard distinguishes `native_memory_gate`, `outcome_prediction_gate`, `runtime_repair`, and provider/empty recovery.
- Evidence packet identifies whether EGO-FS-010 can advance or must stay blocked, and routes remaining blockers without overstating claim.

## Not In Scope

- No runtime implementation changes.
- No automatic closeout of EGO-FS-010.
- No durable memory or identity authority change.
- No program state/evidence ledger update.
- No GitHub Project mutation.

## Rollback

Discard the run artifact and keep EGO-FS-010 blocked pending a later rerun.

## Claim Ceiling

`Functional Subject post-native-memory-gate real-provider observation local/scripted candidate pass`
