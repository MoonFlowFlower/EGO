# EgoOperator: Functional Subject Baseline Comparison Harness

## Goal

Add a reproducible baseline-vs-candidate harness that compares EgoOperator Functional Subject candidate mechanisms against a simpler LLM + memory-off + subject-context-off path over the same scripted cases.

## Scope

- Reuse `scripts/run_ego_experience_trial.py` as the existing experience-eval entrypoint.
- Run candidate and baseline passes over the same Functional Subject sample pack.
- Emit JSON and Markdown reports with per-case deltas, trace paths, mechanism traces, and comparison dimensions.
- Keep the report as local/scripted evidence only.

## Non-Goals

- Do not prove stable user benefit, durable memory efficacy, runtime efficacy, live autonomy, independent awareness, or real consciousness.
- Do not modify `EgoOperator` runtime behavior.
- Do not modify `docs/PROGRAM_STATE_UNIFIED.yaml`, `artifacts/evidence_ledger/**`, or legacy projects.
- Do not create a second eval system outside the existing experience trial runner.

## Acceptance Gate

- Harness compares continuity, initiative, learning, emotion, gate correctness, and traceability.
- Reports do not upgrade local/scripted evidence into durable efficacy.
- At least one baseline and one candidate run can be reproduced.
- Existing Autopilot verification profile passes.

## Rollback

Remove the baseline comparison command, helper/report formatter, tests, task docs, contract path entries, and local board status changes.

## Claim Ceiling

`Functional Subject baseline comparison local/scripted candidate pass`.
