# Call-chain audit

The exact reference must preserve the audited order:

`public observation -> exact posterior diagnostics -> selected action ->
microworld.transition_world -> engine.compute_actual_delta ->
engine.compute_metabolism_ledger -> terminal decision -> exact posterior update`.

The candidate input is exactly `observation`, `organism`, `last_action`, and
`last_delta`. The mapping commitment is used only by the evaluator to build and
score a world. World seed/layout/mapping/private pose, oracle action, packet
label, verdict and future fields must not enter candidate state or action calls.

The private-aligned diagnostic has no candidate state, is labelled evaluator
private, and is excluded from every public gate. This document will be extended
with executed function receipts after the run.

## Executed readback

- Every public exact-reference row called `microworld.policy_observation`, then
  `plan_exact_action`, then `microworld.transition_world`,
  `engine.compute_actual_delta`, `engine.compute_metabolism_ledger`, the energy
  terminal check, and finally `update_exact_posterior` in that order.
- Scratch and existing-public-Bayes rows called the canonical
  `homeostatic_transfer.plan_action` and
  `homeostatic_transfer.update_after_transition` in the same physical chain.
- The exact candidate wrapper was called on all and only the four declared
  exact-state arms. It was never called for `PRIVATE_ALIGNED_REFERENCE`.
- Public receipts contained only the four allowed fields. The independent
  verifier rebuilt the mapping posterior, entropy, Bayes errors, information
  gain and deficit AUC without importing the producer or product runtime.
- Rehashed private-field injection, rehashed entropy tamper, row-hash tamper and
  packet-assignment tamper positive controls were all rejected.
- No file under `labs/ego_life_playground_v0/` changed.
