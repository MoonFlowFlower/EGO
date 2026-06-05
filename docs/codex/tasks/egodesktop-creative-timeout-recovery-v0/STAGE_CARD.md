# EgoDesktop Creative Timeout Recovery & Route Isolation v0 Stage Card

## Problem Reframe

EgoDesktop session-local context now preserves same-window chat continuity, but creative/adult route backend timeouts still surface as raw `llm_expression_unavailable: desktop_turn_timeout` text. After such a failure, the next turn has no bounded recovery marker, so short emotional feedback or a redirect to normal story can be interpreted against stale adult-route context.

This stage fixes local desktop timeout recovery and route isolation only.

## One Hypothesis

If EgoDesktop hides raw timeout markers, keeps failed turns out of session transcript, and sends a one-turn `desktop_recovery_context` on the next backend call, users can recover naturally from a local backend timeout without writing memory or making the adult/creative failure sticky.

## Change Surface

- `EgoDesktop/` local main process and recovery helper
- `scripts/ego_operator_desktop_turn.py` desktop bridge validator/injection only
- targeted Node and Python tests
- `docs/codex/tasks/egodesktop-creative-timeout-recovery-v0/`
- `artifacts/egodesktop_creative_timeout_recovery_v0/`
- evidence ledger / generated status views required for closeout

## Authority Source

- Repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- EgoOperator core runtime, gate, memory, approval, transport, proactive behavior, and human-trial harness remain unchanged.
- `desktop_recovery_context` is a local one-turn bridge hint, not a memory source and not a runtime authority source.

## Boundaries

- claim ceiling: `local_desktop_timeout_recovery_only`
- runtime authority: `none`
- persistence: one turn only
- enabled: `false`
- mainline_connected: `false`
- PSPC claim ceilings remain separate

## Forbidden

- Do not modify `EgoOperator/agent_base.py`.
- Do not write real memory.
- Do not invoke gate, approval, transport, proactive behavior, or tools.
- Do not create or register a PSPC adapter.
- Do not treat timeout recovery as adult-fiction capability, PSPC integration, stable user benefit, live autonomy, consciousness, subjective experience, or real emotion.

## Three-Level Verify

1. Node tests prove timeout fallback, one-turn recovery context, no failed-turn session transcript write, and no executable fields.
2. Python tests prove validator rejection, injection order, route-isolation fixture behavior, and no side effects.
3. Artifact report documents the claim ceiling, rollback, failure meaning, and remaining provider/sidecar risk.

## Rollback

Delete the recovery helper, tests, desktop turn script edits, task docs, artifact directory, and matching state/ledger/generated-view entries. The previous session-local context behavior remains otherwise intact.

## What This Proves

This proves EgoDesktop can represent a local backend timeout as bounded one-turn recovery context and avoid raw timeout text or failed-turn transcript pollution.

## What This Does Not Prove

It does not prove adult creative generation capability, provider health, PSPC mainline integration, EgoOperator runtime integration safety, stable real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, or real emotion.
