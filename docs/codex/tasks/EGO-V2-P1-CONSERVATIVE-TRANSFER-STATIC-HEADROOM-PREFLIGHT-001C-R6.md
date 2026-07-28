# EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6

## Bounded task card

- **Task type:** seed-free, source-history-free, static exhaustive feasibility
  preflight before product-path implementation.
- **Layer:** bounded mechanism-hypothesis preflight plus evidence-instrument
  engineering; `science_weight=0`.
- **Repository:** `D:\Project\AIProject\MyProject\Ego`.
- **Branch:** `codex/ego-v2-conservative-transfer-reference-001c-r6`.
- **Base commit:** `603415f163ca1bccfd38d662570d1a717958ce80`.
- **Normative predecessor:** R5 commit
  `603415f163ca1bccfd38d662570d1a717958ce80`, with exact hashes:
  - card `d9bef189de2d62f157fafcf44874940cdf41a1997c51d4ebbfe27e7d094fbc53`;
  - collision `44d76988be7269201ff606c16c7813f634ee0afa7b3dff676e7fedc2c8962c1a`;
  - design `07abe6caadce1f7b76cfeee051b5d62c63a11f0f115e912e09c89eea42296443`.
- **Lineage discontinuity:** this preflight does not edit, rescore, repair, or
  promote R4/R5 evidence.  It checks a mathematical precondition that R5 itself
  required before candidate implementation.

## Why this card replaces the attempted implementation start

The requested next action was to implement the frozen R5 finite reference.
Before production code, the statistical role found a possible contradiction:
the frozen lower-5% scratch-relative benefit gate may reject every non-scratch
budget-2 prediction across the complete admissible six-source prior space.  An
independent root re-enumeration reproduced zero positive cases.

R5 explicitly says to stop before implementation if the exact reference lacks
encounter headroom.  Continuing to wire navigation/controller/replay after this
warning would optimize a mechanism already known to be unable to meet its
primary Stage-1 endpoint.  This card therefore freezes and independently
recomputes that precondition before any product-path source change.

## Problem definition

At feedback budget two, enumerate every posterior weight state attainable from:

- all `5! = 120` public prototype mappings;
- any multiset of six anonymous source mappings;
- frozen family masses `1/3` scratch, `1/3` source reuse, `1/3` one-swap local;
- the frozen exact 0/1 likelihood after two distinct successful token rows;
- frozen six-decimal BMA predictions;
- the frozen posterior-weighted lower-5% benefit gate with scratch fallback.

Determine both (a) whether any target/source state can produce positive
budget-2 endpoint MAE improvement over structure-matched scratch and (b)
whether a **true-analogy-constrained** state, in which the exact target mapping
occurs at least once in the six-source multiset, can reach the frozen minimum
required improvement `0.021875`.  The unconstrained maximum is a stronger
negative diagnostic only; it cannot by itself authorize a positive return.

## Hypothesis and falsifier

- **H1:** at least one admissible **true-analogy-constrained** six-source state
  and target mapping yields a gated budget-2 improvement of at least `0.021875`
  over scratch.
- **Falsifier:** complete enumeration returns zero positive gated cases or a
  true-analogy-constrained maximum below `0.021875`.  If the unconstrained
  superset maximum is also zero, report that strictly stronger no-go fact.

If falsified, verdict is `CONSERVATIVE_TRANSFER_NO_LEGAL_HEADROOM` and R6
product-path implementation must stop.  Thresholds, priors, quantile, budget,
or pass rule may not be changed under this card.

## Baseline

Structure-matched scratch has uniform mass over all 120 mappings and, after two
exact observations, uniform conditional mass over the six consistent mappings.
It uses the same five public prototype vectors, six-decimal half-even rounding,
and equal-weight `5 tokens x 4 components` MAE endpoint.

## Ablation

The only adjudicative ablation is the frozen gate itself:

- report whether a nontrivial transfer BMA prediction is ever accepted;
- do not use an ungated or retuned result to rescue H1;
- a future prospective design revision may evaluate alternative Bayes-risk or
  robust-decision rules only under a separate frozen task card.

## Exact finite arithmetic

### Frozen anonymous prototype geometry

This source-history-free checker does not infer or choose prototype geometry.
It freezes the exact five public mechanism-increment vectors used by the R5
endpoint, excluding common interaction base `[-18000,0,0,0]`.  These are the
integer-micro-unit form of the immutable environment increments, but carry no
cause names or token mapping:

