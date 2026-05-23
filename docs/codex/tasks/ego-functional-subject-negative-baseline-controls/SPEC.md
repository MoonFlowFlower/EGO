# EgoOperator Functional Subject Negative Baseline Controls

## Goal

Make the Functional Subject baseline comparison a cleaner negative control by disabling native memory gate behavior in the baseline run and surfacing candidate-vs-baseline response attribution summaries.

This is a positive evidence mechanism: quantify what the Functional Subject candidate path adds beyond a plainer LLM/tools path without silently sharing candidate-only runtime gates.

## Source

- EGO-FS-049 GPT-5.5 judge partial verdict.
- Follow-up issue: add baseline comparison traces so beyond-baseline claims are quantified rather than inferred.
- EGO-FS-050 direct trace evidence packet.

## Stage Card

### Boundary Contract

- Owner: Functional Subject eval harness.
- Change surface: `scripts/run_ego_experience_trial.py`, tests, task docs/board.
- Allowed mutation: baseline comparison configuration and report fields.
- Forbidden mutation: EgoOperator runtime behavior, memory authority, program state, evidence ledger, legacy code, GitHub Project.

### Mainline E2E

`run_functional_subject_baseline_comparison -> candidate run with subject context/native gate -> baseline run with memory off, subject context off, native memory gate off -> comparison report`

The report must expose candidate and baseline scorecards separately.

### Evidence Report

Closeout evidence must record:

- candidate/baseline configuration flags
- candidate/baseline response attribution summaries
- per-case delta notes
- proof that baseline native memory gate is disabled
- verification commands

## Acceptance Gate

- Baseline comparison disables native memory gate in the baseline run.
- Report includes candidate and baseline response attribution summaries.
- Report includes a compact comparison summary with clean first-pass counts, repair counts, and mechanism-trace counts.
- Existing baseline comparison tests assert these fields.
- Autopilot regression profile does not regress.

## Not In Scope

- No real-provider comparison run in this task.
- No GPT judge integration for comparison in this task.
- No runtime behavior change.
- No program state/evidence ledger update.

## Rollback

Remove the baseline native-gate disable flag and comparison summary fields.

## Claim Ceiling

`Functional Subject negative baseline control local workflow pass`
