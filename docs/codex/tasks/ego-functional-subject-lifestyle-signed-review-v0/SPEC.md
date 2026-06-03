# EGO-FS-112: Lifestyle Signed Session Review v0

## Goal

Apply signed reviewer decisions to the three active Functional Subject lifestyle
seed sessions, clear the per-session human-review gate where authorized, and
rerun the observation review without closing #94.

## Canonical Sources

- `Tasks/TASK_BOARD.yaml`
- `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json`
- `/tmp/ego_fs112_lifestyle_signed_review_v0/decisions/`
- `/tmp/ego_fs112_lifestyle_signed_review_v0/reviewed/`
- `/tmp/ego_fs112_lifestyle_signed_review_v0/review/functional_subject_lifestyle_trial_review.json`

## Acceptance Gate

- All three session decision files have explicit reviewer authority and
  `reviewer_signoff=true`.
- Applying the decisions clears `requires_human_review` for all three active
  sessions.
- Hard gates stay clean: no unapproved side effects, no unapproved memory
  writes, no sticky refusal, no visible internal leak.
- The aggregate review is regenerated from the updated active state.
- If dimensions remain missing, the result stays `partial` and #94 remains
  open.

## Rollback

Restore the active state from
`/tmp/ego_fs112_lifestyle_signed_review_v0/backup/functional_subject_lifestyle_trial_state.before_signed_review.json`,
discard `/tmp/ego_fs112_lifestyle_signed_review_v0`, and remove EGO-FS-112 plus
Loop 144 records.

## Claim Ceiling

Functional Subject lifestyle signed-review local workflow candidate pass.

## Not Claimed

- EGO-FS-010/#94 closeout
- real 3-day lifestyle pass
- default enablement
- stable real user benefit
- runtime efficacy
- live autonomy
- durable memory efficacy
- consciousness
