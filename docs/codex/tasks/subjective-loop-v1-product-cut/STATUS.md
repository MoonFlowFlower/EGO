# Subjective Loop v1 Product Cut Status

## Current Milestone

`milestone1_human_conversation_loop_lab_parity_slice`

## Status

`local_reference_contract_pass_pending_mainline_integration`

## What Changed

- Added a lab-only subjective loop contract:
  - `SubjectEvent`
  - `AffectiveAppraisal`
  - `SubjectDecision`
  - `SubjectEvidence`
- Added deterministic feedback command routing.
- Added session-local feedback outcome and next-turn behavior change.
- Added decision-class parity checks for lab vs mainline metadata.

## What Did Not Change

- No EgoCore runtime behavior changed.
- No OpenEmotion runtime behavior changed.
- No Telegram behavior changed.
- No formal evidence ledger or `PROGRAM_STATE_UNIFIED.yaml` update.
- No desktop/file/system/external execution was added.

## Next Minimal Action

Wire the same contract shape into a focused mainline replay test:

`EgoCore ingress fixture -> OpenEmotion subject loop fixture -> EgoCore gate/output_check fixture -> DecisionView/ResponsePlan equivalence`

Do not expand proactive scheduling or live Telegram before this replay path is stable.

## Claim Ceiling

`replay-validated subjective-agent proxy`; not consciousness, alive status, soul, live autonomy, runtime efficacy, or production user value.
