# Sole runtime call-chain audit

## Verified chain

`scripts/run_ego_life_playground_v0.py::main`
→ `PlaygroundController.dispatch`
→ `engine.compute_step`
→ public observation / candidate construction
→ optional homeostatic `plan_action`
→ existing `survival_learning.select_action` delegation receipt
→ `microworld.transition_world`
→ `engine.compute_actual_delta`
→ `engine.compute_metabolism_ledger`
→ terminal/lifecycle decision
→ homeostatic `update_after_transition`
→ existing model/memory bookkeeping
→ `SQLiteEventStore.append_step`.

Recovery uses `SQLiteEventStore.recover_run`, which starts from initial state,
recomputes every command through the same `compute_step`, and only then compares
the recomputed trace with stored trace bytes. Terminal and Tk views read
`RecoveryResult.frames` and trace; neither owns state-transition logic.

## Wiring evidence

- Planner receives only current public observation, energy/safety, previous
  action and previous observed energy/safety delta.
- The planner returns a selected action and per-action predictions/ranking.
- The canonical downstream selector receives a one-hot delegation surface and
  must return the same action; mismatch fails closed.
- Transition and metabolism happen before the learner update.
- Updated state is component-hashed, persisted in the trace chain and exactly
  recomputed on recovery.
- In the homeostatic mode, SARSA and factored MPC are forced off and their
  update counts remain zero.

## Alternate-runtime risk

`causal_sprout.py::CausalSproutRuntime` exists as a separate injectable demo
runtime but is not on the live launcher chain. This task does not import or
instantiate it. A future `runtime=` injection into the launcher would create a
semantic fork and must be rejected by regression audit.
