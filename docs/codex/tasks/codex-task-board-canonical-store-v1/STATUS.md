# Status

Current milestone: v1 local canonical board and GitHub mirror sync scaffold.

## Decisions

- `Tasks/TASK_BOARD.yaml` is the canonical board.
- GitHub Issues/Projects are mirrors, not task authority.
- Sync logs/outbox are local operational artifacts and ignored by default.

## Verification Log

- `python3 -m py_compile scripts/codex_project_autopilot.py scripts/sync_github_project.py scripts/github_project_task.py scripts/tests/test_codex_project_autopilot.py scripts/tests/test_sync_github_project.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_github_project_task.py scripts/tests/test_codex_project_autopilot.py scripts/tests/test_sync_github_project.py` -> pass (`98 passed`)
- `python3 scripts/codex_project_autopilot.py local-report` -> pass; source=`local_board`, counts=`epic:1 / ready:9 / human_required:5`
- `python3 scripts/codex_project_autopilot.py local-plan-next` -> pass; selected `EGO-FS-001` / GitHub mirror `#85`
- `python3 scripts/codex_project_autopilot.py local-run-loop --dry-run --max-issues 3` -> pass; planned `EGO-FS-001`, `EGO-FS-002`, `EGO-FS-003` without GitHub mutation
- `python3 scripts/sync_github_project.py doctor` -> pass; `task_count=15`, `cached_issue_count=15`
- `python3 scripts/sync_github_project.py plan` -> pass; diff-only mirror plan uses cached issue ids
- `python3 scripts/sync_github_project.py sync --dry-run` -> pass; wrote ignored local outbox/sync log, no GitHub mutation
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass (`237 passed`, diff check pass)

## Closeout Notes

- GitHub Projects/Issues are now treated as mirror/display surfaces for Autopilot planning.
- Canonical task status for Functional Subject #84-#94 and relevant human-gated carryover tasks lives in `Tasks/TASK_BOARD.yaml`.
- No GitHub `sync --execute` was run in this milestone; remote mirror mutation remains a separate explicit operation.
