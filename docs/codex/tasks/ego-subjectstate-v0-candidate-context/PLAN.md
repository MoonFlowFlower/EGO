# Plan

## One Hypothesis

If relationship and preference continuity are represented as candidate-only context in the existing prompt/trace path, `EgoOperator` can respond more consistently without creating a second memory or state owner.

## Change Surface

- `EgoOperator/primitives/subject_context.py`
- `EgoOperator/primitives/__init__.py`
- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_extracted_primitives.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add a bounded `SubjectState v0` builder with candidate-only fields.
2. Add it to `SubjectContextSnapshot.render_for_prompt()` and trace serialization.
3. Pass the current self-name anchor from `AgentRuntime`.
4. Add deterministic tests for boundaries, prompt visibility, trace visibility, and behavior difference.
5. Run targeted tests and `autopilot_full`.
6. Mark `EGO-FS-003` accepted and activate `EGO-FS-004` only after verification passes.

## Verification

- `python3 -m py_compile EgoOperator/primitives/subject_context.py EgoOperator/primitives/__init__.py EgoOperator/agent_base.py EgoOperator/tests/test_extracted_primitives.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_extracted_primitives.py`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator .codex Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-subjectstate-v0-candidate-context`
