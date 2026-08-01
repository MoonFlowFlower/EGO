# Call-chain audit requirement

The successor must retain the already-audited product ordering:

`public observation -> plan_action -> selected action -> microworld transition
-> metabolism/actual delta -> terminal decision -> update_after_transition`.

The dev-only evaluator may wrap the canonical within-world Bayesian state, but
it must call the same `homeostatic_transfer.plan_action`,
`microworld.transition_world`, `engine.compute_actual_delta`,
`engine.compute_metabolism_ledger`, and
`homeostatic_transfer.update_after_transition` functions in that order. It may
alter only the acquisition target/action after reading canonical public
predictions and its declared transfer statistic. The canonical product source
and default mode remain byte-identical.

The candidate receives only `observation`, `organism`, `last_action` and
`last_delta`. World seed/layout/mapping/pose, packet/split/verdict and future
fields remain evaluator-only. The latent-alignment upper-bound arm is explicitly
private and excluded from learner evidence.

## Executed readback

- All three candidates called the canonical planner before the candidate's
  acquisition-only ranking adjustment.
- Every actual transition and metabolism ledger completed before the canonical
  posterior update.
- The canonical slow consequence accumulator was scrubbed after every update;
  current-world fast token statistics remained real and updateable.
- Every public row recorded the four-field input receipt; the independent
  verifier found no leakage or trace-chain finding.
- No file under `labs/ego_life_playground_v0/` was modified by this task.

An adversarial wiring test found that the first diagnostic run sent shuffled
feedback to the canonical posterior but left the candidate's auxiliary fast
metadata keyed by the unshuffled entity. Those rows are preserved and marked
invalid as `HISTORY_SHUFFLE_FAST_META_PAIRING_BYPASS`. The fix consumes the
canonical update receipt's `updated_token`, and the same three preregistered
mechanisms were rerun under `history_shuffle_wiringfix`. This was a control-path
repair, not a fourth mechanism or threshold change. Qualification remained
unconsumed throughout.

A second hostile test rejected the embedded latent-alignment arm because its
private alignment had been placed in candidate state. Those private rows were
already excluded from gates and are now explicitly invalidated as diagnostics.
The corrected reference keeps candidate state `None`, calls the canonical fixed
planner through an evaluator-owned aligned reference state, and records
`candidate_wrapper_called=false`. It is reported only as an upper bound.
