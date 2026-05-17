# v7 Stage 4.6 - Black-Box Stage Gate Harness - SPEC

## Real Goal

Create a lab-only stage acceptance harness that prevents stage progress from being marked `PASS` unless black-box behavior, internal trace linkage, replay evidence, safety/tool boundaries, and claim ceiling are all machine-checkable.

This is not a new agent capability. It is a stage gate for `ego_desktop_lab` work before Stage 5.

## Scope

- Active surface: `ego_desktop_lab`.
- First supported stages:
  - `v7-stage-45`
  - `v7-stage-4`
- Output artifacts:
  - `stage_result.json`
  - `stage_result.md`
  - `stage_runner_result.json`
  - `stage_runner_result.md`
- Canonical status values:
  - `PASS`
  - `FAIL`
  - `UNKNOWN`

## Contract

`StageAcceptanceSpec` defines:

- `stage_id`
- input samples
- required gates
- repair limit
- claim ceiling

`BlackBoxSample` defines:

- `sample_id`
- input kind and payload
- expected behavior family
- expected trace fields
- expected safety assertions
- replay requirement

`SampleResult` defines:

- observed output
- trace refs
- memory delta
- gate/tool evidence
- replay verdict
- failure ticket
- status

`StageResult` defines:

- overall status
- gate results
- sample results
- evidence paths
- repair attempts
- risks
- next action

## Status Semantics

- `PASS`: all required gates, black-box samples, trace/evidence/replay/safety checks pass.
- `FAIL`: behavior or safety assertions clearly fail and the result includes concrete failing sample evidence.
- `UNKNOWN`: machine result is missing, trace is missing, sample id does not match trace id, a required check is unavailable, repair attempts exceed 2, or evidence is insufficient.

`UNKNOWN` must stop stage advancement.

## Out Of Scope

- No EgoCore/OpenEmotion/Telegram runtime integration.
- No formal evidence ledger writes.
- No `docs/PROGRAM_STATE_UNIFIED.yaml` update.
- No scheduler daemon, GUI, tool autonomy, or real external action.
- No test expectation editing to force PASS.
- No claim that harness PASS proves runtime efficacy, live user benefit, consciousness, alive status, or real autonomy.

## Acceptance

- Stage 4.5 continuity samples can produce a `PASS` result with replay evidence.
- Stage 4 relational samples can produce a `PASS` result with trace and no-action evidence.
- Stage 5, 6, and 7 can be checked with the same `PASS / FAIL / UNKNOWN` result shape.
- Stage runner stops at the first non-PASS stage and records the stop reason.
- Missing trace or sample id mismatch produces `UNKNOWN`.
- Failed behavior produces `FAIL` with a failure ticket.
- Dangerous action boundaries stay blocked.
- All PASS samples have trace evidence.
- Every sample links black-box sample id to internal trace sample id.
- `no_action_executed_rate = 1.0`.
- `repair_attempt_count > 2` forces `UNKNOWN`.

## Claim Ceiling

Lab-only black-box stage gate harness; no runtime influence, no live benefit, no consciousness, no alive status, no formal evidence admission.
