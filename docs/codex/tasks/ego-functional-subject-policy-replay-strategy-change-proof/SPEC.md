# EgoOperator Policy Replay Actual Strategy-Change Proof v2

## Goal

Prove that a repeated failure policy patch changes the next comparable strategy surface, not just that a policy patch candidate exists in trace.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory

Forbidden changes:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-018`
- `/tmp/ego_functional_subject_real_provider_rerun_20260521b/gpt55_judge_result.json`

## Acceptance Gate

- Before/after comparable failure probe shows no replay before setup and an active replay after setup.
- Replay changes a downstream strategy surface such as bounded initiative candidate or outcome repair priority.
- Policy replay proof replies cite trace/replay evidence rather than proposing unexecuted memory/file side effects as proof.

## Claim Ceiling

`Functional Subject policy strategy-change proof local/scripted candidate pass`
