# 001K call-chain audit

## Method

The audit did not rerun any 001J trajectory. It used three independent checks:

1. SHA-256 readback of all 14 frozen 001J task/source/artifact paths.
2. AST call-order inspection of the frozen 001J `run_trajectory` function.
3. A synthetic public-input state intervention on the frozen
   `PublicFactorBayes` object, plus aggregate inspection of already stored 001J
   rows.

## TDD evidence

- RED: the new audit test failed at collection because the 001K producer did
  not exist (`ModuleNotFoundError`).
- First CLI probe found an additional real entrypoint defect: running the file
  directly could not import the repository package. The repository root was
  added to `sys.path`; this changed only the task-local offline producer.
- GREEN: `2 passed` in the pinned NumPy 2.2.6 environment.

## Facts

- All frozen 001J hashes match their pre-campaign commitments.
- Frozen source order is:
  `reference.plan` -> `transition_world` -> `compute_actual_delta` ->
  `compute_metabolism_ledger` -> `reference.update`.
- A negative observed update changed the posterior state hash. Replanning from
  the same legal public payload read that exact updated state hash and changed
  the selected action from `interact` to `turn_right`.
- The stored 001J public arm contains 1,536 rows, 64 successful interactions,
  and 1,405 turn actions (`91.47%`).
- `orient_visible_token` accounts for 1,305 decisions.
- No stored 001J public trajectory identified all five token effects within 96
  actions.
- No original 001J heldout trajectory was executed by this audit.

## Mechanism judgment

The "posterior never reaches the planner" explanation is rejected for the
tested call path. Update, planner read, and final action selection are wired.

This does **not** prove the planner uses the posterior well. The strongest
remaining candidate is a geometry/target-selection defect: the legacy planner
turns whenever horizontal offset is nonzero, including front-diagonal targets,
and recomputes its target after every turn. That mechanism can create turn
oscillation even when the posterior is correct.

The strongest rebuttal is that sparse interactions may still originate from
insufficient public observability or unavoidable acquisition cost. The lowest
cost discriminator is therefore an evaluator-only correct-posterior
substitution with the legacy planner, followed by a geometry-only intervention
with the public posterior.

## Claim ceiling

This audit establishes local call-chain wiring and a stored action-distribution
diagnosis only. It is not evidence of positive public acquisition headroom.
