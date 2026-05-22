# Status

## Current

`accepted_local`

## Notes

- This task repairs `EGO-FS-015`.
- It does not change memory authority, program state, evidence ledger, or legacy code.

## Completed

- Added a prompt contract for ambiguous selfhood goals.
- Added a bounded output repair guard for clarification-only replies.
- Added deterministic fake-LLM coverage.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py -q` -> pass
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 259 tests + diff check
