# Status

## Current Milestone

`EGO-FS-006` local/scripted implementation and verification.

## Decisions

- Policy patches are session-local candidates.
- Repeated same-class failures use a threshold of two observations before candidate emission.
- Replay is prompt/trace context only and does not promote persistent learning.

## Evidence

- `python3 -m py_compile EgoOperator/primitives/subject_context.py EgoOperator/agent_base.py EgoOperator/tests/test_extracted_primitives.py` passed.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_extracted_primitives.py` passed with 30 tests.
- Scripted repeated 429 failure emits a `PolicyPatchCandidate`, then a later 429 turn replays it and changes the fake LLM strategy.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` passed: 250 tests plus scoped diff check.

## Risks

- Future persistent policy learning must go through a mutation gate and audit trace before becoming canonical.

## Next Step

Continue to `EGO-FS-007`.
