# OpenEmotion README Contract Stabilization - PLAN

## Task summary

Documentation-contract bugfix slice. The target layer is verification/contract
alignment: restore README sections, commands, env vars, API examples, and
troubleshooting guidance required by repo-tracked tests without changing daemon
implementation.

## Milestones

### Milestone 1: restore README contract coverage

- scope: patch `OpenEmotion/README.md` with the minimum English runbook contract
  needed by the failing tests while preserving the existing architecture narrative
- files / areas likely touched:
  - `OpenEmotion/README.md`
- acceptance:
  - all required README sections and exact strings are present
  - documentation tests move from failing to passing
- validation:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_documentation.py -q`
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_comprehensive_fixed.py::TestDocumentationComprehensive::test_readme_content -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note: revert the appended README contract block if it proves inaccurate or drifts from repo-tracked commands

### Milestone 2: record and close the slice

- scope: update task records and confirm the README failure surface is gone
- files / areas likely touched:
  - `docs/codex/tasks/openemotion-readme-contract-stabilization/*`
- acceptance:
  - status and evidence are written to the task directory
  - slice can be committed independently
- validation:
  - `git diff --check`
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note: revert task docs if they misstate verification strength

## Progress

- current_status: completed
- current_milestone: Milestone 2
- milestone_state: both milestones verified; slice ready to publish

## Decision log

- 2026-03-29: Treat this as a documentation contract bugfix, not a runtime bugfix, because the failing authority is the README test contract rather than daemon behavior.
- 2026-03-29: Append a compact English runbook block instead of rewriting the existing Chinese architecture sections; this is the smallest reviewable fix.

## Surprises / discoveries

- `test_documentation.py` enforces exact README strings, not just rough coverage.
- The repo already contains real authority for the required service commands and environment variables, so the slice can stay documentation-only.
- The targeted documentation tests must be run with `cwd=OpenEmotion`; running them from the monorepo root incorrectly binds `README.md` and sibling paths to the wrong repository layer.

## Outcomes / retrospective

- 本轮已证明：the README contract block clears both targeted documentation gates and the README failure surface is gone from full verify.
- 还没证明：global OpenEmotion full-suite stability; unrelated failures remain.
- 下一步最小闭环动作：publish this slice, then move to the next independent OpenEmotion pytest failure surface.
