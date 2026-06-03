# Stage Card: EGO-FS-079 Policy Default-Enablement v0

## Problem Reframe

The user explicitly authorized creating a default-enablement Stage Card. That
authorization is not authorization to enable the policy patch. The real task is
to define the minimum contract that must be satisfied before any
behavior-changing default enablement can be proposed, implemented, or claimed.

The risk is a silent jump from a disabled feedback-policy artifact to default
runtime calibration. That would break the Functional Subject evidence chain by
turning advisory replay data into active policy without human sanity evidence,
reviewer approval, rollback proof, or longer real-provider observation.

## One Hypothesis

Default enablement can become safe to implement only if it is split into a
separate, feature-flagged proof task with explicit reviewer approval, human
sanity evidence or explicit risk acceptance, no memory/training side effects,
and a rollback arm that proves the runtime returns to the disabled baseline.

## One Change Surface

Documentation and task-state only.

This Stage Card may define:

- prerequisites;
- feature flag name;
- replay packs;
- reviewer gate;
- implementation boundary;
- rollback proof;
- claim ceiling.

This Stage Card must not change:

- EgoOperator default runtime behavior;
- policy enablement;
- memory;
- training;
- tools;
- approvals;
- program state;
- evidence ledger;
- GitHub Project truth-source state.

## Authority Source

- `Tasks/TASK_BOARD.yaml` is canonical task state.
- This Stage Card is the default-enablement planning contract.
- `Tasks/stage_cards/ego-fs-074-policy-enablement-decision-gate-v0.md` is the
  prior enablement decision gate.
- `/tmp/ego_fs072_feedback_policy_patch_admission_record_v1/feedback_policy_patch_admission_record.json`
  is the disabled admission artifact.
- `/tmp/ego_fs073_policy_admission_review_guard_v1/policy_admission_review_guard_report.json`
  is broader replay guard evidence.
- `/tmp/ego_fs075_policy_opt_in_proof_arm_v1/policy_opt_in_proof_arm_report.json`
  is opt-in proof-arm evidence.
- `/tmp/ego_fs076_policy_reviewer_packet_v1/policy_reviewer_packet_report.json`
  is the current reviewer hold packet.
- `docs/codex/tasks/ego-pursue-functional-subject-goal-v1/` is the loop ledger.

## What Can Change Later

A later separately authorized implementation/proof task may add a
disabled-by-default feature flag and a proof mode that applies the admitted
policy patch inside a controlled arm.

Suggested flag:

`EGO_POLICY_PATCH_DEFAULT_ENABLEMENT_PROOF=1`

The flag name is reserved for a proof task. It must not be enabled by this Stage
Card.

## What Cannot Be Proven Here

This Stage Card cannot prove:

- default enablement works;
- production feedback learning works;
- stable user benefit;
- live autonomy;
- durable memory efficacy;
- real subjective experience;
- independent personhood;
- consciousness.

## Boundary Contract

- Owner: `EgoOperator`.
- Candidate record: `FeedbackPolicyPatchAdmissionRecord`.
- Current admission status: `review_ready_disabled`.
- Default status after this Stage Card: disabled.
- LLM role: interpret, propose, and explain only.
- Runtime gate role: own admission and all side-effect boundaries.
- Memory gate role: unchanged; no policy patch may write memory.
- Tool gate role: unchanged; no policy patch may execute tools.
- Approval gate role: unchanged; no policy patch may create or approve actions.
- Program state and evidence ledger: not modified by this stage.

## Mainline E2E

Allowed future path:

`user event -> PredictionRecord -> feedback observation -> candidate update -> disabled admission artifact -> broader replay guard -> reviewer packet -> default-enablement Stage Card -> feature-flagged proof task -> runtime gate -> trace -> rollback proof -> reviewer decision`.

Forbidden paths:

- `feedback observation -> silent default runtime calibration`;
- `disabled admission artifact -> automatic policy enablement`;
- `policy patch -> memory write`;
- `policy patch -> training`;
- `policy patch -> tool/action/approval execution`;
- `scripted pass -> claim stable user benefit`.

## Prerequisites Before Any Implementation Task

All must be true before a default-enablement implementation/proof task is
allowed:

1. EGO-FS-072 admission artifact still passes and remains disabled.
2. EGO-FS-073 broader replay guard still passes.
3. EGO-FS-075 opt-in proof arm still passes.
4. EGO-FS-076 reviewer packet is updated or superseded by a reviewer packet
   that explicitly allows a proof task.
5. EGO-FS-053 human sanity transcript is reviewed as pass, or the user writes
   an explicit risk acceptance that scripted-only proof is enough for this
   proof task.
6. Longer real-provider observation scope is defined before any default-on
   claim.
7. Rollback proof plan names the exact disable command/env var and expected
   no-residue checks.

## Minimum Replay Contract

Any future implementation/proof task must run at least:

- source admission record replay;
- primary Functional Subject sample pack;
- blind unlabeled guard pack;
- policy opt-in proof arm;
- disabled rollback arm;
- one human sanity transcript review or explicit scripted-only risk acceptance;
- no-tools/no-approvals/no-memory/no-training checks.

The proof task must report:

- target improvement count;
- unrelated regression count;
- broad pattern collision count;
- enabled application count;
- rollback disabled-arm application count;
- visible transcript deltas;
- failure taxonomy;
- what the result cannot prove.

## Reviewer Gate

Before any default-on behavior:

- A reviewer packet must compare enabled proof arm, disabled rollback arm, and
  baseline behavior.
- The reviewer packet must list exact accepted risk, residual blockers, and
  rollback instructions.
- If the reviewer verdict is not explicit pass, the patch remains disabled.

## Rollback Plan

Rollback for this Stage Card:

- delete this file;
- remove EGO-FS-079 from `Tasks/TASK_BOARD.yaml`;
- remove Loop 80 records from the pursue-goal docs.

Rollback for any future proof implementation must include:

- unset `EGO_POLICY_PATCH_DEFAULT_ENABLEMENT_PROOF`;
- rerun the disabled rollback arm;
- confirm no memory writes;
- confirm no training artifacts;
- confirm no tool calls or pending approvals;
- confirm runtime selection is unchanged by default;
- record the rollback evidence in the task ledger.

## Evidence Report

This Stage Card is based on:

- EGO-FS-072: disabled policy patch admission record;
- EGO-FS-073: broader replay guard;
- EGO-FS-074: enablement decision gate;
- EGO-FS-075: opt-in proof arm;
- EGO-FS-076: reviewer hold packet;
- EGO-FS-077: current human sanity packet/proxy refresh;
- EGO-FS-078: stale-goal freshness guard.

Current known blockers:

- user human sanity evidence is still missing;
- reviewer approval for enablement is still missing;
- longer real-provider observation is still missing;
- no default-enablement implementation task is authorized by this Stage Card.

## Claim Ceiling

`Policy default-enablement Stage Card local planning pass`.

This does not claim default enablement, runtime efficacy, stable user benefit,
live autonomy, durable memory efficacy, real subjective experience, independent
personhood, or consciousness.
