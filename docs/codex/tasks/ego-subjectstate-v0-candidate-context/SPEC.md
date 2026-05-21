# EgoOperator: SubjectState v0 Candidate Context

## Goal

Add `SubjectState v0` as a candidate-only context primitive for `EgoOperator`, carrying identity anchors, user preference cues, relationship continuity cues, commitments, consent boundaries, memory candidates, relationship update candidates, and policy patch candidates into the existing prompt/trace path.

## Scope

- Extend `EgoOperator/primitives/subject_context.py` with a bounded `SubjectState v0` record.
- Inject the record into the existing subject-context prompt block.
- Preserve `user text -> LLM understanding -> candidate response/plan -> gate -> trace`.
- Include current candidate-local self-name as an identity anchor.
- Add deterministic tests proving trace visibility, candidate-only boundaries, and one behavior-changing prompt effect.

## Non-Goals

- Do not write core memory, operator memory, program state, evidence ledger, or canonical task state from `SubjectState v0`.
- Do not make `SubjectState v0` decide final replies.
- Do not add keyword-first routing or template fallback.
- Do not modify legacy `EgoCore`, `OpenEmotion`, or `ego_desktop_lab`.

## Acceptance Gate

- `SubjectState v0` does not write core memory/state directly.
- Prompt/context and trace show the candidate context is present.
- At least one deterministic case shows behavior changes versus no `SubjectState`.
- Existing subject-context, permission, and runtime tests do not regress.

## Rollback

Remove the `SubjectState v0` builder, prompt field, runtime self-name wiring, tests, and local board status updates.

## Claim Ceiling

`SubjectState v0 candidate context local candidate pass`.
