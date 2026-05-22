# Plan

## One Hypothesis

If subject-state mutation is represented as explicit proposal and decision records, later memory or relationship promotion can be audited without letting LLM output directly mutate canonical state.

## Change Surface

- `EgoOperator/primitives/subject_context.py`
- `EgoOperator/primitives/__init__.py`
- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_extracted_primitives.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add proposal and decision record builders.
2. Add runtime storage for pending candidate mutation proposals.
3. Block `source=llm_output`.
4. Write audit trace rows for explicit decisions.
5. Add deterministic tests.
6. Run targeted and full verification.

## Verification

- `python3 -m py_compile EgoOperator/primitives/subject_context.py EgoOperator/primitives/__init__.py EgoOperator/agent_base.py EgoOperator/tests/test_extracted_primitives.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_extracted_primitives.py`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator .codex Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-subject-state-mutation-gate-audit-trace`
