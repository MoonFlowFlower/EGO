# Codex Autopilot L2 Dirty Baseline STATUS

## Current State

- state: `local_workflow_pass_pending_publish`
- github_issue: `#18`
- claim_ceiling: `Codex autopilot L2 scoped single-issue local candidate pass`

## Decisions

- Dirty baseline is local operational state, not repo authority.
- Dirty baseline defaults to tracked dirty state (`git status --short -uno`) to avoid expanding large untracked runtime/artifact noise; automatic write-capable L2 still needs a later allowed-path untracked scan before staging.
- L2 remains dry-run/control-plane only in this slice.
- #14 must be normalized before any autopilot execution.

## Verification Log

- #17 was closed as `Done`; #18 was created and set `In Progress`.
- Added local baseline support under `.codex/autopilot/`.
- Added `baseline`, `diff-scope`, `run-once --dry-run`, and `normalize-issue --dry-run`.
- Added tests for baseline capture, unchanged pre-existing dirty state, new scoped and unsafe changes, changed pre-existing unsafe state, normalize-issue output, and run-once refusal for non-ready classes.
- Verification passed:
  - `python3 scripts/github_project_task.py verify --issue 17 --expect-status Done`
  - `python3 scripts/github_project_task.py verify --issue 18 --expect-status "In Progress"`
  - `python3 scripts/codex_project_autopilot.py baseline` recorded 52 tracked dirty entries without full untracked expansion.
  - `python3 scripts/codex_project_autopilot.py diff-scope` reported 52 unchanged pre-existing entries, 0 scoped changes, and 0 unsafe changes.
  - `python3 scripts/codex_project_autopilot.py run-loop --dry-run --max-issues 3 --max-minutes 10` planned #18 and did not stop on old dirty noise.
  - `python3 scripts/codex_project_autopilot.py normalize-issue --issue 14 --dry-run` produced a canonical issue body proposal.
  - `python3 scripts/codex_project_autopilot.py run-once --issue 14 --dry-run` refused #14 as `unknown`.
  - `python3 scripts/codex_project_autopilot.py run-once --issue 18 --dry-run` planned a scoped dry-run implementation path.
  - `python3 -m py_compile scripts/codex_project_autopilot.py scripts/tests/test_codex_project_autopilot.py scripts/github_project_task.py scripts/ego_operator_devloop.py`
  - `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_github_project_task.py scripts/tests/test_ego_operator_devloop.py scripts/tests/test_codex_project_autopilot.py`
  - `git diff --check -- .codex .agents/skills/codex-project-autopilot AGENTS.md scripts/codex_project_autopilot.py scripts/tests/test_codex_project_autopilot.py docs/codex/tasks/codex-cross-project-devloop-toolkit-v1 docs/codex/tasks/codex-autopilot-l2-dirty-baseline-v1`
