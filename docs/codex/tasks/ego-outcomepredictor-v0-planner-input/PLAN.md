# Plan

## One Hypothesis

If current viability and subject signals are scored into reversible action outcomes, `EgoOperator` can avoid premature direct replies in ambiguous/high-uncertainty fallback paths while preserving the main LLM/gate architecture.

## Change Surface

- `EgoOperator/primitives/subject_context.py`
- `EgoOperator/primitives/__init__.py`
- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_extracted_primitives.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add outcome option scoring and selected prediction.
2. Add prompt and trace visibility.
3. Pass structured outcome predictions into fallback planner.
4. Record prediction effect in trace when it changes action choice.
5. Add deterministic baseline-vs-candidate test.
6. Run targeted and full verification.

## Verification

- `python3 -m py_compile EgoOperator/primitives/subject_context.py EgoOperator/primitives/__init__.py EgoOperator/agent_base.py EgoOperator/tests/test_extracted_primitives.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_extracted_primitives.py`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator .codex Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-outcomepredictor-v0-planner-input`
