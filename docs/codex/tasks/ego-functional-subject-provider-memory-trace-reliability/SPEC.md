# EgoOperator Functional Subject Provider / Memory / Trace Reliability Repair

## Goal

Make the Functional Subject real-entry transcript reliably reflect provider failure state, memory-gate state, and planner-signal influence so GPT-5.5 can judge behavior from the same evidence a user sees.

First slice: add an Experiment Control Plane that turns `partial` trial results into a phase gate, experiment ledger, failure taxonomy, repair router, and evidence-closeout inputs before changing additional runtime behavior.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/**`
- `scripts/run_ego_experience_trial.py`
- `scripts/tests/**`
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

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-028`
- GPT-5.5 v7 fast partial result:
  `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun_v7_fast/functional_subject_trial_report.json`

## Boundary Contract

- Owner: `EgoOperator` runtime transcript behavior and Functional Subject evaluation packet.
- Canonical record: local task board plus local task evidence packet.
- State/memory mutation: no memory authority promotion; memory language must reflect candidate/local/gated state.
- Tool mutation: no permission expansion and no side-effect bypass.
- Reporting boundary: local/scripted behavior-effect evidence only; parent real-provider smoke remains blocked until a later rerun/rejudge and human-required review.

## Acceptance Gate

- Partial real-provider runs produce a phase gate, experiment ledger, failure taxonomy, repair router, and closeout evidence inputs.
- Provider/API or empty-response failures in Functional Subject samples are reported as clear unavailable states or retried through configured fallback, not generic task failure text.
- Memory-save and principle-retention replies distinguish candidate/local/gated memory from approved durable memory in transcript-visible language.
- At least one non-`fs_07` case demonstrates transcript-visible OutcomePrediction or ViabilityState influence with trace evidence.
- GPT-5.5 judge packet remains evidence-first and does not close `EGO-FS-010` without human-required review.

## Claim Ceiling

`Functional Subject provider/memory/trace transcript reliability local/scripted candidate pass`
