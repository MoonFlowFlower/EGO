# Codex Autopilot L3/L4 v2 PLAN

## Milestone 1: Board And Contract

- Create #21 for L3 verified closeout executor.
- Create #22 for L4 scheduled dry-run patrol.
- Extend `.codex/project_contract.yaml` with `auto_closeout` rules and v2 task path.

## Milestone 2: L3 Closeout Oracle

- Add `verify-profile`, `closeout-check`, and `closeout-once`.
- Require local verify profile before closeout.
- Require LLM reviewer only for `scripted_with_llm_judge`.
- Block hard-stop classes and high-impact markers before any reviewer.

## Milestone 3: L4 Dry-Run Patrol

- Extend `run-loop` with `--mode l3-closeout`.
- Add `--write-report` under ignored `.codex/autopilot/runs/`.
- Create a daily Codex cron automation that only runs dry-run patrol.

## Milestone 4: Verification And Closeout

- Run py_compile, script tests, doctor/report, L3 dry-run report, and scoped diff check.
- Close #21 after L3 passes.
- Move #22 to `In Progress` after automation creation; close it only after scheduled report evidence exists.

## Rollback

Revert contract, script, tests, task docs, and schema changes; pause/delete the Codex automation.
