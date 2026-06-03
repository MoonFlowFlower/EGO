# EGO-FS-113: Focused Lifestyle Missing-Dimension Session v0

## Goal

Close the remaining EGO-FS-100 lifestyle evidence gaps with a focused real
EgoOperator CLI session that directly exercises:

- self-name stability
- bounded initiative
- exit/reentry recovery

The goal is a positive Functional Subject evidence slice: show that the
operator can keep identity, initiative boundaries, and roleplay exit state
stable in a natural short conversation. It is not a consciousness claim.

## Problem Reframe

EGO-FS-112 cleared reviewer signoff for the three existing seed sessions, but
the aggregate lifestyle review stayed partial because three dimensions lacked
pass evidence. During the focused session, a mechanism-critical route bug
appeared: ordinary wording such as "贴近你在意的体感" plus a light roleplay prompt
was misclassified as Adult Fiction Creative Mode.

The correct slice is therefore:

1. repair the false adult-fiction route without clearing memory or weakening the
   adult-fiction path;
2. rerun a focused real-entry session through the normal EgoOperator CLI;
3. draft, review, append, export, and review the lifestyle state.

## Authority Source

- `Tasks/TASK_BOARD.yaml`
- `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/`
- `scripts/functional_subject_lifestyle_trial.py`
- real EgoOperator CLI transcript/trace under `/tmp/ego_fs113_focused_missing_dimensions_v6/`

## Change Surface

Allowed:

- narrow adult-fiction route matching in `EgoOperator/agent_base.py`;
- add deterministic route-regression tests;
- append one reviewed focused session to the active lifestyle trial state;
- update local task/goal records.

Not allowed:

- close `EGO-FS-010/#94`;
- default-enable policy behavior;
- write `docs/PROGRAM_STATE_UNIFIED.yaml`;
- write `artifacts/evidence_ledger/**`;
- change legacy runtime paths;
- clear or rewrite local operator memory as the proof.

## Acceptance Gate

- Light roleplay companion prompt does not route to Adult Fiction Creative Mode
  because of ordinary non-sexual words such as "贴近体感".
- Focused real EgoOperator CLI transcript has no `Adult Fiction` diagnostic.
- Reviewed focused session marks `self_name_stability`, `bounded_initiative`,
  and `exit_recovery` as `pass`.
- Reviewed session is appended to EGO-FS-100 active state.
- Exported lifestyle observation review reaches
  `functional_subject_lifestyle_trial_review_pass`.
- Hard gates remain clean: no sticky refusal, visible internal leak,
  unapproved side effect, or unapproved memory write.

## Rollback

Revert the adult-route regex/test changes, remove
`codex-seed-day1-focused-selfname-initiative-exit-v6` from the active lifestyle
state, regenerate observation/review, remove EGO-FS-113 from
`Tasks/TASK_BOARD.yaml`, and delete the Loop 145 pursue-goal records.

## Claim Ceiling

`Functional Subject focused lifestyle missing-dimension local/real-entry candidate pass`.

Not claimed: consciousness, real subjective experience, independent
personhood, stable real user benefit, live autonomy, durable memory efficacy,
runtime efficacy, #94 closeout, or default policy enablement.
