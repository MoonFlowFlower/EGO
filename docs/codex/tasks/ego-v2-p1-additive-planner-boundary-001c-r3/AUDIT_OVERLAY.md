# R3 hostile-audit overlay

## Controlling interpretation

This overlay does not rewrite any byte of the formal diagnostic packet.  It
records the narrower interpretation required by post-run statistical,
data-flow, and final read-only review.

```text
formal_gate_classification: INVALID_FORMAL_GATE
diagnostic_classification: BANKABLE_BOUNDED_NEGATIVE_DIAGNOSTIC
reported_verdict_preserved: BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION
accepted_implementation: false
formal_cycle_count: 1
balanced_stage: not_run_boundary_failed
fresh_effect_seeds_consumed: false
eligible_for_separate_effect_card: false
```

## What the diagnostic actually established

The tested, uncommitted R3 build used only worlds 52/54 and policy seed 711.
All six fresh-process recoveries were self-replay exact, all existing rehashed
tamper controls rejected their mutations, and independent SQLite row-level
recomputation reproduced every trace hash, trace-chain link, mean size, and
maximum size.

The frozen engineering boundary still failed:

| World | Fresh recovery seconds | Trace mean | Trace max |
|---|---|---:|---:|
| 52 | `9.9678454`, `9.8390975`, `9.9962901` | `33,508.8696B` | `36,161B` |
| 54 | `12.4508154`, `11.8863512`, `12.2358326` | `33,619.1441B` | `37,129B` |

Consequently world 54 did not satisfy three recoveries at `<=10s`, and
neither context satisfied trace mean `<=32,768B`.  The balanced stage was
correctly skipped and no fresh-effect seed was consumed.

Relative to the banked R2 observations, R3 reduced recovery medians from
`10.6502s` to `9.9678s` on world 52 and from `14.2467s` to `12.2358s` on
world 54; trace means fell by approximately `841B` and `847B`.  This is a
bounded diagnostic comparison, not a controlled causal performance estimate,
and it did not meet the acceptance boundary.

## Why the formal gate is invalid/incomplete

1. The formal verifier checked batched online execution against batched fresh
   replay.  It did not compute or bind an actual old-context differential
   against the frozen R2 scalar planner.  Therefore `exact=true` proves
   new-code self-replay, not scalar-versus-batch semantic equivalence.
2. The single-product-path AST scan did not include `predictive_control.py`.
   Manual review found no hidden input, checkpoint, stored-plan shortcut, or
   second reducer, but the automated evidence did not cover the changed
   planner file.
3. The compact projection receipt was described as lossless, but it omitted
   per-state fields and cannot reconstruct the source receipt.  It is only a
   hash-bound compact summary.

The private balanced evaluator did validate the smoke context manifest and
read the actual policy/world seeds from SQLite through
`_assert_db_context_allowed`; post-run review therefore found no fresh-seed
firewall defect in that path.

Focused tests and a same-model read-only diagnostic found the batch arithmetic
low risk and bit-exact on sampled rows, but that does not repair the missing
formal old-context differential.  The literal `scalar_equivalence_contract`
field was not a computed result.

## Provenance and rollback disposition

The exact tested source, verifier, relevant tests, and dependency files are
preserved in:

```text
artifacts/EGO-V2-P1-ADDITIVE-PLANNER-BOUNDARY-001C-R3/tested_implementation_bundle.zip
SHA-256: 947f66d9bbc91e753d1f073b8c2b372b6e683c8ea814aeb9c995143a48c1104b
```

The tracked diff is preserved as:

```text
artifacts/EGO-V2-P1-ADDITIVE-PLANNER-BOUNDARY-001C-R3/tested_tracked_diff.patch
SHA-256: 0fc421734dd183ea0281f4e7ed5722e9db0a488364c7b4058ebfaf475401d550
```

`provenance_closeout.json` binds the original formal packet bytes, per-file
source hashes, code-path hashes, bundle, patch, one formal command, independent
row-level recomputation, and validity defects.  After those bytes were frozen,
the unaccepted R3 source/test/verifier changes were removed from the active
tree.  The branch therefore banks documentation and artifacts only; it does
not leave the failed candidate active.

## Review independence boundary

The statistical, data-flow, hostile, and final read-only reviews were role
separation within one model collaboration tree.  They are not external
independent audits.

## Claim ceiling

This packet supports only the statement that the exact archived, uncommitted
R3 build failed the recovery-time and trace-mean boundaries on already-used
development contexts.  It does **not** establish R2-scalar equivalence,
balanced prediction improvement, held-out adaptation, survival benefit,
mechanism failure, AGI, agency, consciousness, or electronic life.
