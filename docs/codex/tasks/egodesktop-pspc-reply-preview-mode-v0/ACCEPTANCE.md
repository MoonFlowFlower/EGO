# EgoDesktop PSPC Reply Preview Mode v0 Acceptance

## Acceptance Criteria

- `--pspc-reply-preview-mode` explicitly enables local preview only.
- Normal mode does not send `pspc_reply_preview_context`.
- EgoDesktop chat remains enabled in preview mode.
- Session-local histories map deterministically:
  - gentle history -> `warm_approach`
  - frequent interruption -> `cautious_boundary`
  - late-night care -> `low_interrupt_care`
  - mixed history -> `mixed_low_confidence`
- Valid context is injected only as temporary system context for the desktop turn.
- Invalid context is rejected before runtime handling.
- Preview context and visual scenario contain no executable authority fields.
- No `EgoOperator/agent_base.py`, runtime registry, gate, memory, approval, transport, proactive, or human-trial harness changes.
- Report records status, scenario list, side effects absent, rollback, next allowed step, and claim ceiling.

## Required Tests

- `node --test tests\pspc_reply_preview.test.js`
- `python -m pytest -q tests\test_ego_operator_desktop_pspc_reply_preview.py`
- `npm test`
- `python -m py_compile scripts\ego_operator_desktop_turn.py`
- repo integrity and closeout gates

## What This Proves

It proves a local EgoDesktop user can test PSPC-influenced reply style in an explicit preview mode while no runtime authority is granted.

## What This Does Not Prove

It does not prove PSPC is production-integrated, safe for default runtime integration, beneficial for real users, backed by durable memory, autonomous, conscious, subjectively experiencing, or emotionally real.

## Failure Meaning

Failure means the current preview should be rolled back to perception-only and shadow-only artifacts. It should not be promoted into a gated proposal-hint integration review.
