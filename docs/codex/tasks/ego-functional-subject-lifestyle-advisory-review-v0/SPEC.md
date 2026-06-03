# EgoOperator: lifestyle three-session advisory review v0

## Problem Reframe

EGO-FS-110 created a current review packet and one decision template per active
session. The remaining gate is reviewer verdicts. Codex must not clear
`requires_human_review`, but it can inspect the raw transcript/trace evidence
and produce a non-authoritative advisory review to reduce reviewer load.

This is not another helper-tool task. It is a first-pass evidence interpretation
over the existing three-session packet.

## Hypothesis

If Codex produces an explicit advisory verdict map with evidence excerpts and
counterexamples, the human/reviewer can fill the decision JSON files faster,
while canonical review authority stays unchanged.

## Change Surface

- Read the three active lifestyle seed transcripts and trace evidence.
- Produce `ADVISORY_REVIEW.md` and `advisory_review.json` with recommended
  verdicts.
- Keep all recommendations advisory-only.
- Do not mutate active trial state, clear review flags, or close #94.

## Do Not Change

- Do not modify EgoOperator runtime behavior.
- Do not modify `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Do not modify `artifacts/evidence_ledger/**`.
- Do not modify legacy EgoCore/OpenEmotion/ego_desktop_lab.
- Do not edit the three session decision JSON files as signed reviewer output.
- Do not clear `requires_human_review`.
- Do not close EGO-FS-010/#94.

## Acceptance

- Advisory review covers all three active sessions.
- Advisory review covers all required dimensions:
  self-name stability, relationship continuity, emotion understanding,
  subjective preference, bounded initiative, bounded non-obedience, feedback
  adaptation, and exit recovery.
- Advisory review separates positive evidence from counterexamples.
- Advisory review explicitly marks `exit_recovery` unknown if not tested.
- Active review remains partial and human-required.
- `Tasks/TASK_BOARD.yaml` and pursue-goal records point to the advisory review
  and the next signed-decision step.

## Claim Ceiling

`Functional Subject lifestyle advisory review local workflow candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable real user benefit, live autonomy, durable memory efficacy,
runtime efficacy, a real 3-day lifestyle pass, signed reviewer verdicts, or #94
closeout.
