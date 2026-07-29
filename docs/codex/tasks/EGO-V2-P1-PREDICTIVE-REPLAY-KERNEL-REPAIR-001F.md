# EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F

## Bounded task card and collision record

- **Problem definition:** the live V2 predictor still performs full fresh-process
  replay through the sole controller/engine/planner/persistence path, but the
  banked R2/R3 old-context evidence did not satisfy the frozen `<=10s` recovery
  boundary and `<=32768B` mean trace boundary. R4 also found inadequate
  outcome-stratum support and feature rank. Performance must be repaired before
  any successor learning mechanism can be adjudicated without weakening replay.
- **Prior negative evidence:** preserve 001A/001B/001C/R1/R2/R3/R4 and their
  verdicts. R3's archived tested patch improved timing but still failed the
  boundary and omitted three formal bindings: scalar/batch equivalence over the
  actually reached requests, lossless compact-receipt reconstruction, and
  inclusion of `predictive_control.py` in the single-path scan. R4 remains
  `INSUFFICIENT_OUTCOME_SUPPORT`.
- **Layer:** engineering implementation and bounded old-context performance
  verification; `science_weight=0`.
- **Current stage:** the current outcome-conditioned additive learning framing is
  frozen as `CURRENT_OUTCOME_CONDITIONED_ADDITIVE_FRAMING_EXHAUSTED`; the broader
  mechanism family is `MECHANISM_FAMILY_NOT_FALSIFIED`. This card repairs reusable
  runtime/replay infrastructure only and does not reopen the additive result.
- **Hypothesis:** after a measurement-only profile, exact hoisting, batching, and
  reuse of prediction requests within each deterministic beam depth can reduce
  fresh-process recovery time and trace size while leaving every public input,
  scalar prediction, node ordering, chosen action, update, final state, model
  hash, and replay hash unchanged.

## Collision-before-collapse comparison

### Candidate 1 — archived R3 patch unchanged (minimal)

- **Evidence produced:** previously measured partial speed and trace-size gains.
- **Strongest cheap match:** the archived R3 result itself.
- **Leakage/hard-coding risk:** low label leakage, but incomplete provenance can
  make an approximate or lossy route appear exact.
- **Smallest falsifier:** world 54 remains over 10 seconds or any of the three
  missing formal bindings fails.
- **Expected failure:** already observed; world 54 remained approximately
  `11.89--12.45s` and mean trace remained above 32768 bytes.
- **Decision:** rejected as insufficient, retained only as negative evidence and
  an implementation clue.

### Candidate 2 — stored-plan/checkpoint recovery (shortcut baseline)

- **Evidence produced:** low replay wall time.
- **Strongest cheap match:** direct database/state restoration.
- **Leakage/hard-coding risk:** extreme; it bypasses fresh planner recomputation
  and can conceal a disconnected learned path.
- **Smallest falsifier:** delete the stored plan/checkpoint and require the same
  action/trace from serialized state plus observation.
- **Expected failure:** fast timing without causal replay evidence.
- **Decision:** rejected.

### Candidate 3 — profile-led exact beam prediction kernel (selected)

- **Evidence produced:** callable before/after profiles, exact scalar/batch
  equality, unchanged planner/update/replay outputs, and lossless compact trace
  receipts.
- **Strongest cheap match:** scalar planner with identical model, state,
  observation, node ordering, and archived databases.
- **Leakage/hard-coding risk:** cache keys that omit a public state component,
  approximate vector arithmetic, test-only fast paths, or trace fields silently
  dropped rather than reconstructable.
- **Smallest falsifier:** one reachable request differs bit-for-bit, one node or
  action changes, the receipt cannot reconstruct its committed evidence, or the
  old-context boundary still fails.
- **Expected failure:** Python beam expansion or hashing—not prediction math—may
  dominate, leaving insufficient headroom.
- **Decision:** selected because it alone preserves the evidence-generating path
  while attacking the measured cost.

## Frozen implementation contract

- **Real path:** no second product path. Fresh recovery remains
  `PlaygroundController.dispatch -> engine.compute_step ->
  predictive_control.plan_action -> transition/metabolism -> SQLite commit and
  recovery`.
- **Profile first:** profile only already-consumed copied databases from worlds
  52 and 54, policy seed 711. Profiling cannot mutate canonical banked databases.
  The implementation must address measured hotspots; an unmeasured speculative
  rewrite is forbidden.