| Order | Integer micro-units | Canonical JSON bytes | Lowercase SHA-256 |
|---:|---|---|---|
| 0 | `[0,-20000,0,160000]` | `[0.0,-0.02,0.0,0.16]` | `22659515e916b3b5ead3390438733bda2e15df9b44b6b0b9afcab30718b0dae9` |
| 1 | `[0,-180000,0,40000]` | `[0.0,-0.18,0.0,0.04]` | `9799be678e4269454a06e199889f37eee9cc1aec02b810befdef3fcc583b04b8` |
| 2 | `[0,0,160000,20000]` | `[0.0,0.0,0.16,0.02]` | `3d6288b3042ee89950548d7a3ef44d183243feb7af0913ce9a25b9a2b040099f` |
| 3 | `[0,120000,0,0]` | `[0.0,0.12,0.0,0.0]` | `4df0754afbdd63f7e4865bfd10062c20ec5414e469c6b4f8776cddbd8babd5ff` |
| 4 | `[280000,0,0,0]` | `[0.28,0.0,0.0,0.0]` | `846bdcd2a0768a906623d807c95580c025a63b99d87b2335d7d097f972f71c16` |

Order is the lexicographic order of the listed canonical UTF-8 JSON bytes.
Tests must rederive every hash from these card-frozen bytes and must also verify
the canonical scorer posts from `S=[450000,620000,500000,430000]` plus base
plus prototype.  Two implementations copying an unbound table are not accepted.

- Prototype/delta/prediction values use signed integer micro-units (`10^6`).
- Prototype order and SHA-256 values are rederived from the frozen canonical
  JSON vectors.
- Mapping order is `itertools.permutations(range(5))`.
- One-swap order is `itertools.combinations(range(5), 2)`.
- On common `/360` prior units, every surviving mapping receives scratch `1`,
  exact-source count contribution `20`, and one-swap-neighbour contribution `2`.
- Exact half-even integer rational rounding is used at the six-decimal BMA
  boundary.
- The 5% quantile uses integer CDF comparison
  `20 * cumulative_weight >= total_weight`.
- No binary floating posterior, quantile, threshold, or verdict arithmetic is
  allowed.

## Coverage contract

- Derive all 13 distinct per-source contribution vectors.
- Derive all 18,564 distinct sums obtainable from six arbitrary source entries.
- Cover every remaining-prototype set (`C(5,3)=10`) and every truth order
  (`3!=6`).  The two orders of the already observed complement are proven
  grammar-equivalent, yielding all `10 x 6 x 2 = 120` target mappings.
- Separately enumerate the true-analogy subset by requiring the exact target
  mapping to appear one or more times in the six-source multiset; report its
  own case count, positive count, and maximum improvement.
- Cross-check the symmetry reduction by explicitly expanding all 20 ordered
  observed-prototype pairs (`2,227,680` state/target cases) through the same
  frozen integer arithmetic kernel.  This is a coverage/symmetry cross-check;
  it is not an independent implementation of contribution, rounding, or q05.

The primary enumeration, symmetry cross-check, tests, and role reviews are all
inside the same model/tool lineage.  None is external independent audit.

This is a complete finite enumeration, not statistical sampling; no p-value or
confidence interval is applicable.

## Trace/replay requirement

The producer writes canonical machine-readable outputs under the task artifact
root.  A **fresh CLI process** must rerun the producer before reading the prior
bundle, canonicalize outputs, and require exact equality of result content and
core file hashes.  Stored verdict fields are never inputs to enumeration.  The
trace records coverage counts, arithmetic contract, maximum case, and gate-use
counts, not per-world or private data.

The enumerator must be outcome-neutral: computation returns observed values
without asserting the expected negative answer.  A separate first-true
dispatcher implements both positive and negative branches, with synthetic
tests proving the positive branch is reachable and private/instrument-invalid
branches retain priority.  Expected R6 values may be asserted in tests only
after this two-sided dispatch property is established.

## Leakage and seed firewall

- The producer imports no repository runtime module and reads no repository
  source/data file except its own frozen task bytes for provenance.
- It accepts no CLI seed, world, mapping, source row, trace, run, artifact, or
  environment input.
- It does not call `_token_mapping`, `objects_by_cause`, a controller, an engine,
  `transition_world`, or a scorer.
