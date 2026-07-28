# EGO-V2-P1-ADDITIVE-PLANNER-BOUNDARY-001C-R3

## Bounded task card

- **Problem definition:** R2 reduced the conditional delta model from 1,800
  to 420 weights and preserved six exact fresh-process recoveries, but it did
  not restore the frozen product boundary. World 52 recovered in
  `10.567--11.448s`, world 54 in `13.813--14.524s`, and trace means were
  `34,349.6/34,465.8B`. The balanced stage correctly did not run. A read-only
  R2 profile attributes `6.461s` under profiler overhead to 196,075 scalar
  conditional-delta evaluations inside the fixed beam.
- **Prior negative evidence:** preserve all 001A/001B/001C/R1/R2 results.
  R2 verdict remains `BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION`; it is not a
  repair PASS and no fresh-effect seed was consumed.
- **Layer:** engineering implementation and bounded learning-path performance
  verification; `science_weight=0`.
- **Current stage:** successor of local commit
  `363f6d49cbd54524ce283e7580e23c45ada4b532` on branch
  `codex/ego-v2-additive-planner-boundary-001c-r3`.
- **Hypothesis:** prewarming each beam depth's unique public prediction
  requests and vectorizing only the additive conditional expectation across
  those requests can remove per-request NumPy allocation overhead without
  changing a single scalar prediction, node, action, or model update. Compact
  trace projection evidence can retain its hashes, means, maximum numeric
  difference and all-preserved flag below the existing trace threshold.
- **Three candidates:** relax thresholds/checkpoint recovery (rejected as an
  evidence downgrade); one more scalar/cache micro-optimization (rejected by
  R2 read-only scalar/cache prototypes); exact depth batching plus lossless
  compact receipts (selected, with exact scalar equivalence as hard gate).
- **Baseline:** unmodified R2 scalar planner on identical serialized R2 model,
  observation, organism, beam requests, and archived old-context databases.
- **Ablation:** disable depth prewarming and call the scalar planner; expand
  compact projection receipts back from their source report in tests and
  verify the preserved fields/hashes.
- **Real path:** no new product path. `controller.dispatch ->
  engine.compute_step -> plan_action -> transition/metabolism -> SQLite`
  remains the sole online and replay path. Stored plans/checkpoints are never
  inputs.
- **TDD contract:** RED tests precede code for batch-vs-scalar exact tuples,
  exact plan/node/trajectory receipts, cache prewarm coverage, and compact
  projection receipts. Fail on any scalar/batch inequality, node ordering
  change, or missing projection evidence.
- **Performance gate:** only already-consumed worlds 52/54 and policy seed 711.
  First use copies of banked R2 databases for exact diagnostic recovery. Then
  run exactly one formal R3 boundary cycle: three fresh processes per context,
  every recovery exact and `<=10s`; trace mean `<=32768B`, trace max
  `<=65536B`; all existing dispatch/size/tamper/single-path gates unchanged.
- **Balanced gate:** only if the performance gate passes, reuse the frozen R2
  outcome-stratified support/rank, callable legacy/no-update, base-only,
  residual-only, outcome-rotation, leakage and subprocess-recompute gates.
  Do not change the model, LR, support floor, metrics, or thresholds.
- **Provenance:** batch producer records request count, unique cache misses,
  scalar-equivalence result and implementation hash. Trace compact receipt
  records projection mean by state, aggregate raw/projected hashes, maximum
  absolute difference and all-preserved flag.
- **Fresh firewall:** worlds 60--65 and policy seeds 721/722 are forbidden;
  the CLI accepts only `--gate` or private old-context recomputation.
- **Acceptance:** positive only if all performance and balanced gates pass.
  `fresh_effect_seeds_consumed=false` always;
  `eligible_for_separate_effect_card=true` only on full development PASS.
- **Stop condition:** after one frozen formal R3 cycle, stop and bank failure
  if runtime/trace remains blocked, any exact equivalence breaks, or balanced
  support/effect fails. Do not change threshold, horizon, beam, feature set,
  clip, LR, value weights, seeds, or model parameters after seeing results.
- **Rollback:** reverse only uncommitted R3 hunks; never rewrite R2 or older
  commits/artifacts.
- **Allowed files:** this card/collision record;
  `predictive_control.py`; minimal `engine.py` trace/code-path schema pins;
  focused tests; one R3 verifier/test; new R3 artifacts.
- **Forbidden:** controller/store/world/metabolism/action/lifecycle/UI changes,
  mainline/route state, old artifacts, hidden labels, network/LLM, checkpoint,
  stored-plan replay, fresh seeds, push or tag.
- **Claim ceiling:** at most exact-equivalent planner/trace engineering plus
  measured old-context prediction evidence. No held-out adaptation, survival
  effect, neural self-formation, agency, AGI, consciousness or electronic-life
  claim.
- **Auto-Remote-Anchor:** forbidden.

## Verdicts

- `ADDITIVE_PLANNER_BOUNDARY_REPAIRED_ON_DEVELOPMENT_CONTEXTS`
- `ADDITIVE_PLANNER_BOUNDARY_NO_DELTA_IMPROVEMENT`
- `INSUFFICIENT_OUTCOME_SUPPORT`
- `BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION`
- `BLOCKED_EXACT_BATCH_EQUIVALENCE`

