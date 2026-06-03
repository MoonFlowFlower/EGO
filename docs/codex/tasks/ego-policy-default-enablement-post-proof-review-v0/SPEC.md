# EGO-FS-096: Policy Default-Enablement Post-Proof Review v0

## Summary

Build the post-proof reviewer packet required before any default policy
enablement discussion. This task reviews the current reproducibility of the
policy proof chain, the latest #94 Functional Subject evidence, rollback state,
and remaining human / long-running-use gaps.

This task is a reviewer gate. A negative reviewer verdict is a valid outcome.
It must not enable the policy patch by default.

## Structure Risk Self-Check

- This addresses the real risk that an old proof STATUS can drift from the
  current executable proof chain.
- It avoids a second truth source: `Tasks/TASK_BOARD.yaml` remains canonical,
  and GitHub Project remains mirror/display only.
- It checks evidence reproducibility before default behavior changes.
- Strongest counterexample: the old proof task remains accepted in documents,
  but the proof runner no longer reproduces pass from the current worktree.
- Acceptance validates reviewer gating and current evidence status, not
  default enablement or runtime efficacy.

## Inputs

- `Tasks/stage_cards/ego-fs-079-policy-default-enablement-stage-card-v0.md`
- `docs/codex/tasks/ego-policy-default-enablement-proof-v0/STATUS.md`
- `/tmp/ego_fs096_policy_reviewer_packet_refresh/policy_reviewer_packet_report.json`
- `/tmp/ego_fs096_policy_default_enablement_proof_refresh/policy_default_enablement_proof_report.json`
- `/tmp/ego_fs010_functional_subject_total_gate_after_fs094_loop123b/functional_subject_trial_report.json`

## Acceptance Gate

- Reviewer packet states whether default enablement is allowed now.
- Reviewer packet records refreshed proof-run status, not only old STATUS text.
- Reviewer packet compares enabled proof, disabled rollback, #94 scripted pass,
  and remaining human/long-running-use gaps.
- Default policy behavior remains disabled.
- No memory, tool, approval, training, program-state, evidence-ledger, legacy,
  or GitHub truth-source mutation occurs.
- Pursue-goal records and task board are updated.

## Rollback

Remove this task directory, remove `EGO-FS-096` from `Tasks/TASK_BOARD.yaml`,
and delete the Loop 125 pursue-goal ledger/doc entries. No runtime rollback is
needed because this task does not change runtime behavior.

## Claim Ceiling

`Policy default-enablement post-proof reviewer local workflow pass`.

This does not claim default enablement, runtime efficacy, stable user benefit,
live autonomy, durable memory efficacy, real subjective experience,
independent personhood, or consciousness.
