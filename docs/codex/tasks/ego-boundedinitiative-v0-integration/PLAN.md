# Plan

## One Hypothesis

If initiative is represented as a bounded signal with explicit quiet and approval constraints, `EgoOperator` can become more helpful without creating unapproved background autonomy.

## Change Surface

- `EgoOperator/primitives/initiative.py`
- `EgoOperator/primitives/subject_context.py`
- `EgoOperator/primitives/__init__.py`
- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_extracted_primitives.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add bounded initiative signal derivation.
2. Inject the signal into subject context and trace.
3. Cover authorized reminder, remedial policy replay, continuation, opt-out, and anti-spam.
4. Run targeted and full verification.
5. Mark `EGO-FS-007` accepted and activate `EGO-FS-008`.

## Verification

- `python3 -m py_compile EgoOperator/primitives/initiative.py EgoOperator/primitives/subject_context.py EgoOperator/primitives/__init__.py EgoOperator/agent_base.py EgoOperator/tests/test_extracted_primitives.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_extracted_primitives.py`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator .codex Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-boundedinitiative-v0-integration`
