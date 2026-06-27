# EgoDesktop Joi Real-Loop G-ABLATION Captured Calibration Reference v0 Plan

1. Add task card, mutation scope, and task-board entry.
2. Send the card to desktop Claude for review before implementation.
3. Repair card-level blockers before implementation:
   - freeze a predeclared calibration prompt pack before capture and build the split partition manifest against it;
   - add disjointness assertions and overlap-positive control;
   - define captured calibration as fixed output schedule replay, not captured state reuse;
   - require calibration row capture through the existing 006 tap / real sendChatTurn path;
   - add must-fire positive controls for synthetic fallback, synthetic kind, split overlap, and captured-calibration
     shuffle/invariance.
4. Record Claude `NO_BLOCKING_FINDINGS` source-limited review for the repaired card.
5. Add failing tests for:
   - rejecting heldout-only input as a calibration source;
   - rejecting calibration/heldout split overlap;
   - rejecting synthetic calibration fallback and `synthetic_reference` kind;
   - building a calibration reference from captured calibration trace-row input;
   - ensuring the heldout replay builder consumes that reference and no longer emits `synthetic_reference`;
   - proving heldout output is invariant to heldout-observation shuffle and non-seed calibration-state mutation;
   - preserving evaluator precondition pass with `scoring_run_authorized=false`.
6. Add the minimal calibration-reference module and CLI.
7. Update the existing offline replay builder to accept a required calibration-reference artifact for the 009 artifact.
8. Build the calibration reference and rebuilt heldout row, then run the evaluator precondition.
9. Update status/task board and regenerate route-convergence views.
10. Run focused tests, `npm test`, repo fast verify, and scoped closeout.
11. Sent Claude the B-009-IMPL-1 implementation repair packet.
12. Claude returned `NO_BLOCKING_FINDINGS (source-limited)` for the repair; mark accepted, commit locally only, and send
    Claude a commit readback.

## Non-Goals

- No `CREATURE_ON` row.
- No baseline scoring, threshold freeze, same-access reproducer execution, or verdict.
- No route, attribution, readiness, product, agency, emotion, subjectivity, consciousness, alive-status, or Bar-2 claim.
- No default EgoDesktop runtime enablement.
- No program-state or evidence-ledger update.
