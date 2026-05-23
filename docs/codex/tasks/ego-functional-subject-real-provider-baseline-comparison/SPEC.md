# EgoOperator Functional Subject Real-Provider Baseline Comparison

## Goal

Run the cleaned candidate-vs-baseline Functional Subject comparison through the real provider so beyond-baseline evidence is measured on the same external model path used by operator trials.

This is a positive eval task: compare candidate mechanisms against a baseline where operator memory, SubjectContext, and native memory gate are disabled.

## Source

- EGO-FS-051 local negative baseline controls.
- EGO-FS-049 GPT-5.5 judge request for baseline comparison traces.

## Stage Card

### Boundary Contract

- Owner: Functional Subject eval harness.
- Change surface: task metadata and report/evidence packet only.
- Allowed action: run real-provider candidate-vs-baseline comparison.
- Forbidden action: runtime code changes, memory authority change, program state/evidence ledger update, legacy code changes, GitHub Project mutation.
- Secret handling: read provider key only from local environment or user-authorized local key file; never record the key.

### Mainline E2E

`scripts/run_ego_experience_trial.py --functional-subject-baseline-comparison --case-limit 20`

The candidate run keeps Functional Subject mechanisms enabled. The baseline run disables operator memory, SubjectContext, and native memory gate.

### Evidence Report

Closeout evidence must record:

- report path
- candidate/baseline configuration flags
- candidate/baseline response attribution summaries
- comparison summary
- whether this changes EGO-FS-010 status or only adds evidence

## Acceptance Gate

- Real-provider comparison completes with JSON/Markdown report.
- Candidate and baseline runs both use `provider_mode=openrouter`.
- Baseline native memory gate is disabled.
- Comparison summary is recorded.
- EGO-FS-010 status is not upgraded unless separate judge/human gates allow it.

## Not In Scope

- No GPT-5.5 judge integration in this task.
- No runtime implementation change.
- No program state/evidence ledger update.
- No GitHub Project mutation.

## Rollback

Discard the run artifact and keep EGO-FS-010 blocked.

## Claim Ceiling

`Functional Subject real-provider baseline comparison observation candidate pass`
