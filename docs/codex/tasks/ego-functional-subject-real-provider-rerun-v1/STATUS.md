# Status

## Current

`ready`

## Notes

- This task is a local canonical rerun packet for #94 / `EGO-FS-010`.
- It is ready once `OPENROUTER_API_KEY` is present in the local terminal environment.
- The key must not be committed, echoed, or written into task files.
- Current Codex shell preflight reports `OPENROUTER_API_KEY` missing.

## Verification So Far

- Task docs added.
- `python3 scripts/codex_project_autopilot.py local-plan-next` selects `EGO-FS-020` as ready.
- `git diff --check -- Tasks/TASK_BOARD.yaml .codex/project_contract.yaml docs/codex/tasks/ego-functional-subject-real-provider-rerun-v1` -> pass.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 265 tests + diff check.
- Real-provider run is pending environment setup in the operator terminal.
