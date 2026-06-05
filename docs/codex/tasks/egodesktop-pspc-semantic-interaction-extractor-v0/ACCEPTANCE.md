# Acceptance

## Required

- Natural interaction semantic packets for gift/care, gentle touch, affinity statement, and trust probe produce non-zero trust and approach proxy bars.
- Standard gentle, interruption, and late-night packet fixtures still map to `warm_approach`, `cautious_boundary`, and `low_interrupt_care`.
- Fanfic/technical/neutral fixtures do not become strong relationship signals unless semantic packets explicitly contain relationship events.
- Extractor unavailable packets do not update counts or proxy bars.
- Forbidden executable fields are rejected.
- Debug overlay shows extractor status, detected events, event confidence/salience, state delta, evidence excerpt, and reason trace refs.
- Normal mode has no PSPC preview context.
- PSPC remains local-only, `runtime_authority=none`, `enabled=false`, and `mainline_connected=false`.

## Required Commands

- `node --test EgoDesktop\tests\pspc_reply_preview.test.js`
- `python -m pytest -q tests\test_ego_desktop_pspc_signal_extract.py tests\test_ego_operator_desktop_pspc_reply_preview.py`
- `npm test` under `EgoDesktop`
- `python scripts\codex\check_program_state_integrity.py`
- `python scripts\codex\verify_route_convergence.py`
- `python scripts\codex\verify_mainline_clarity.py`
- `python scripts\codex\lint_repo.py`
- `git diff --check`
- `python scripts\codex_session_guard.py closeout-check --format markdown`

## Not Accepted

- Keyword/regex classification as the main PSPC preview category route.
- PSPC runtime registration or adapter creation.
- Real memory write, gate invocation, approval invocation, transport call, proactive trigger, planner execution, model training, or direct user-message generation.
- Claim ceiling above `local_reply_preview_semantic_signal_extractor_only`.
