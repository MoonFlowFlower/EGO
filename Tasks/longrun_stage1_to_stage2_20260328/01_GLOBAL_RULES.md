# Global Rules

## Purpose

This batch exists to close `MVP11.5 readiness` and produce a formal `Stage 2` admission decision.

## Hard Boundaries

- Do not advance to `Stage 3 / MVP12` in this batch.
- Do not treat shadow or partial artifacts as phase pass.
- Do not use old stale commands when a current repo-backed test or artifact path exists.
- Do not skip `Independent Reviewer -> Verifier` on required steps.
- Do not update truth sources to claim `Stage 2` unless admission review passes.

## Authority Priority

1. `EgoCore/docs/PROGRAM_STATE_UNIFIED.yaml`
2. `OpenEmotion/roadmap/ROADMAP_STATE.json`
3. `OpenEmotion/roadmap/versions/*.spec.yaml`
4. `OpenEmotion/artifacts/handoff/LATEST_HANDOFF.md`
5. `README.md`

## Verification Contract

- Minimum verification level for local code/report changes: `V1-V2`
- Minimum verification level for `ready / promote` claims: `V4`
- Minimum evidence level for `Stage 2 promoted`: `E4`
- A negative readiness decision (`not_ready` / `stay_stage1`) may be recorded at `V3 / E3` if it is directly backed by the current rerun artifacts and criteria mapping.

## Default Output Contract

Every step report must state:

- what changed
- what self-review found and fixed
- what verification ran
- what is still unproven
