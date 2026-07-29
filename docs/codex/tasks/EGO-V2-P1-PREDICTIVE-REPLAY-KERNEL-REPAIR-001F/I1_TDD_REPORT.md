# 001F I1 TDD and frozen-cycle report

## Verdict

`BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION`

The exact prewarm kernel repaired the fresh-process recovery-time boundary in
both consumed contexts and remained byte-identical to the callable scalar
ablation. The frozen cycle nevertheless failed because world 54's mean trace
size was `32847.16949152543B`, which is `79.16949152543B` above the preregistered
`32768B` limit. No threshold or post-result source change was made.

## Layer and route state

- Engineering implementation plus bounded old-context performance verification.
- `science_weight=0`.
- The current outcome-conditioned additive learning framing remains
  `CURRENT_OUTCOME_CONDITIONED_ADDITIVE_FRAMING_EXHAUSTED`.
- This result does not reopen or adjudicate the R4 learning mechanism.

## TDD sequence

1. The first focused RED run failed on the absent scalar reference, absent
   authenticated compact projection receipt, and absent compact candidate
   receipt (`3 failed, 1 passed`).
2. The exact-prewarm/receipt implementation made the focused suite green.
3. A second RED test required nonzero-offset batch rows to equal the scalar
   producer bit-for-bit; it failed because the batch producer did not yet exist.
4. The batch producer and depth prewarm then made the focused implementation
   suite `5 passed`.
5. The checker suite was written before the checker and failed `4 failed`; after
   implementation it passed `4 passed`.
6. The relevant predictor predecessor group passed `37 passed, 5 skipped` after
   replacing its implementation-coupled scalar-call count with a batch-call
   assertion and expanding the authenticated compact candidate receipt before
   comparison to the unchanged frozen fixture.

## Implemented callable changes

- Per-depth public prediction requests are prewarmed and evaluated in
  action-wise batches.
- The batch arithmetic has a callable scalar reference and a nonzero-offset
  bit-exact test.
- The trace-only candidate and delta-projection receipts use fixed-version,
  hash-authenticated, losslessly expandable encodings.
- The UI-visible candidate `total` remains directly available.
- The source-path scan now explicitly binds `predictive_control.py`.
- No controller, store, environment, world, metabolism, action, lifecycle, or
  UI source changed.

## Frozen performance results

| context | optimized dispatch total | scalar dispatch total | fresh recovery seconds | trace mean | trace max |
|---|---:|---:|---|---:|---:|
| world 52 / policy 711 | `7.709871499770088s` | `8.701676599914208s` | `6.896058099984657`, `6.661194299987983`, `7.228872200008482` | `32742.58695652174B` | `35359B` |
| world 54 / policy 711 | `10.28637799990247s` | `11.786265799892135s` | `8.832739200006472`, `9.009272199997213`, `8.774763699999312` | `32847.16949152543B` | `36327B` |

The optimized and scalar databases are byte-identical within each context, all
ordered command rows and trace rows are exact, and final states are exact. This
shows semantic equivalence for this frozen old-context cycle; it does not show
that the learning mechanism is useful.

## Replay, tamper, and row recomputation

- All six fresh-process full recoveries were exact and below 10 seconds.
- Controller startup, explicit recovery, load, export, same-process recovery,
  and online signatures agreed.
- Command, predictive-model, plan-prediction, and update-receipt rehash tamper
  controls were rejected in both contexts.
- A one-off read-only report-reading process (not a checked-in deliverable)
  recomputed 210 trace rows, the two trace means/maxima, recovery thresholds,
  scalar equality flags, and the final verdict from the banked artifacts. It
  reproduced the same failure exactly.
- This is only a second report-reading process operated by Codex, not an
  implementation-independent or external audit.

## Regression boundaries

- Focused implementation tests: `5 passed`.
- Checker tests: `4 passed`.
- Relevant predictor predecessor tests: `37 passed, 5 skipped`.
- These results use the repository-pinned runtime command
  `uv run --with-requirements requirements-ego-v2.txt ...`, which resolved
  Python `3.12.13` and NumPy `2.2.6`. The default host Python/NumPy is not an
  admissible substitute because `numeric_runtime_contract()` intentionally
  fails closed on a different NumPy version.
- A wider life/visual group produced `82 passed, 1 skipped, 6 failed`; all six
  failures are stale version literals (`state.v9`, `trace.v14`, or
  `code_path.v10`) against the already-live `state.v10`, `trace.v15`, and
  `code_path.v11`. The 001F diff does not change those global versions. No
  full-suite-green claim is made.
- An attempted all-`tests/` collection stopped on an unrelated missing
  `route_convergence_common` import in the K0 foundation test.

## Stop condition and next routing decision

The one formal 001F cycle has been consumed and banked. Because R3 and 001F are
two exact performance-route rounds that did not pass the complete frozen
boundary, the task-card stop condition freezes further post-result trace tuning
under this framing. Do not shave another 80 bytes and rerun the same card.

The next useful action is a new docs-only route/card decision: either retire the
raw-JSON mean-size instrument as an engineering proxy through an independently
justified boundary redesign, or separate trace storage/observability requirements
from learned-mechanism admission. Bayesian active identification must not run
until that governance decision is made; worlds 60--65 remain contaminated and
ineligible as fresh held-out worlds.

## Claim ceiling

At most: exact-equivalent old-context replay/performance engineering evidence
and a banked 79-byte mean-trace boundary failure.

This does not prove learning success, positive transfer, held-out adaptation,
survival improvement, neural self-formation, agency, AGI, consciousness, or
electronic life.
