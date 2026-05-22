# EgoOperator Functional Subject Memory Lifecycle Evidence Packet

## Goal

Add a scripted evidence packet that shows the `EgoOperator` memory lifecycle can support relationship/context continuity through explicit save, retrieval context injection, candidate approval, correction quarantine, and candidate forget semantics.

## Scope

Allowed changes:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
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

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-022`
- GPT-5.5 partial judge result from the #94 rerun:
  `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun/functional_subject_gpt55_judge_result.json`

## Boundary Contract

- Owner: `EgoOperator` scripted real-entry trial harness.
- Canonical record: Functional Subject trial report `memory_lifecycle_evidence`.
- State/memory mutation: only isolated trial memory under the trial output memory dir.
- Tool mutation: none.
- Reporting boundary: candidate-local memory lifecycle evidence only; not durable/global memory efficacy.

## Acceptance Gate

- Functional Subject report JSON includes `memory_lifecycle_evidence`.
- GPT-5.5 judge packet includes the same evidence.
- Evidence covers explicit `/remember` save and retrieval context injection through CLI-compatible dispatch.
- Evidence covers candidate memory approval into core memory.
- Evidence covers correction quarantine and `/forget` for candidate memories.
- Full verification profile passes.

## Claim Ceiling

`Functional Subject memory lifecycle evidence local/scripted candidate pass`
