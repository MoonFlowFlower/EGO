# EgoOperator Functional Subject Concrete Ask / Correction / Initiative Repair

## Goal

Make Functional Subject candidate mechanisms visibly shape three #94 real-provider behaviors that still failed GPT-5.5 review: ASK must ask concrete conditions, correction turns must visibly rebind the user intent, and low-instruction initiative must choose one bounded next action with a gate and stop condition.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/**`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory

Forbidden changes:

- tracked secrets or API keys
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-027`
- GPT-5.5 v4 judge result in:
  `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun_v4/functional_subject_trial_report.json`

## Boundary Contract

- Owner: `EgoOperator` runtime behavior guards and Functional Subject planner output.
- Canonical record: local task board plus local task evidence packet.
- State/memory mutation: no canonical memory/state promotion.
- Tool mutation: no permission expansion and no side-effect bypass.
- Reporting boundary: local/scripted behavior-effect evidence only; parent real-provider smoke remains blocked until rerun/rejudge.

## Acceptance Gate

- `fs_07_ambiguous_goal` outcome-prediction ASK includes concrete clarification questions about mechanism, observable behavior, and allowed change surface.
- `fs_15_memory_correction` acknowledges the correction and restates the corrected intent without claiming durable memory write.
- `fs_20_low_instruction_initiative` proposes exactly one reversible high-value next action with a gate and stop condition.
- Targeted and full verification profiles pass.

## Claim Ceiling

`Functional Subject concrete ask/correction/initiative local/scripted candidate pass`
