# Codex Autopilot L2 Dirty Baseline PLAN

## Milestone 1: Board Transition

- Close #17 as L0/L1 complete.
- Create #18 for dirty-baseline scoped L2.

## Milestone 2: Baseline And Scope

- Add local baseline recording under `.codex/autopilot/`.
- Add diff-scope comparison that separates unchanged pre-existing dirty paths from scoped and unsafe new changes.
- Use tracked dirty status by default so large untracked runtime/artifact folders do not make the autopilot control plane unusable.

## Milestone 3: L2 Dry-Run Shape

- Add `run-once --issue N --dry-run`.
- Add `normalize-issue --issue N --dry-run`.
- Keep v2 dry-run only for implementation planning; no automatic code patching.

## Milestone 4: Verification

- Run script tests, py_compile, scoped diff check, and real dry-run commands.
- Commit/push only scoped files.
