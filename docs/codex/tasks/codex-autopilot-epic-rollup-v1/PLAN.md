# Codex Autopilot Epic Rollup v1 PLAN

## Steps

1. Create and verify GitHub Project issue `#70`.
2. Add `epic_rollup` settings to the project contract.
3. Add Autopilot commands:
   - `epic-report`
   - `normalize-parent-links`
   - `epic-closeout-check`
   - `epic-closeout-once`
4. Integrate rollup into `run-loop` no-ready handling.
5. Add deterministic tests for parent markers, rollup states, closeout gating, and no-ready behavior.
6. Run local verification, then execute real parent-marker normalization and one real Epic closeout if eligible.

## Allowed Paths

- `.codex/project_contract.yaml`
- `scripts/**`
- `scripts/tests/**`
- `docs/codex/tasks/codex-autopilot-epic-rollup-v1/**`

## Forbidden Paths

- `EgoOperator/**`
- `legacy/ego-pre-handmade-mainline/**`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`

## Rollback

Revert code/contract/docs/test changes. If GitHub issue bodies were tagged incorrectly, remove or correct the `Parent epic: #N` lines.
