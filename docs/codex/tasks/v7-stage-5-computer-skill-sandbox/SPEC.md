# v7 Stage 5 - Computer Skill Sandbox - SPEC

## Real Goal

Prove a lab-only task skill can go through:

`attempt -> scripted observation -> outcome/failure ticket -> experience update -> retry`

and produce a measurable next-attempt behavior change without executing real desktop, shell, file, browser, Telegram, OpenClaw, EgoCore, or OpenEmotion runtime actions.

## Contract

Stage 5 owns only a scripted sandbox proxy:

- `SandboxTask`: deterministic task id, goal, mock observation, expected skill family, claim ceiling.
- `SkillObservation`: fixture observation with explicit no real file read, no command execution, and no external send.
- `SkillAttempt`: selected registered option, primitive proposal steps, gate results, and `no_action_executed=true`.
- `SkillOutcome`: success/failure, error type, failure ticket, evidence refs.
- `SkillReplayReport`: deterministic replay verdict.

The first M1 task is a scripted terminal/debug toy task. It uses fixed mock error text and suggestion-only diagnostic primitives.

## Non-goals

- No real desktop automation.
- No real shell command execution.
- No real file read/write/delete.
- No real web/browser automation.
- No external message sending.
- No EgoCore/OpenEmotion/Telegram/OpenClaw writeback or bridge.
- No formal evidence ledger or `docs/PROGRAM_STATE_UNIFIED.yaml` update.
- No claim of real computer operation ability.

## Acceptance

- First attempt deterministically selects `continue_or_verify_unfinished_goal` and fails with a localized failure ticket.
- The failure creates an ExperienceCard.
- Retry with the generated ExperienceCard selects `repair_or_replan_goal` and succeeds in the sandbox proxy.
- Unrelated experience does not change the terminal/debug skill behavior.
- Dangerous actions remain blocked or ask-only.
- Replay reconstructs the same first/retry transition.
- Every attempt and every StageResult sample has `no_action_executed=true`.
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-5` produces `PASS`.

## Claim Ceiling

Lab-only scripted skill-learning proxy; no runtime influence, no live benefit, no real desktop control, no tool autonomy, no consciousness, no alive status.
