# Codex GitHub Rate-Limit Wait/Resume v1 PLAN

## Steps

1. Create and verify GitHub Project issue `#83`.
2. Add `github_rate_limit` settings to the project contract.
3. Extend `scripts/github_project_task.py` with bounded rate-limit detection, wait, retry, and structured error metadata.
4. Thread wait metadata through `scripts/codex_project_autopilot.py` outputs.
5. Add deterministic tests for wait, long-wait stop, retry exhaustion, non-rate-limit errors, and closeout verify-stage recovery.
6. Run local verification, then resume the interrupted Epic closeouts for `#48`, `#58`, and `#63` if GitHub quota allows.

## Allowed Paths

- `.codex/project_contract.yaml`
- `scripts/**`
- `scripts/tests/**`
- `docs/codex/tasks/codex-github-rate-limit-wait-resume-v1/**`

## Forbidden Paths

- `EgoOperator/**`
- `legacy/ego-pre-handmade-mainline/**`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`

## Rollback

Revert code/contract/docs/test changes. If a closeout mutation partially succeeded, verify the affected issue before retrying.
