# Collision record — EGO-V2-P1-ADDITIVE-PLANNER-BOUNDARY-001C-R3

## Collision

R2 preserved exact replay and improved R1's recovery times, but not enough:
all six fresh recoveries exceeded 10 seconds and both trace means exceeded
32,768 bytes. The balanced stage was correctly blocked. Profiling a copy of
the banked world-54 database reconstructed 118 commands and located the main
remaining conditional cost in 196,075 scalar calls to
`_planning_prediction_vector_from_packed` (`6.461s` cumulative under profiler
overhead). A scalar arithmetic rewrite remained exact but still took
`13.18--13.51s`; a cross-step cache had only 18,645 hits against 177,430
misses and took `14.07--14.68s`. Those diagnostics reject another local scalar
or dictionary-cache patch.

## Candidates

| Candidate | Evidence | Strongest objection | Smallest falsifier |
|---|---|---|---|
| Raise 10s/32KiB thresholds or use checkpoints | Green-looking boundary | Weakens the frozen replay/provenance contract | Original R2 gate still fails |
| Remove outcome conditioning from simulated nodes | Near-001C speed | Severs conditioning from the action-ranking causal path | Residual ablation cannot affect planning |
| Exact depth prewarm/batch plus lossless trace compaction | Same scalar predictions and smaller trace | Batch arithmetic may alter floating order/ties | Exact tuple, plan, node, action, trajectory and recovery comparisons |

## Selection

Select exact depth prewarming/batching. It changes representation of
computation, not the learned model or policy objective. Per-row softmax remains
the frozen scalar implementation; only the six-outcome additive expectation is
vectorized across independent requests, using the same explicit outcome
addition order. Every emitted tuple must equal the scalar path exactly.

Compact only redundant projection receipts: keep per-state means, aggregate
raw/projected hashes, maximum difference and all-preserved. The full update
report remains callable; compact trace bytes are not the only source of truth.

## Stop boundary

No fresh seed, parameter, metric or threshold changes are allowed. Any exact
equivalence failure closes the batch candidate. Any formal boundary failure is
banked without another rescue patch under this card. A pass would only unlock
the already-frozen old-context balanced gate, not a held-out effect claim.
