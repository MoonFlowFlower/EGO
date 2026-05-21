# Status

Current milestone: architecture contract v0.

## Decisions

- Functional Subject v0 is a candidate context and proposal layer, not a new canonical state authority.
- `EgoOperator` remains the implementation owner for runtime gate, approval, trace, and CLI entry behavior.
- LLMs can understand, propose, plan, and express; they cannot directly mutate identity, memory, relationship, policy, program state, evidence, or tool side effects.
- Later implementation tasks must prove a mechanism changes planning/gating/trace behavior, not only that text summaries exist.

## Verification Log

- `python3 -m py_compile scripts/tests/test_functional_subject_contract.py scripts/codex_project_autopilot.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_functional_subject_contract.py scripts/tests/test_codex_project_autopilot.py` -> pass (`83 passed`)
- `python3 scripts/codex_project_autopilot.py local-plan-next` -> pass; after accepting `EGO-FS-001`, next selected task is `EGO-FS-002`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass (`241 passed`, diff check pass)

## Closeout Notes

- `EGO-FS-001` is accepted in `Tasks/TASK_BOARD.yaml`.
- `EGO-FS-002` is now the active local-board task.
- No runtime behavior was changed; this task only defines the architecture contract and deterministic contract guard.
