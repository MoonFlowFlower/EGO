# EgoDesktop PSPC Perception Demo v0 Acceptance

## Acceptance

- A local EgoDesktop viewer can play four deterministic PSPC perception scenarios.
- The same trigger `我回来了。` is displayed for every scenario.
- The four histories produce visibly distinct presentation-only reactions:
  - gentle history -> warm approach
  - frequent interruption -> cautious boundary
  - late-night care -> low-interrupt care
  - mixed history -> hesitation / low confidence
- Debug overlay is hidden by default and exposes only audit fields.
- Recording mode has fixed window size, deterministic timing, deterministic order, and seeded deterministic motion.
- EgoOperator runtime, gate, memory, approval, transport, proactive behavior, and human-trial harness are not modified.
- No adapter is created.
- Reports state what this proves and what it does not prove.

## Required Tests

- `node --test EgoDesktop/tests/pspc_perception_demo.test.js`
- `npm test` inside `EgoDesktop`
- EgoDesktop smoke with `--pspc-recording-mode`
- repo integrity and closeout checks

## What This Proves

It proves a local presentation layer can replay PSPC proposal-hint histories as different visible Live2D companion behaviors for a human perception review.

## What This Does Not Prove

It does not prove PSPC is integrated into EgoOperator, adapter readiness, runtime integration safety, EgoOperator efficacy, real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, real emotion, or market fit.

## Failure Meaning

Failure means this visual demo is not ready for human perception review. It does not invalidate the earlier PSPC shadow artifacts, but PSPC should remain artifact-only or visual-shim-only until the presentation layer is fixed.
