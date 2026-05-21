# Plan

## One Hypothesis

If repeated same-class failures produce candidate-only policy patches and replay them into the next comparable turn, `EgoOperator` can show early feedback-shaped behavior without creating a persistent learning authority.

## Change Surface

- `EgoOperator/agent_base.py`
- `EgoOperator/primitives/subject_context.py`
- `EgoOperator/tests/test_extracted_primitives.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add session-local policy failure counters and candidate storage.
2. Classify repeated provider/tool failure signatures.
3. Emit `PolicyPatchCandidate` after the second same-class failure.
4. Replay matching candidates into `SubjectState v0` on comparable future turns.
5. Record feedback and replay in trace.
6. Add scripted repeated-failure test and run full verification.

## Verification

- `python3 -m py_compile EgoOperator/primitives/subject_context.py EgoOperator/agent_base.py EgoOperator/tests/test_extracted_primitives.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_extracted_primitives.py`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator .codex Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-policy-patch-candidate-replay-loop`