- **TDD:** add RED tests before source changes for reached-request scalar/batch
  exactness, cache-key completeness, planner/node/action equality, lossless trace
  reconstruction, single-path scan coverage, and failure on corrupted receipts.
- **Baseline:** live scalar predictor/replay at this card's parent commit, on
  byte-identical copied old-context databases and identical process/runtime
  settings.
- **Ablations:** disable the optimized kernel and execute the scalar route;
  disable compact projection and produce full evidence; corrupt/remove one
  compact source field and require reconstruction failure.
- **Performance verification:** development diagnostics may run only on already
  consumed worlds 52/54 and policy seed 711. A frozen formal old-context cycle is
  allowed only after focused tests and exactness checks pass. Require three fresh
  processes per context, each exact and `<=10s`; trace mean `<=32768B`, trace max
  `<=65536B`; no threshold, horizon, beam, feature, learning-rate, or model change.
- **Replay:** recompute through the actual planner from serialized state and
  public observation. Stored action/plan/checkpoint trust is forbidden. Compare
  final state, event/action sequence, model/update count, trace hashes, and all
  designated replay receipts.
- **Provenance:** every timing row records producer function, input database hash,
  run id, world/context/policy identity, aggregation rule, implementation/code
  path hashes, Python/NumPy versions, process mode, and baseline/ablation route.
  The single-path scan must include `predictive_control.py`.
- **Acceptance:** `PREDICTIVE_REPLAY_KERNEL_BOUNDARY_REPAIRED` only if exactness,
  all performance/trace gates, independent row-level recomputation, failure-path
  tests, and ablations pass. Any semantic mismatch is an immediate hard failure.
- **Stop conditions:** bank `BLOCKED_EXACT_KERNEL_EQUIVALENCE` on any semantic
  drift; bank `BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION` if the one frozen cycle
  misses timing/trace; no second threshold-tuning attempt. If another exact
  kernel round fails, freeze this performance route and re-examine the boundary
  or runtime architecture under a new card.
- **Rollback:** reverse only uncommitted 001F implementation hunks. Never rewrite
  or mutate prior task cards, artifacts, banked rows, databases, results, or
  verdicts.

## Scope and firewall

- **Allowed paths:**
  - this task card;
  - `labs/ego_life_playground_v0/predictive_control.py`;
  - only if needed for lossless trace receipts,
    `labs/ego_life_playground_v0/engine.py`;
  - `tests/test_ego_life_playground_v0.py` and focused new tests under `tests/`;
  - `tests/test_ego_v2_factored_predictive_control_boundary_gate_001c.py`,
    limited to replacing implementation-coupled scalar-cache assertions with
    exact prewarm/batch assertions and expanding the authenticated compact
    candidate receipt before comparison to the unchanged frozen fixture;
  - one new checker and its tests under `scripts/codex/`;
  - `docs/codex/tasks/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/` reports;
  - new artifacts only under
    `artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/`.
- **Forbidden:** controller/store/world/environment/metabolism/action/lifecycle/UI
  changes; route-state mutation; hidden labels, mappings, coordinates or seeds;
  network/LLM; a test-only execution route; changing any prior artifact; held-out
  execution; push or tag.
- **Held-out firewall:** worlds 30--150, including 60--65, have lineage-private
  mapping exposure and are permanently ineligible for a fresh canonical claim.
  Policy seeds 721/722 do not cure contaminated world IDs. A future effect card,
  if ever authorized, must use externally selected, commitment-hashed opaque
  worlds wholly greater than 150 after implementation, priors, thresholds, and
  the development verdict are frozen.
- **Successor learning order:** after this card only, a separate bounded
  old-context admission card may compare Bayesian active identification with an
  equal-access `PUBLIC_COUNT_DEFICIT_COVERAGE` control on worlds 52/54. No
  held-out effect execution is authorized here.
- **Claim ceiling:** exact-equivalent old-context replay/performance engineering
  evidence only. No prediction-learning success, survival effect, held-out
  adaptation, neural self-formation, agency, AGI, consciousness, or electronic
  life claim.
- **Auto-Remote-Anchor:** forbidden.

## I1 scope clarification

The first RED/green cycle established that the predecessor boundary test
directly counted calls to the scalar `_prediction_for_pose` implementation and
read the trace-only candidate projection as if it were the full planner object.
Those assertions reject the selected exact prewarm mechanism by construction.
The narrow predecessor-test path above is therefore admitted before the source
implementation commit. This clarification does not change any fixture, metric,
threshold, context, seed, runtime semantic, or acceptance condition.
