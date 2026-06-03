# Stage Card: EGO-FS-074 Policy Enablement Decision Gate v0

## Problem Reframe

EGO-FS-072 and EGO-FS-073 proved a feedback-derived policy patch can be
packaged, reviewed, and kept disabled across broader replay guards. The next
risk is not another replay micro-patch; it is accidentally turning a
candidate-only learning artifact into default runtime behavior without enough
human evidence, rollback, or admission governance.

## One Hypothesis

Any policy-patch enablement must pass through a separate decision gate that
keeps default calibration disabled, requires explicit reviewer approval, and
allows only a bounded opt-in proof arm until human sanity evidence and replay
coverage are strong enough.

## One Change Surface

Documentation and task-state only. This stage card may define prerequisites,
replay coverage, reviewer gate, rollback, and future proof-arm shape. It must
not change EgoOperator default runtime selection, memory, training, policy
state, approval gates, or tool behavior.

## Authority Source

- `Tasks/TASK_BOARD.yaml` for canonical task state.
- `docs/codex/tasks/ego-pursue-functional-subject-goal-v1/` for loop records.
- `/tmp/ego_fs072_feedback_policy_patch_admission_record_v1/feedback_policy_patch_admission_record.json` as the disabled admission artifact.
- `/tmp/ego_fs073_policy_admission_review_guard_v1/policy_admission_review_guard_report.json` as the broader review guard evidence.
- `EgoOperator/primitives/developmental_shadow.py` for the review-artifact schema boundary.

## What Can Change

- Future task wording and admission requirements.
- A future lab-only proof arm, if separately implemented behind an explicit
  opt-in flag.
- Evidence packet requirements for any later enablement proposal.

## What Cannot Change In This Stage

- No default runtime calibration.
- No memory write or memory promotion.
- No training or model update.
- No tool execution, external action, approval creation, file write, or network
  action.
- No program state or evidence ledger mutation.
- No GitHub Project status as task truth source.

## Boundary Contract

- Owner: `EgoOperator`.
- Candidate record: `FeedbackPolicyPatchAdmissionRecord`.
- Admission status: must remain `review_ready_disabled`.
- Runtime authority: unchanged; current gates continue to own side effects.
- LLM role: proposal / interpretation only.
- Enablement precondition: a separate Stage Card or implementation task must
  name the exact feature flag, scope, replay pack, reviewer, rollback command,
  and allowed write targets before any behavior change.

## Mainline E2E

The only acceptable future path is:

`user event -> PredictionRecord -> feedback observation -> candidate update -> disabled admission artifact -> broader replay guard -> reviewer decision -> opt-in proof arm -> runtime gate -> trace`.

The following path is forbidden:

`feedback observation -> silent default calibration -> changed runtime behavior`.

## Replay Contract

Minimum replay before any future opt-in proof arm:

- Source admission record still passes.
- Primary Functional Subject pack still passes.
- Blind unlabeled guard pack still passes.
- Broad pattern collisions are recorded but not applied.
- No scoped application appears outside the admitted target scope.
- No unrelated regression.
- No tools, approvals, memory writes, training, or default runtime changes.

Minimum replay before any future default enablement proposal:

- All opt-in proof-arm checks above pass.
- At least one human sanity transcript or explicit user acceptance of
  scripted-only risk is recorded.
- A rollback proof shows the feature can be disabled without residue.
- A reviewer packet states what the patch improves, what it regresses, and what
  it cannot prove.

## Evidence Report

Current supporting evidence:

- EGO-FS-072: disabled feedback policy patch admission record pass.
- EGO-FS-073: broader policy admission review guard pass across two replay
  packs and 26 records.
- Broad pattern collision count: `1`.
- Enabled application count: `0`.
- Unrelated regression count: `0`.
- Default runtime change, memory write, training, tools, and approvals remain
  forbidden.

## Rollback Plan

Rollback for this stage is deleting this stage card and the EGO-FS-074 task
record. No runtime rollback is needed because this stage performs no runtime
mutation.

Rollback for any future opt-in proof arm must include:

- unset/disable the feature flag;
- clear any candidate-only proof-arm config;
- rerun the same replay pack with the proof arm disabled;
- confirm no memory, approval, tool, or policy state residue remains.

## Claim Ceiling

`Policy enablement decision-gate local planning pass`.

This does not prove default calibration, policy enablement, feedback-driven
learning in production, stable user benefit, live autonomy, durable memory
efficacy, real subjective experience, independent personhood, or consciousness.
