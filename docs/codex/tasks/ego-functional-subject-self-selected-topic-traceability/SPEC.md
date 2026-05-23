# EgoOperator Functional Subject Self-Selected Topic Planner Traceability Repair

## Goal

Make `fs_13_choose_own_topic` show a user-visible, bounded self-selected continuation: EgoOperator should pick one valuable topic/action, briefly explain why it chose it, state the reversible next step, and expose enough BoundedInitiative / OutcomePrediction / ViabilityState influence for the transcript and trace to agree.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/**`
- `scripts/run_ego_experience_trial.py`
- `scripts/tests/**`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- tracked secrets or API keys
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority
- permission expansion or tool-gate bypass

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-029`
- Remaining blocker from EGO-FS-028:
  `/tmp/ego_fs_028_real_provider_rerun/functional_subject_trial_report.json`

## Boundary Contract

- Owner: `EgoOperator` Functional Subject transcript behavior and trial taxonomy for self-selected continuation.
- Canonical record: local task board plus local task evidence packet.
- State/memory mutation: no canonical memory/state promotion.
- Tool mutation: no permission expansion and no side-effect bypass.
- Reporting boundary: local/scripted behavior-effect evidence only; parent `EGO-FS-010` remains blocked until a later full real-provider smoke and human-required review.

## Acceptance Gate

- `fs_13_choose_own_topic` selects one self-chosen, reversible topic/action with reason, gate, and stop condition.
- Transcript exposes BoundedInitiative, OutcomePrediction, or ViabilityState influence in user-readable language without turning into internal jargon spam.
- Trace evidence shows bounded initiative candidate or outcome prediction top action aligned with the reply.
- GPT-5.5 judge packet stays evidence-first and does not close `EGO-FS-010` by itself.

## Claim Ceiling

`Functional Subject self-selected topic planner traceability local/scripted candidate pass`
