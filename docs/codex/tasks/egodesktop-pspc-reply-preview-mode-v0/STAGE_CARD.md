# EgoDesktop PSPC Reply Preview Mode v0 Stage Card

## Problem Reframe

The current perception demo is visible but does not affect the local chat reply, so it cannot test whether an operator can feel PSPC history tendencies in a real desktop chat loop.

This stage adds an explicit local-only reply preview mode. It lets EgoDesktop pass a session-local PSPC style hint into the desktop turn script only when `--pspc-reply-preview-mode` is set.

## One Hypothesis

If a session-local PSPC preview profile is injected as temporary system context for one desktop turn, the operator can feel different reply tone, distance, and care tendencies while EgoOperator runtime authority, memory, gate, approval, transport, and proactive paths remain unchanged.

## One Change Surface

- `EgoDesktop/`
- `scripts/ego_operator_desktop_turn.py`
- targeted tests
- this task docs
- `artifacts/egodesktop_pspc_reply_preview_mode_v0/`
- necessary state and evidence ledger entries

## Authority Source

- Repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- EgoOperator core path remains `user text -> LLM understanding -> proposal/plan -> runtime gate -> trace`.
- PSPC authority in this stage is `none`.

## Boundaries

- claim ceiling: `local_reply_preview_only`
- runtime authority: `none`
- enabled: `false`
- mainline_connected: `false`
- adapter_created: `false`
- allowed use: explicit local EgoDesktop reply preview only

## Forbidden

- Do not modify `EgoOperator/agent_base.py`, runtime registry, gate, memory, approval, transport, proactive behavior, or human-trial harness.
- Do not create an adapter.
- Do not write real memory.
- Do not invoke gates or approvals.
- Do not trigger proactive messages.
- Do not add open-ended PSPC chat.
- Do not claim consciousness, subjective experience, real emotion, live autonomy, durable memory, stable user benefit, or production integration safety.

## Three-Level Verify

1. Contract tests prove the preview context is non-executable and flag-gated.
2. Desktop tests prove normal mode omits preview context and preview mode keeps chat enabled.
3. Report artifacts prove four histories map to warm approach, cautious boundary, low-interrupt care, and mixed low confidence with side effects absent.

## Rollback

Delete the preview module, tests, desktop turn script edits, renderer/main wiring, report script, this task directory, `artifacts/egodesktop_pspc_reply_preview_mode_v0/`, and matching state/ledger/generated-view entries.

## What This Can Prove

An explicit local EgoDesktop preview mode can let PSPC session-local style hints affect the current desktop reply style and Live2D presentation without granting runtime authority.

## What This Cannot Prove

This does not prove PSPC production integration, runtime integration safety, adapter readiness, stable real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, or real emotion.
