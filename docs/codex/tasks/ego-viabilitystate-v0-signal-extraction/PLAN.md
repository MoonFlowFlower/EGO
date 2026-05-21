# Plan

## One Hypothesis

If `EgoOperator` has deterministic advisory viability signals in the prompt/trace path, later planner and gate slices can rank actions against evidence, risk, resource, initiative, and relationship pressure without creating a second authority.

## Change Surface

- `EgoOperator/primitives/subject_context.py`
- `EgoOperator/primitives/__init__.py`
- `EgoOperator/tests/test_extracted_primitives.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add viability cue extraction and scoring.
2. Render `ViabilityState v0` in subject context and trace.
3. Link viability summary into `SubjectState v0`.
4. Add deterministic high-pressure and low-pressure tests.
5. Run targeted tests and `autopilot_full`.
6. Mark `EGO-FS-004` accepted and activate `EGO-FS-005`.

## Verification

- `python3 -m py_compile EgoOperator/primitives/subject_context.py EgoOperator/primitives/__init__.py EgoOperator/tests/test_extracted_primitives.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_extracted_primitives.py`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator .codex Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-viabilitystate-v0-signal-extraction`
