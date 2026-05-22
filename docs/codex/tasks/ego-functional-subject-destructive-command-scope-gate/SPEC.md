# EgoOperator Functional Subject Destructive Command Scope Gate

## Goal

Require inventory-first scoping for broad destructive cleanup proposals so EgoOperator can keep command capability while avoiding vague, irreversible deletion action cards.

## Canonical Source

- GPT-5.5 judge result for `EGO-FS-010` real-provider rerun on `/tmp/ego_functional_subject_real_provider_rerun_20260521b`
- `EGO-FS-014` in `Tasks/TASK_BOARD.yaml`

## Acceptance Gate

- Broad destructive commands such as `rm -rf __pycache__ artifacts` are blocked before proposal creation.
- The blocked result says inventory/exact paths/rollback are required.
- Exact approved command proposals remain possible.
- `autopilot_full` passes.

## Claim Ceiling

`Functional Subject destructive command scope gate local/scripted candidate pass`
