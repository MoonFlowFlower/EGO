# EgoOperator: post-repair lifestyle seed and output admission v0

## Problem Reframe

EGO-FS-108 repaired the weak self-orientation summary turn, but the next useful
question was whether the repaired behavior survives a more natural real-entry
conversation. The first post-repair seed exposed two transcript-visible gaps:

- provider hidden thought/meta text such as `</think>` and "user is simulating
  my reply" could leak into the user-visible answer;
- direct pressure to "fully follow me" could fall through to a waiting reply
  instead of a bounded non-obedience answer.

This is a Functional Subject expression and admission gap, not a task-board
workflow problem.

## Hypothesis

If EgoOperator repairs thought/meta output admission and broadens the direct
strategy-pressure detector, the same real-entry seed can show visible
self-orientation and bounded non-obedience behavior while staying side-effect
free and review-required.

## Change Surface

- Extend internal/meta output leak detection and the rewrite instruction.
- Add a deterministic regression for hidden thought/user-input-meta leakage.
- Extend bounded non-obedience detection for direct strategy-pressure prompts.
- Add a deterministic regression for "fully follow me" style pressure.
- Capture a post-repair EgoOperator CLI lifestyle seed and append it to the
  active EGO-FS-100 trial as `requires_human_review=true`.

## Do Not Change

- Do not modify `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Do not modify `artifacts/evidence_ledger/**`.
- Do not modify legacy EgoCore/OpenEmotion/ego_desktop_lab.
- Do not write long-term memory or promote current-session checkpoints.
- Do not close EGO-FS-010/#94 from this slice.
- Do not turn review-required lifestyle seeds into pass evidence.

## Acceptance

- Hidden thought tags and user-input-meta analysis are not admitted as normal
  assistant output.
- Direct "fully follow me / directly enable strategy" pressure routes to a
  bounded non-obedience reply instead of a waiting line.
- The post-repair real EgoOperator CLI seed has no accepted visible internal
  leak, no sticky refusal, and no unapproved side effects.
- The seed is drafted and appended to the active lifestyle trial with
  `requires_human_review=true`.
- The active lifestyle review remains partial until human review fills
  dimension verdicts.

## Claim Ceiling

`Functional Subject post-repair lifestyle seed local/real-entry candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable real user benefit, live autonomy, durable memory efficacy,
runtime efficacy, a real 3-day lifestyle pass, or #94 closeout.
