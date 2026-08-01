# EXPLORE — EGO V2 homeostatic survival loop 001L

## Current framing

The unknown is no longer whether legal public feedback contains any learnable
signal. 001K established that bounded fact. The unknowns are (a) how robustly
the frozen acquisition/planning mechanism clears the original gate across
packets, and (b) whether the same mechanism is correctly wired into the sole
runtime without being replaced by an animation or second reducer.

## E0 — preflight

- Hypothesis: the product path already has suitable selector/update/reset/
  replay seams, but no legal-public homeostatic reference mode.
- Kill criterion: insertion requires a second controller/store/replay or a
  change to observation/action/world grammar.
- Minimal experiment: AST/call-chain audit plus a synthetic update -> planner
  read -> downstream selected-action test.
- Observation: launcher, terminal and Tk all route through
  `PlaygroundController.dispatch -> engine.compute_step -> store.append_step`,
  while recovery recomputes `compute_step` before comparing stored traces.
  `causal_sprout.py` is a separate injectable demo runtime and is not on this
  launcher path.
- Decision: connect only inside the canonical reducer; do not reuse the
  injectable demo runtime or its behavior engine.
- Status: call-chain hypothesis supported; implementation proof pending.

## E1 — failing contract tests

- Hypothesis: a clean public-state module plus one mutually exclusive reducer
  selector is sufficient for update/read/final-action wiring and reset tests.
- Change: added focused tests for leakage, drive intervention, reset semantics,
  mutual exclusion, downstream selection and state tamper rejection.
- Preregistered prediction: collection fails because the module does not yet
  exist; after implementation the same tests must pass without a second reducer.
- Observation: pytest failed at import exactly as predicted.
- Implementation result: the JSON-only reference, reset semantics, public
  scanner, drive intervention and reducer delegation tests now pass (`7
  passed` including SQLite recovery and HTML rendering).
- Decision: the canonical reducer seam is sufficient; proceed to bounded
  runtime observability and R evidence rather than creating another engine.

## E2 — runnable product vertical slice

- Hypothesis: the default-off mode can run through terminal, SQLite persistence,
  replay and trace views while SARSA and factored MPC remain inactive.
- Change: added mutually exclusive `public_bayes` mode, public consequence
  update, death reset receipt, terminal/Tk projections, explicit launcher flag
  and trace-only HTML renderer.
- Preregistered prediction: 12 terminal steps commit; homeostatic update count
  becomes 12; SARSA and factored MPC update counts remain zero; recovery
  reproduces hashes.
- Observation: all predictions held. Direct explicit launch completed and the
  terminal exposed deficits, per-action predictions, actual outcome/delta,
  posterior/slow/fast hashes, selection reason and update count.
- Limitation: this proves wiring and observability, not positive transfer or R
  robustness.
- Decision: keep the mode default-off and move the research lane to the single
  robustness successor.

## R hypotheses

Packet denominator composition, unsafe acquisition scheduling, and navigation
reacquisition are the three candidate variance mechanisms. Stored rows are
analyzed before any new algorithm. Maximum two substantive candidates and no
post-qualification tuning.

## R0 — stored-row diagnosis and failing successor tests

- Stored 001K evidence: late first beneficial interaction and high turn
  fraction are negatively associated with public gain; the clearest witness is
  `001k-replication-0013`, which eventually reaches sign accuracy 1.0 but
  discovers beneficial effects late and oscillates around a known harmful
  front token.
- Strongest alternative: the recovery denominator alone changed. This is
  incomplete because public loss and navigation traces also worsen on the same
  slices.
- Frozen candidates: stateful `S4_HARM_ESCAPE` and stateless
  `S4_UNSEEN_FRONTIER_PRIORITY`, both generic public-history mechanisms; the
  unchanged 001K candidate is only a carry-over control.
- Failing tests: packet/protected-hash audit, two-candidate budget, public-only
  escape and verifier positive controls fail at import because no 001L producer
  or verifier exists yet.
- Implementation readback: the producer now exposes only the unchanged control
  plus the two preregistered mechanisms; focused tests prove packet commitments,
  protected predecessor hashes, public-input rejection, and the known-harm
  frontier action. The separately authored verifier imports no producer code
  and declares row, aggregate, assignment, leakage, and protected-file positive
  controls (`4 passed`).
- Decision: commit the complete producer/verifier before any search result is
  visible, then run the new search packet once for candidate selection.

## R1 — search-dev readback and freeze

- Single changed layer: navigation behavior after a harmful token has been
  learned; posterior update, effect scoring, world grammar, observations,
  actions and budgets remained unchanged.
- Carry-over control: gain `0.297833333334`, recovery `0.536899896957`, `16/16`
  positive worlds, mean harmful-loop maximum `10.875`.
- `S4_HARM_ESCAPE`: gain `0.327131510417`, recovery `0.589715302409`, `16/16`
  worlds, harmful-loop maximum `2.75`; both preregistered improvements held.
- `S4_UNSEEN_FRONTIER_PRIORITY`: gain `0.31478125`, recovery
  `0.567451664316`, `16/16` worlds and earlier beneficial discovery, but its
  harmful-loop diagnostic worsened to `23.25`.
- Decision: the preregistered ranking selects `S4_HARM_ESCAPE`. Producer,
  independent verifier, selected config, NumPy `2.2.6`, action budget, seeds,
  thresholds and both formal packet hashes are frozen. Qualification has not
  yet been consumed.
