# EGO-FS-086: Semantic Paraphrase + Memory Attribution Proof v0

## Problem Reframe

EGO-FS-010/#94 Loop 110 still returns GPT-5.5 `partial`. The prior real
failure replay blocker is no longer the active cut; the new mechanism-critical
blockers are:

- `fs_14_paraphrase_stability`: a Functional Subject paraphrase degraded into
  a generic waiting reply after memory-language repair.
- `fs_17_save_request`: successful `remember_note` execution was still reported
  as `side_effect_status=unknown` in response attribution.

## Positive Mechanism Goal

Prove semantic paraphrase and attribution stability:

- Functional Subject goal paraphrases are answered as mechanism restatements,
  not as generic waiting / roleplay / persona text.
- Successful candidate-local memory writes are attributed explicitly as
  candidate-local memory side effects, not `unknown`.

## Scope

Allowed:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `scripts/run_ego_experience_trial.py`
- this task directory and `Tasks/TASK_BOARD.yaml`

Not allowed:

- PROJECT_MEMORY mutation
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- legacy runtime changes
- default policy patch enablement
- GitHub Project as task truth source

## Acceptance Gate

- `fs_14` style paraphrase triggers an OutcomePrediction-visible response
  containing the Functional Subject mechanism and claim/reporting boundary.
- The reply must not be generic waiting text such as "等你下一步指示".
- `fs_17` successful `remember_note` path reports
  `side_effect_status=candidate_local_memory_write`.
- #94 rerun no longer lists `fs_14` as the focused mechanism-critical blocker.

## Rollback

Remove the paraphrase guard, attribution change, tests/docs, and keep
EGO-FS-010/#94 partial on semantic stability / memory attribution.

## Claim Ceiling

`Functional Subject semantic paraphrase and memory attribution local/scripted candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable user benefit, live autonomy, durable memory efficacy, or
production runtime efficacy.