- The five vectors are the public R5-frozen anonymous prototype vectors, not a
  source-world mapping.
- No source/development/held-out worlds or policy seeds run.  Worlds `30..150`
  remain contaminated and unchanged; no world above `150` is inspected.

## Evidence artifacts

Under `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/`:

- `result.json` — hypothesis, exact counts, maximum effect, verdict, hashes;
- `trace.jsonl` — finite-coverage and maximum-case receipts;
- `baseline_comparison.json` — exact scratch and gated-reference comparison;
- `ablation_report.json` — gate-use diagnostic without rescue semantics;
- `replay_report.json` — independent rerun/canonical equality;
- `failure_manifest.json` — exact no-headroom blocker and forbidden next actions;
- `claim_ceiling.txt` — bounded preflight claim.

## Acceptance gate

Accept only if:

1. R5 commit and three file hashes match;
2. the exact allowed paths are the complete diff;
3. the producer has tests for fixed signatures, contribution grammar, state
   count, complete target coverage, half-even rounding, exact quantile boundary,
   output schema, no input surface, and expected failure dispatch;
4. the primary symmetry-reduced enumeration and explicit 20-ordered-pair
   same-kernel expansion agree on zero positive cases and maximum improvement;
5. replay from code recomputation matches canonical result bytes;
6. all evidence files derive from callable computation and contain producer,
   inputs, aggregation, code hash, and run receipt;
7. tests exercise the exact vectorized half-even and q05 functions used by the
   evidence path, not unused scalar lookalikes;
8. provenance binds the producer, test file, Python version, NumPy version,
   dtype, R5/R6 authority bytes, and fresh-process replay mode;
9. no product source, controller, seed, mapping, pilot, push, or tag is used.

## Stop conditions

- Any R5 byte/hash drifts.
- Any private mapping, seed, runtime trace, source row, or world-dependent input
  is required.
- Any floating comparison affects posterior, q05, threshold, or verdict.
- Coverage is sampled rather than complete.
- Threshold, prior, quantile, budget, or endpoint changes after seeing output.
- Any product implementation begins before a positive feasibility result.
- Any result artifact is hand-authored rather than generated and replayed.

## Rollback

Remove only uncommitted files named below.  Never reset, amend, rewrite, delete,
or mutate R4/R5 or unrelated files.  A later correction must be a successor
commit.

## Allowed files

- `docs/codex/tasks/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6.md`
- `docs/codex/tasks/ego-v2-p1-conservative-transfer-static-headroom-preflight-001c-r6/COLLISION_RECORD.md`
- `scripts/codex/check_ego_v2_conservative_transfer_static_headroom_001c_r6.py`
- `scripts/codex/tests/test_check_ego_v2_conservative_transfer_static_headroom_001c_r6.py`
- `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/result.json`
- `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/trace.jsonl`
- `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/baseline_comparison.json`
- `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/ablation_report.json`
- `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/replay_report.json`
- `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/failure_manifest.json`
- `artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6/claim_ceiling.txt`

All `labs/`, product tests, controller, engine, predictive-control, microworld,
store, UI, launcher, route-state, historical artifact, source/development/
heldout, push, and tag paths are forbidden.

## Verdict dispatch

First true condition:

1. `PRIVATE_TRUTH_OR_SEED_INPUT`;
2. `STATIC_HEADROOM_INSTRUMENT_INVALID`;
3. `CONSERVATIVE_TRANSFER_NO_LEGAL_HEADROOM` when the
   true-analogy-constrained maximum gated improvement is below `0.021875`;
4. `STATIC_REFERENCE_HEADROOM_FEASIBLE` only when the constrained maximum meets
   `0.021875`; an unconstrained-only positive case returns `UNKNOWN` and cannot
   authorize implementation.

No verdict authorizes product-path implementation automatically.  A positive
result would only return to a separately frozen implementation card.  A
negative result requires a prospective design revision or route closure.

## Claim ceiling

This card may establish only a complete seed-free mathematical feasibility or
infeasibility result for the exact frozen R5 budget-2 finite gate.  It cannot
establish controller-path effect, transfer learning, near-miss safety,
development or held-out behavior, survival benefit, neural emergence, AGI,
agency, consciousness, subjectivity, emotion, companion readiness, or
electronic life.

## Auto-Remote-Anchor

`forbidden`
