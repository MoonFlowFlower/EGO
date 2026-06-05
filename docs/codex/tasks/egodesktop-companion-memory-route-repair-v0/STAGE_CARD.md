# EgoDesktop Companion Memory Wording + Route Misfire Repair v0

## Problem Reframe

PSPC preview signal is now observable and active in EgoDesktop, but the visible companion experience is still interrupted by two non-PSPC defects:

- session-local recall and memory-boundary replies can expose engineering policy wording such as candidate-local/operator-memory/project-state language;
- timeout recovery can describe ordinary affectionate interaction failures as a creative-route timeout.

This stage treats those as EgoDesktop companion-visible reply contract defects, not as PSPC mechanism failures.

## One Hypothesis

If EgoDesktop translates local session/memory boundary output into companion-visible wording and keeps timeout recovery route-neutral unless the failed turn was explicitly creative/adult creative, then the same PSPC warm-approach state will be perceptible without policy wording or route-misfire interruptions.

## One Change Surface

- `scripts/ego_operator_desktop_turn.py` may add desktop-only visible reply rewriting for session-local recall wording.
- `EgoDesktop/src/desktopRecoveryContext.js` may refine local timeout recovery classification and fallback wording.
- Tests, local docs, artifacts, project contract, task board, program state, evidence ledger, and generated views may be updated as required.

## Authority Source

- Current repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- The default runtime owner remains `EgoOperator/`.
- This stage is EgoDesktop local presentation/recovery behavior only.

## Boundaries

- Do not modify EgoOperator core memory store, runtime gate, approval flow, transport, proactive behavior, human-trial harness, or runtime registry.
- Do not create or register a PSPC adapter.
- Do not write real memory.
- Do not let PSPC gain runtime authority.
- Do not raise repo-wide claim ceiling.

## Three-Level Verify

1. Contract tests: desktop reply/recovery context rejects authority escalation and executable fields.
2. Fixture tests: recent user-visible logs no longer expose engineering policy wording or creative-route timeout misfires.
3. Repo gates: EgoDesktop tests, targeted Python tests, route/program/mainline checks, lint, diff check, closeout-check.

## Rollback

Delete this task package, companion repair artifacts, companion-specific tests, and revert this task's changes to `scripts/ego_operator_desktop_turn.py`, `EgoDesktop/src/desktopRecoveryContext.js`, `Tasks/TASK_BOARD.yaml`, `.codex/project_contract.yaml`, program-state/evidence-ledger/generated views.

## Claim Ceiling

`local_desktop_companion_wording_and_route_repair_only`

This cannot prove PSPC mainline integration, true learning, durable memory, runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.
