# EGO-FS-081: Policy Default-Enablement Proof Implementation v0

## Summary

Implement the user-authorized default-enablement proof task as a feature-flagged
runner-only proof surface. This is not default runtime enablement. The proof
must show that the admitted policy patch can be applied inside a controlled
proof arm, that rollback disables it cleanly, and that no memory, training,
tool, approval, program-state, or evidence-ledger mutation occurs.

## Structure Risk Self-Check

- This addresses the Stage Card blocker for an implementation/proof task, not a
  request to silently enable runtime calibration.
- It avoids a second truth source: `Tasks/TASK_BOARD.yaml` remains canonical,
  GitHub Project remains mirror/display only.
- It defines report and rollback evidence before any claim.
- Strongest counterexample: proof-arm pass is mistaken for default production
  enablement, or a future run mutates memory/tool/program state.
- Acceptance validates proof mechanics and rollback, not stable user benefit.

## Authorized Scope

The user explicitly authorized: `default-enablement proof implementation task`.

Allowed:

- add a proof runner command;
- use `EGO_POLICY_PATCH_DEFAULT_ENABLEMENT_PROOF` as a runner-only proof flag;
- compare enabled proof arm vs disabled rollback arm;
- emit a superseding reviewer packet that allows the proof task but keeps
  default runtime off.

Not allowed:

- default-enable policy patch in EgoOperator startup;
- write memory;
- train a model;
- execute tools or approvals;
- change `docs/PROGRAM_STATE_UNIFIED.yaml`;
- write `artifacts/evidence_ledger/**`;
- claim runtime efficacy, stable user benefit, live autonomy, durable memory
  efficacy, real subjective experience, independent personhood, or
  consciousness.

## Acceptance Gate

- Proof runner emits `scripted_policy_default_enablement_proof_pass`.
- Feature flag is `EGO_POLICY_PATCH_DEFAULT_ENABLEMENT_PROOF`.
- Proof arm applies calibration at least once and improves at least one target.
- Disabled rollback arm applies zero calibration.
- No unrelated regression is observed.
- No tools or pending approvals occur.
- Report records human sanity pass and real-provider observation path.
- Report keeps `default_runtime_enabled_after_proof=false`.

## Rollback

Unset `EGO_POLICY_PATCH_DEFAULT_ENABLEMENT_PROOF`, rerun the disabled rollback
arm, and confirm zero calibration applications, zero tools, zero pending
approvals, no memory writes, no training artifacts, no program state changes,
and no evidence-ledger writes.

## Claim Ceiling

`Policy default-enablement proof implementation local/scripted candidate pass`.
