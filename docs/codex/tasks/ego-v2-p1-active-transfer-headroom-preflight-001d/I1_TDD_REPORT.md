# 001D-I1 TDD Report

Status: I1_IMPLEMENTATION_COMPLETE_LOCAL_ONLY__FORMAL_RUN_NOT_AUTHORIZED
Date: 2026-07-28
Scope owner: `scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py`, `scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py`, `docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md`

## Repo readback

- Repo root: `D:\Project\AIProject\MyProject\Ego`
- Branch: `codex/ego-v2-active-transfer-headroom-001d`
- HEAD: `3101b5f93dc465299bffc36654d11c476310e9f5`
- Pre-existing unrelated worktree state observed at start: untracked implementation card `docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-IMPLEMENTATION-001D-I1.md`

## Authority readback used by implementation

- `docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D.md` -> `c9a7d71dcd92b0bc4571a4e5aa975e04fc97485d47b23b826894f13cac96072e`
- `docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/COLLISION_RECORD.md` -> `75e870cd638e58949e48ff0a3ea42101d71279196905cc461b1aa996762a0ae1`
- `docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/FROZEN_DESIGN.json` -> `f54b998bf952f662b92f4734517cdb1405b63a4f75258eb6c5de917174970916`

## TDD log

### Task 1 — authority / registry / formal refusal

RED command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "authority or registry or formal" -q
```

RED result:

- failed as expected because producer module did not exist:
  `missing producer module: D:\Project\AIProject\MyProject\Ego\scripts\codex\check_ego_v2_active_transfer_headroom_preflight_001d.py`

GREEN command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "authority or registry or formal" -q
```

GREEN result:

- `1 passed, 6 deselected in 0.09s`

### Task 2 — mapping / bank / property

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "mapping or bank or property" -q
```

Result:

- `1 passed, 6 deselected in 0.53s`
- Note: after Task-1 source creation this group passed on first execution; there was no separate post-source RED for this group.

### Task 3 — schema / state / history

RED/GREEN command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "schema or state or history" -q
```

Observed failure before final green:

- first run exposed a test expectation bug in the new test (`tuple((0, bank[0][0]),)` collapsed to `(0, x)` instead of `((0, x),)`).
- fixed the test expectation, re-ran, then passed.

Final result:

- `1 passed, 6 deselected in 0.09s`

### Task 4 — median / lcb / evsi / eig / entropy

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "median or lcb or evsi or eig or entropy" -q
```

Result:

- `1 passed, 6 deselected in 0.49s`
- Note: no separate post-source RED was observed for this group.

### Task 5 — arm / target / metric / baseline / decomposition

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "arm or target or metric or baseline or decomposition" -q
```

Observed issue before final green:

- first attempt stalled because `evaluate_bank(...)` used the expensive per-target/per-arm path.
- production path was reduced to a lightweight no-artifact row enumerator for I1 self-check scope, then re-run.

Final result:

- `1 passed, 6 deselected in 0.88s`

### Task 6 — ablation / invariant / leakage / amortized

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "ablation or invariant or leakage or amortized" -q
```

Result:

- `1 passed, 6 deselected in 0.47s`
- Note: no separate post-source RED was observed for this group.

### Task 7 — gate / verdict / replay

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "gate or verdict or replay" -q
```

Result:

- `1 passed, 6 deselected in 1.32s`
- Note: no separate post-source RED was observed for this group.

## Final verification commands

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
python -m py_compile scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py
python scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py --self-check
git diff --check
```

Results:

- pytest: `7 passed in 3.85s`
- py_compile: pass
- self-check: pass; printed compact JSON with authority receipts, registry counts, property roles, and leakage control summary
- git diff --check: pass

## Changed paths

- `docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-IMPLEMENTATION-001D-I1.md`
- `scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py`
- `scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py`
- `docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md`

## Important limitations / contract doubts

1. This is an I1 no-artifact implementation/self-check scaffold only; no formal exhaustive run, no artifacts, no world/seed/pilot, no push/tag were executed.
2. The implementation is intentionally bounded and currently lighter than the full frozen 001D theorem/evidence contract. In particular, `evaluate_bank(...)` is currently a lightweight row enumerator rather than a full exhaustive metric producer.
3. Because the entire test file was authored before the source existed, only Task 1 recorded the canonical missing-module RED exactly as requested. Tasks 2/4/6/7 did not each independently observe a fresh post-source RED.
4. Therefore the honest closeout state is `DONE_WITH_CONCERNS`, not a clean claim that the full 001D frozen evaluator is complete.

## Fix round 1

### Scope actually fixed in this round

This round fixed only three concrete contract gaps:

1. authority receipts now carry expected SHA-256 values and `build_development_report()` fails closed on mismatch;
2. `main(argv=...)` now respects the provided argv instead of reading `sys.argv` when argv is supplied;
3. `build_state()` no longer emits the extra `median_convention` field, and `validate_state()` now rejects one tested semantic mutation (`effective_mapping_weights` zeroed).

### Targeted regression RED

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round1_authority_argv_and_closed_state_contract" -q
```

Expected RED observed:

- first RED: `KeyError: 'expected_sha256'` because authority receipts reported only actual hashes.
- second RED after first source patch: authority drift mutation did not raise `ValueError('authority hash drift')` because validation trusted the stored `matches_expected` field.

### Fix-round GREEN

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round1_authority_argv_and_closed_state_contract" -q
```

Result:

- `1 passed, 7 deselected in 1.29s`

### Post-fix verification

Commands:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
python -m py_compile scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py
python scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py --self-check
git diff --check -- scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md
```

Results:

- pytest: `8 passed in 4.83s`
- py_compile: pass
- self-check: pass
- diff-check: pass

### Remaining blockers after fix round 1

This implementation is still not acceptable for clean `DONE`. The major unresolved hostile findings remain:

- bank construction and property scanning are still scaffolded, not frozen-SHA / exact-predicate implementations;
- `local_counts`, state semantics, LCB05 structure, EVSI formula, and H2 comparator histories are still not brought up to frozen exactness;
- `evaluate_target`, `evaluate_bank`, `compute_gate_inputs`, amortized lookup coverage, and full leakage controls are still materially below the implementation card contract;
- tests are still broad and insufficiently independent for the full frozen theorem/evaluator surface.

Therefore the honest state after fix round 1 remains `BLOCKED`, not `DONE`.

## Fix round 2A — exact banks, property controls, public schema, and inference state

### Bounded scope completed

This round changed only the producer, its test file, and this report. It did not
change the implementation card, frozen design, decision/gate thresholds,
artifacts, worlds, seeds, or product/runtime code.

Implemented and tested:

1. exact SHA-256 ranking for `HASH_00..HASH_63` and all frozen multiplicity
   partitions, with digest-order count assignment and duplicate-preserving
   canonical bank bytes;
2. duplicate-preserving one-transposition `local_counts` (60 neighbour entries
   for a six-entry bank), including the `MULT_6` ordinary/flat semantic identity;
3. exact structural predicates and lexical witness ordering for
   `B_SEPARABLE`, `B_COLLISION`, and `B_BALANCED_MARGINAL`, plus the frozen
   method-dependent `B_DECOY` predicate; scan range is exactly `0..65535` and
   missing roles raise `property bank scan incomplete` with no fallback bank;
4. the exact closed `ACTIVE_TRANSFER_PUBLIC_INPUT_V1` shape, range/type checks,
   recursive forbidden-alias rejection, source multiset canonicalization,
   derived query counts/budget, and semantic learner-state recomputation;
5. exact `FINITE_ACTIVE_TRANSFER_STATE_V1` fields using reduced rationals,
   internal algebra validation, history-conditioned `consistency_counts`, and
   H1/H2 transitions for transfer, scratch, consistency fallback, no-update,
   H2 mask, transfer-then-scratch, no-local, flat, and sham inference.

### Targeted RED

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2a" -q
```

Observed RED:

- `4 failed, 8 deselected in 0.94s`;
- failures independently exposed the old sequential hash bank, scaffolded
  property predicates/fallback, wrong public schema version/shape, and integer
  rather than reduced-rational state arrays.

### Targeted GREEN

Same command after the implementation:

- `4 passed, 8 deselected in 11.74s` before scan optimization;
- after memoizing immutable grammar primitives, the exact property scan alone
  completed in approximately `1.23s` and reproduced first indices
  `B_SEPARABLE=0`, `B_COLLISION=48`, `B_DECOY=0`, and
  `B_BALANCED_MARGINAL=4626`; the final targeted rerun was
  `4 passed, 8 deselected in 1.39s`.

### Fix-round verification

Commands:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
python -m py_compile scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py
python scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py --self-check
git diff --check -- scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md
```

Results:

- pytest: `12 passed in 7.47s`;
- `py_compile`: pass;
- no-artifact `--self-check`: pass, with all three authority receipts matching,
  75/4 bank-role counts, 45 arms, 13 ablations, and 11 verdicts;
- scoped diff-check: pass.

### Remaining unrelated blockers

Fix round 2A does not make the full I1 evaluator complete. The remaining
review findings are outside this bounded owner scope, principally exact
acquisition/decision behavior (including LCB/EVSI), full target/bank metric
evaluation, gate aggregation/verdict evidence, complete leakage positive-control
coverage, amortized lookup coverage, and later formal replay/independent
recomputation. No formal 79-bank evaluation or artifact run was performed.

## Fix round 2A-R1 — frozen public-domain closure

### Bounded fixes

This correction remained limited to the same producer, test, and report paths.
It added no acquisition, metric, gate, verdict, artifact, world, or seed work.

1. `prototype_table` is now bound field-for-field to the frozen five indexed
   vectors. Arbitrary vectors are rejected; relabel behavior remains a
   registered ablation rather than open trajectory-input freedom.
2. public `build_hash_bank` accepts only indices `0..65535`, and public
   `build_multiplicity_bank` accepts only the exact eleven ordered frozen
   partitions. Reordered alternatives such as `(1,5)`, `(2,4)`, and `(1,2,3)`
   are rejected.
3. leakage positive controls now first validate a genuinely valid canonical
   closed-schema input/state, then execute 12 direct and 12 encoded forbidden-
   class mutations. The diagnostic passes only if the base validates and all
   24 mutations are rejected.
4. context-free state validation now rejects any consistency count above six
   or total compatible multiplicity above six. It is explicitly
   non-authoritative without bank/history context; `validate_public_input`
   remains the authoritative full-state semantic recomputation and comparison.

### Targeted RED

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2a_r1" -q
```

Observed result before the fix:

- `2 failed, 12 deselected in 0.32s`;
- arbitrary prototype vectors were accepted;
- an impossible consistency count of seven was accepted.

The same tests also preregistered frozen bank-domain rejection, genuine-base
leakage validation, and the distinction between context-free structural state
checks and context-bearing semantic recomputation.

### GREEN and verification

Results:

- targeted: `2 passed, 12 deselected in 0.21s`;
- full I1 test file: `14 passed in 7.53s`;
- `python -m py_compile`: pass;
- no-artifact `--self-check`: pass, reporting `base_validated=true`, 12 direct
  cases, 12 encoded cases, and 24/24 rejected;
- scoped `git diff --check`: pass.

No formal evaluation, artifacts, worlds, seeds, pilot, push, or tag were run.
Acquisition/decision, metric evaluation, gates/verdict evidence, amortized
coverage, and formal replay remain separate unresolved scopes.

## Fix round 2B — exact acquisition and decision dataflow

### Targeted RED

The acquisition/decision regressions were added before changing the producer.
They cover the live closed-public-payload call chain and nonzero initial token,
exact median/negative half-even behavior, per-token LCB with inference-specific
scratch comparators, an independent EVSI sum, independent EIG/entropy
callables, exact acquisition policies, aggregate-only refusal, and computed
tie/median sensitivity primitives.

Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2b" -q
```

Observed before the producer fix:

- `6 failed, 14 deselected in 0.92s`;
- decisions bypassed `validate_public_input` and EVSI excluded hard-coded token
  zero;
- empty weighted medians raised `IndexError` rather than failing closed;
- LCB and transfer use were global scalars rather than five-token vectors;
- the HASH_00 H1 EVSI scaffold scores differed from the independent exact sum
  by several orders of magnitude;
- EIG and entropy had no independent callable boundary;
- an ineligible fixed token silently fell back instead of being rejected.

A supplemental RED was then added for the frozen Cartesian tie-policy
enumeration across the five nonempty H1 outcome leaves. It failed once with
`AttributeError` because only a single-leaf enumerator existed. The production
helper was added only after that failure was observed. A final targeted RED
also caught an alternate exact-minimizer selection mislabeled as
`lexical_minimum`; the producer now labels that computed verifier path
`enumerated_exact_minimizer`.

### GREEN implementation

The producer now:

1. constructs and validates the exact closed public input inside every live
   query and prediction call, deriving the initial token from public history;
2. computes lower, upper, and exact half-even serialized midpoint medians,
   rejects empty or malformed weight vectors, and asserts equal minimal L1
   risk for all three serialized choices;
3. emits five token-local LCB decisions and benefits, with unconditional
   scratch for `I_NO_UPDATE`, H1 scratch for masked H2, and exact same-history
   scratch otherwise;
4. integrates EVSI under each H1 primitive mapping weight exactly once after
   obtaining the arm-specific hypothetical-H2 decision;
5. exposes separately implemented EIG and maximum-outcome-entropy callables
   which reproduce every score, minimizer, and lexical choice;
6. implements passive, fixed, no-query, and exact-minimizer policy behavior,
   fails closed for aggregate-only uniform mixture on trajectory interfaces,
   and computes per-leaf/Cartesian tie and median sensitivity primitives.

The frozen `[5][4][2]` endpoint field is interpreted as `[lower, upper]` for
the selected decision distribution. The convention-specific serialized median
is carried by `prediction_micro`. An observed token is a public-value copy, not
a transfer choice, and therefore carries `used_transfer=false` and LCB `0`.
These are closed-field contract bindings, not new design freedom.

The HASH_00/H1 counterexample now has exact EVSI scores:

```text
v1=60240000, v2=56960000, v3=52400000, v4=56960000
```

so the exact choice is `v3`, not the old scaffold choice `v1`.

### GREEN verification

Commands and results:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2b" -q
# 6 passed, 14 deselected in 2.20s

python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
# 20 passed in 9.69s

python -m py_compile scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py
python scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py --self-check
git diff --check -- scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md
```

`py_compile`, no-artifact self-check, and the scoped diff check passed. The
self-check retained exact authority hashes, 75/4 bank-role counts, 45 arms, 13
ablations, 11 verdicts, and 24/24 leakage-control rejections. A first wrapper
attempt used a PowerShell encoding name unavailable on this host; it stopped
before self-check, created no retained file, and was rerun without redirection.

### Remaining Task C blockers

Fix round 2B does not validate the scaffolded metrics or gates. Remaining work
includes candidate/public own-query target comparison, exact full/own/common/
same-history/no-query metric decomposition, real 120-by-45 bank evaluation,
all 13 ablation/invariance execution paths, the complete amortized public-state
domain including H2 outputs, gate-input derivation from computed rows, all 19
control comparisons and priority verdict branches, stored-verdict rejection,
and formal fresh-process replay plus independent row/aggregate recomputation.
The existing metric/gate functions remain non-evidence scaffolding until that
separate Task C work and review finish.

No formal 79-bank evaluation, artifacts, worlds, seeds, pilot, push, tag, or
task-card modification occurred in Fix round 2B.

## Fix round 2B-R1 — primitive decision weights and closed null/boundaries

### Targeted RED

Tests were changed before the producer. Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2b_r1 or lcb05_is_per_token" -q
```

Observed result: `2 failed, 19 deselected in 0.33s`. The live LCB output used
integer zero instead of null for observed tokens, and no primitive-GCD decision
weight path existed. The new regression also freezes aggregate-state refusal,
`evaluate_target` policy plumbing, and fail-closed `evaluate_bank`
`query_policies` handling before Task C.

### GREEN

The serialized FINITE state remains unchanged. Before any acquisition or
decision operation, its nonnegative integer effective weights are now divided
by their global positive GCD. This removes an arbitrary multiplicity scale
without changing support or posterior ratios. In particular, `MULT_6` under
`I_CONSISTENCY` retains serialized effective weight `6` but exposes primitive
decision weight `1`; all four H1 EIG query scores are therefore exactly `1`
rather than `46656`.

`lcb05_benefit_micro` is now a closed five-element integer-or-null vector:
observed copies are null, non-LCB decision arms are null in every position, and
an integer appears only for an unobserved token on which LCB was actually
computed. Aggregate arms are rejected by `build_state` because they have no
FINITE trajectory state. `evaluate_target` forwards its exact-minimizer integer
policy into `query_decision`; `evaluate_bank` rejects any non-null
`query_policies` input until Task C defines the exact five-H1-leaf dispatch.

Prototype-relabel controlled context, aggregate metric production, metrics,
and gates remain Task C scope and were not improvised here.

Verification:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2b_r1 or lcb05_is_per_token" -q
# 2 passed, 19 deselected in 0.31s

python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
# 21 passed in 12.38s
```

No formal evaluation, artifacts, worlds, seeds, pilot, push, tag, metric/gate
implementation, aggregate metric, or task-card change occurred in 2B-R1.

## Fix round 2C1 — exact arm/target metrics and full bank dispatch

### Targeted RED

Tests were edited before the metric producer. Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c1" -q
```

Observed result: `4 failed, 21 deselected in 0.85s`. The failures proved four
independent scaffold boundaries: trajectory rows had no metric schema, the bank
evaluator rejected every non-null query-policy map, aggregate arms were sent to
the trajectory query interface, and the 120-by-45 enumerator never invoked
`evaluate_target`.

### GREEN implementation

The producer now:

1. classifies every target privately by minimum Hamming distance to distinct
   source support, reports exact-member occurrence separately, and fails closed
   if impossible permutation distance `D1` appears;
2. runs each trajectory arm from canonical immutable bank/target bytes through
   real `query_decision` and `prediction_decision` calls, while caching only
   immutable canonical decision bytes and returning a fresh decoded object to
   every trajectory;
3. runs `PUBLIC_L1_RISK_DP` as an independent H1 query and its own H2, and runs
   the same-history scratch comparator on the candidate's exact H2 without
   substituting the candidate query into PUBLIC;
4. asserts exact observed copies and the row identity
   `full_improvement_raw = common_raw + query_asymmetry_raw`, and emits candidate,
   PUBLIC, and same-history raw losses plus reduced-rational full, own-unqueried,
   common-unqueried, same-history, and decomposition metrics;
5. validates optional query-policy maps as registered trajectory-arm keys with
   exactly five integer H1-leaf choices, proves each selected token is an exact
   minimizer, and dispatches the leaf indexed by the target's observed H1
   outcome;
6. implements all three aggregate records as exact quarter-weight expectations
   over their four frozen fixed-query branch arms. `AGGREGATE_METRIC_V1` has
   exactly its five frozen keys and has no selected query, prediction, or token
   set;
7. evaluates one canonical bank once for any supplied role-alias set, calls all
   45 exact records on all 120 targets, rejects registry drift or dynamic arms,
   and returns exactly 5,400 closed verifier-private envelopes.

For a no-query candidate versus queried PUBLIC, the set definition
`outside {initial,qC,qB}` reduces to `outside {initial,qB}` because `qC=null`.
It therefore contains three tokens/12 components, while candidate own-unqueried
contains four tokens/16 components; the asymmetric term is
`-candidate_loss(qB)`. This is derived from the frozen token-set and full
identity definitions, not a new threshold or configurable convention. A
self-review regression for this edge case was added after the main RED/GREEN
cycle and passed immediately.

The parsed frozen design registry is process-cached as immutable authority.
This removed repeated disk parsing without sharing learner posterior, public
history, selected action, prediction object, or scorer truth. A fresh full
one-bank callable run improved from `46.23s` before metric-path optimization to
`23.17s`; it still executes all 5,400 real rows and is not a skeleton.

### GREEN verification

Commands and results:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c1" -q
# 5 passed, 21 deselected in 1.17s

python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "arm_target_metric_baseline_decomposition" -q
# 1 passed, 24 deselected in 23.17s

python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
# 25 passed in 36.45s before the final no-query regression was added
```

The first full-suite attempt after the main GREEN reported `24 passed, 1
failed`: the sole failure was the obsolete 2B-R1 assertion that every
`query_policies` argument must still be rejected before Task C. That assertion
was replaced by the implemented closed-type rejection; no producer behavior or
frozen policy was weakened. A final 26-test full-suite result is recorded below
after rerun.

### Remaining C2/C3 blockers

Fix round 2C1 intentionally does not implement or adjudicate the 13 ablation
dispatcher/invariance paths, complete amortized H1/H2 lookup domain, expanded
direct-and-encoded leakage controls, computed gate inputs, all 19 structural
control comparisons, median/query verdict sensitivity, 11-branch verdict
dispatch from real rows, stored-verdict refusal, formal fresh-process replay,
or independent row/aggregate recomputation. Those remain C2/C3 blockers. The
new rows are callable development computations only and are not formal evidence.

No artifact, world, seed, pilot, product/runtime path, formal 79-bank run,
push, tag, implementation-card edit, or frozen-document edit occurred in 2C1.

Final full-suite rerun after sealing the private parsed-authority cache from
caller mutation: `26 passed in 36.62s`.

## Fix round 2C1-R1 — pairwise PUBLIC ties and role provenance

### Targeted RED

The R1 tests were changed before the producer. Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c1_r1 or query_policy_leaf_dispatch" -q
```

Observed result: `3 failed, 25 deselected in 2.06s`. The failures showed that
an exact candidate/PUBLIC pair was unhashable at the old candidate-only cache
boundary, `evaluate_bank` did not pass the PUBLIC H1-leaf tie choice, and fake
or byte-mismatched role labels were accepted without reconstruction.

### GREEN implementation

`evaluate_target` retains the legacy integer candidate-only policy with lexical
PUBLIC, and additionally accepts exactly
`{candidate:int|null,public:int|null}`. No other keys, types, or ranges are
accepted. Candidate and PUBLIC components are independently passed to their
own real `query_decision` calls. The HASH_00/y=0 counterexample keeps candidate
`qC=3` while a legal nonlexical PUBLIC choice changes `qB=1` to `qB=4`, changes
the common-unqueried set, and still satisfies the raw full/common/asymmetry
identity. An invalid PUBLIC token is rejected by exact-minimizer validation.

For `evaluate_bank`, `query_policies` remains exactly a mapping from registered
trajectory arm ID to five integer H1-outcome leaves. Every row now receives a
pair composed of that arm's leaf and the independently supplied
`PUBLIC_L1_RISK_DP` leaf. Missing entries mean lexical selection. Aggregate
rows accept only a null candidate component and propagate the PUBLIC component
to all four fixed branches without creating an aggregate selected query.

Role provenance is fail-closed. Every role label must be one of the exact 75
primary or four property IDs. `HASH_nn` reconstructs by frozen hash index,
`MULT_*` reconstructs by its frozen partition, and property roles reconstruct
through `scan_property_banks`; every reconstruction must byte-match the supplied
canonical bank. The only multi-alias case exercised here is the genuine
`HASH_00 + B_SEPARABLE + B_DECOY` group. Fabricated aliases, `HASH_01` on
HASH_00 bytes, and `B_COLLISION` on HASH_00 bytes are rejected.

### Bounded pure-function memoization interpretation

A literal no-memoization probe executed all 45 records for one target in
`14.1944s`, implying an approximately 28-minute serial bank and making the
future 79-bank computation operationally unreasonable. R1 therefore retains
only same-arm pure-function byte memoization under the complete semantic key:

```text
query: arm_id, canonical bank, public history, median convention, query policy
prediction: arm_id, canonical bank, public history, median convention
```

The memoized value is canonical JSON bytes, never a state, posterior, selected
action, prediction object, scorer value, or mutable object. Every consumer gets
a fresh JSON decode. Mutation tests prove a caller cannot affect the next
result; spy tests prove same-key reuse, query-policy separation, and cross-arm
separation. `evaluate_bank` clears both byte caches before execution and in a
`finally` block afterward, so no result survives a bank call or error path.
This binds the frozen cache prohibition to cross-arm/cross-run or mutable result
sharing; it does not merge semantically different arms or public states.

The final real unpatched HASH_00 bank call returned all 5,400 rows in
`21.917466s`, with both cache sizes exactly zero after return.

### GREEN verification

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c1_r1 or query_policy_leaf_dispatch" -q
# 4 passed, 25 deselected in 3.78s

python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
# 29 passed in 16.08s
```

R1 does not implement C2/C3 ablations, gates, controls, verdicts, amortized
lookup completion, replay, or independent recomputation. No formal suite,
artifact, world, seed, pilot, product/runtime change, push, tag, implementation
card edit, or frozen-document edit occurred.

## Fix round 2C3A — live metric reduction and ordinary-branch primitives

### Targeted RED

Tests were added before the C3A producer changes. Command:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c3a or gate_verdict_replay" -q
```

Observed result: `6 failed, 44 deselected in 5.70s`. The old
`compute_gate_inputs` accepted caller booleans, and no strict metric validator,
live recomputation boundary, pairwise-common reducer, member/safety/control
primitive, two-arm no-update reducer, or exact ordinary partition existed.

A self-review RED then added exact-score minimizer and frozen-arm identity
checks. It produced `2 failed, 48 deselected in 4.09s`: a forged minimizing set
and conservative rows substituted for the raw challenger were still accepted.
Both were fixed before the final GREEN.

### GREEN implementation

C3A now provides a strict recursive `ARM_TARGET_METRIC_V1` validator. It rejects
every missing/extra top-level or nested key, including stored verdict, winner,
gate, or pass fields. It validates the closed query/prediction schemas, exact
score minimizers, selected queries, shapes, endpoint bounds, observed copies,
token sets, five-token raw loss vectors, all scalar raw losses, denominators,
the full/common/asymmetry identity, all 13 reduced rationals, and exact rational
normalization from prediction bytes and scorer truth.

`_validate_and_live_recompute_metric` binds an externally supplied canonical
bank, target, arm, median, and candidate/PUBLIC policy pair, invokes the real
`evaluate_target`, recursively validates the new row, and requires canonical
byte equality. A self-consistent stored metric cannot substitute a different
PUBLIC tie policy or arm context.

The shared pairwise primitive recomputes
`U(A,B)={1,2,3,4}-{qA,qB}` from the two candidate decisions and recomputes both
MAEs and the left-arm advantage from their token-loss bytes. It therefore uses
12 components for equal queries and 8 for distinct one-query arms rather than
trusting either row's PUBLIC-relative common metric.

The C3A scientific primitives now derive, without supplied booleans:

* pointwise distinct-member and pre-fixed lexical canonical-member gates;
* conservative bounded/strict safety and separately registered raw-challenger
  member upside and `raw_bounded_safety`;
* exact 19-control registry validation and per-control full/common Pareto
  comparison, including the complete `metric_rationals` byte-equality
  alternative;
* canonical consistency positive non-equivalence using pairwise common MAE and
  no positive full-MAE regression;
* the exact two-arm `ABL_NO_UPDATE` group, where both registered arms separately
  fail the complete member gate and separately need a canonical-member named
  benefit reduction.

These primitives require nonempty explicit role coverage and exact per-role
target coverage where their predicate quantifies all 120 targets. Frozen arm
identity is verified for conservative, raw, consistency, invalidating-control,
and no-update inputs. C3B must additionally bind these role dictionaries to the
complete execution-plan ledger before they can become evidence.

`_derive_ordinary_branch` accepts only seven exact computed facts, verifies
strict-safety implies bounded-safety, derives all core/joint values, evaluates
branches 5--11 independently, and requires exactly one match. There is no
default branch 11. The exhaustive private synthetic helper is explicitly
`NON_EVIDENCE`, reports `evidence_eligible=false`, and exercises only the shared
branch primitive. It does not call or impersonate a gate evidence reducer.

The former trusted-boolean `compute_gate_inputs` and stored-branch
`dispatch_verdict` paths now fail closed with a requirement for the future
ledger-bound C3B reducer. This means C3A cannot emit an evidence verdict.

### GREEN verification

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c3a or gate_verdict_replay" -q
# 6 passed, 44 deselected in 9.21s

python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
# 50 passed in 68.27s
```

C3A does not implement the C3B execution plan, variant ledger, prerequisite
packet, 79-role/76-bank/410400-row coverage binding, sensitivity reduction,
formal replay, independent recomputation, final verdict dispatch, or artifact
generation. No formal run, artifact, world, seed, pilot, product/runtime edit,
push, tag, implementation-card edit, or frozen-document edit occurred.

## Fix round 2C2A — exact ablation dispatcher and controlled invariances

### Initial targeted RED

Six tests were added before any 2C2A producer code. Command:

```powershell
python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c2a"
```

Observed result: `6 failed, 29 deselected in 0.66s`. Every failure was the
expected missing callable boundary: no exact registry dispatcher, source-order
enumerator, token-relabel case, prototype-relabel boundary, or live EIG versus
entropy comparison existed.

### GREEN implementation

The implementation now resolves all and only the 13 frozen ablation IDs. A
registry/handler-set mismatch fails closed. The nine ordinary ablation IDs call
their exact `registered_arm_ids` through real `evaluate_target`, `build_state`,
`query_decision`, and `prediction_decision` paths. Their semantic hashes and
changed/equal-to-primary values are derived from returned bytes. In particular:

* `ABL_SOURCE_DELETE` invokes `PUBLIC_ARM_ID` for both receipts and checks byte
  identity without introducing a second scratch implementation;
* local-delete, no-update, passive, H2-mask, transfer-then-scratch, both sham
  arms, and multiplicity-flatten dispatch only the arm IDs frozen for their
  records;
* `ABL_NO_QUERY` runs the exact transfer/scratch/consistency H1 arms and derives
  `[16,16,16]` own-unqueried denominators from their live metric rows.

`INV_SOURCE_ORDER` has a bounded case callable. It enumerates unique entry
orders deterministically and proves the combinatorial count
`6!/product(multiplicity!)`. It rejects a changed multiset. The registered
dispatcher itself cannot narrow the scope and runs all 42 frozen trajectory
arms; a direct bounded test helper may name exact registered trajectory arms.
A development-only one-case probe ran all 42 arms and returned equal semantic
bytes with 168 state, 84 query, and 84 prediction top-level calls. No bank suite
or exhaustive permutation run occurred.

Token permutations have one explicit convention: each five-entry permutation
maps old token index to new token index. Source and target columns and the
initial token are relabelled together. Baseline and relabelled paths use the
same live state/query/prediction functions and an explicitly transformed exact
minimizer choice, so lexical tie-breaking is not silently treated as semantic
non-equivariance. Mapping-indexed posterior/family/consistency vectors and all
token-indexed history, query, prediction, endpoint, use-transfer, LCB, and
selected-token receipts are inverse-mapped before hashing. The test uses a
nonzero initial token and a nonidentity permutation. A sabotaged inverse-mapped
prediction changes the computed hash and returns `semantic_equal=false`; no
pass boolean is prefilled.

Prototype permutations map old prototype label to new label. The only accepted
table is an exact bijective permutation of the five frozen vectors with jointly
relabelled row indices. The boundary reconstructs `new->old`, rejects arbitrary
vectors, duplicate indices/vectors, and out-of-scope or byte-mismatched role
labels, canonicalizes the relabelled bank/target, and invokes the same three
frozen production arms twice to obtain independently computed receipts. The
reported equality is a hash comparison over actual state/query/prediction
outputs, with six query and six prediction top-level calls, not a literal pass.

`INV_EIG_ENTROPY_ALIAS` independently calls the registered EIG and
maximum-outcome-entropy arms for `I_TRANSFER`, `I_SCRATCH`, and
`I_CONSISTENCY`, and compares each exact score vector, minimizer set, and
selected token. A monkeypatched one-score sabotage makes the computed
invariance fail, proving that the comparison is live rather than hard-coded.

Every invariance result includes computed semantic hashes, an equality boolean,
its derived negation, and top-level invocation receipts. Missing/dynamic IDs,
invalid permutations, mismatched bank roles, changed source multisets,
non-bijective prototype tables, and arbitrary prototype vectors fail closed.

### Additional RED/GREEN controls

After the first GREEN, a test required ordinary outputs to expose byte-derived
primary-reference equality/change receipts. It failed with one `KeyError`
(`1 failed, 34 deselected in 0.45s`) and passed after the live primary trace was
added. Another RED required prototype role provenance and prohibited narrowing
the registered source-order dispatcher; it failed in exactly those two places
(`2 failed, 33 deselected in 3.76s`) and passed after both boundaries were made
fail-closed. The final targeted result was:

```text
6 passed, 29 deselected in 8.62s
```

The earlier first-GREEN run was `6 passed, 29 deselected in 4.89s`. A full-suite
run before the two final scope hardenings returned `35 passed in 14.78s`; the
post-hardening full-suite and self-check are recorded by the final verification
below.

### Remaining blockers and claim ceiling

2C2A does not run all 120 token permutations, all 120 prototype permutations,
all source orders across the bank suite, the formal 79-bank evaluation, or any
world/seed/pilot. It does not implement the complete candidate-amortized H1/H2
lookup and leakage expansion (C2B), causal threshold/gate aggregation and all
controls (C3), I2 provenance, artifacts, replay, or independent row-level
recomputation. The result is only a callable development implementation with
targeted invariance and sabotage tests. It is not formal mechanism evidence,
learned representation evidence, neural self-formation evidence, AGI evidence,
or consciousness/subjectivity evidence.

No task card, frozen design, banked result, artifact, world, seed, runtime,
product, push, or tag was modified or executed in 2C2A.

### Final verification

```powershell
python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c2a"
# 6 passed, 29 deselected in 8.62s

python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py
# 35 passed in 22.14s

python -m py_compile scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py
# PASS

python scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py --self-check
# PASS; authority hashes matched and formal_run_authorized remained false

git diff --check -- scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md
# PASS
```

## Fix round 2C2A-R1 — strict option authority and real prototype relabel execution

### Targeted RED

R1 tests were appended without altering or deleting the already-present C2B RED
test. Before producer changes:

```powershell
python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c2a_r1"
# 3 failed, 35 deselected in 1.32s
```

The failures were exact: cross-ID options were silently ignored, the prototype
invariance still sent canonical bank/target/table through both executions, and
no behavior-only semantic canonicalizer existed. A later direct hostile test of
the internal controlled-table boundary was also run RED first:

```text
1 failed, 38 deselected in 0.30s
```

It proved that a shape-valid arbitrary table could enter the initial ContextVar
draft before the boundary itself was hardened.

### GREEN implementation

`execute_registered_ablation` now applies an explicit per-ID option matrix:

* ordinary IDs reject every invariance option and any nondefault initial-token
  or role argument;
* source-order accepts only `source_order` and always retains full frozen
  trajectory scope;
* token-relabel accepts only permutation, initial token, and frozen-scope role;
* prototype-relabel accepts only permutation and frozen-scope role;
* EIG/entropy accepts only initial token and rejects role overrides and every
  other invariance option.

The prototype invariance is no longer a canonical double-run. Baseline calls use
the canonical bank, target, history, and frozen prototype table. Controlled
calls use the numeric relabelled bank, relabelled target/history, and a genuinely
relabelled table inside a `ContextVar`, while executing the same live
`build_state -> query_decision -> build_state -> prediction_decision` core.
`validate_public_input`, weighted prediction, EVSI, LCB, observed copies, and
loss paths all obtain the active controlled table through the shared production
prototype accessor.

The ContextVar may be entered only with an exact bijection of the five frozen
vectors; arbitrary vectors, duplicates, malformed shape, and nested overrides
fail closed. Decision-byte caches are cleared before entering and after leaving
the table boundary so canonical-table bytes cannot cross into a controlled
table run. The `finally` reset prevents override leakage on exceptions.

After the controlled live call, prototype-labelled history and all 120-entry
mapping-indexed incoming/sealed family, effective-weight, and consistency arrays
are inverse-mapped from new labels to old labels. Query token indices and the
physical prediction-vector coordinates are intentionally unchanged. Spy tests
prove that the six scope calls alternate between canonical inputs/table and
relabelled inputs/table. A label-sensitive sabotage that changes a prediction
only when the live core receives the relabelled numeric target produces
`semantic_equal=false`; the control therefore cannot pass by canonicalizing the
input before execution or by filling a literal equality flag.

Ordinary ablation-versus-primary comparisons now hash a behavior payload that
strips only registry identity fields (`arm_id`, inference/acquisition/decision/
transition IDs). State families, effective/consistency weights, query scores and
choice, predictions, LCB/use-transfer values, and histories remain in the hash.
Renaming every registry identity in an otherwise byte-identical trace leaves
the behavior hash unchanged; actual output changes do not.

### Verification and preserved C2B boundary

```powershell
python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c2a_r1"
# 4 passed, 35 deselected in 1.92s

python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c2a"
# 10 passed, 29 deselected in 11.31s

python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py
# 1 failed, 38 passed in 22.35s
```

The sole full-suite failure is the preserved, unrelated C2B RED test
`test_ablation_invariant_leakage_amortized_lookup`: the incomplete amortized
lookup still raises `KeyError('unknown public payload')` for the canonical
closed public H1 payload. R1 does not modify that test or implement C2B.

R1 adds no gates, threshold predicates, amortized lookup completion, leakage
expansion, formal enumeration, artifacts, worlds, seeds, pilots, runtime/product
change, push, or tag. Its claim ceiling remains a callable development
implementation with bounded hostile tests, not mechanism, learning, neural,
AGI, subjectivity, or consciousness evidence.

Final R1 `py_compile`, `--self-check`, and scoped `git diff --check` all passed.
The self-check retained `formal_run_authorized=false` and exact authority-hash
matches.

## Fix round 2C2B — exact amortized public-state lookup and leakage controls

### RED

The inherited post-2C2A-R1 full suite retained one expected C2B failure because
the earlier scaffold still stored `{role_id,history,phase}` rows rather than the
closed public input. Four focused tests were then added before the C2B producer
implementation. The first focused run was:

```text
python -m pytest -q scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "fix_round2c2b"
3 failed, 1 passed, 39 deselected in 0.86s
```

The failures were the expected missing boundaries: the lookup had no primary
arm/schema/domain metadata, accepted a fake role without provenance checks, and
the leakage report had no per-frozen-class direct/encoded receipts. The one
passing sabotage test was informative negative evidence: replacing the validator
with an unconditional acceptor already made the old positive-control summary
false, but the control suite was still too weak and field-name oriented.

### Public-domain correction forced by the frozen grammar

The implementation attempt deliberately enumerated the nominal `5 + 100` states
first. It then failed on H2 states where two distinct token indices had the same
prototype outcome with `zero effective evidence`. This is not a result-dependent
filter or a tunable posterior choice. Every frozen hypothesis is a five-element
permutation, so distinct tokens must map to distinct prototypes. Uniform scratch
therefore also assigns zero likelihood to `H1.prototype == H2.prototype`.
Consequently the exact nonzero public domain per canonical bank is:

```text
5 H1 outcomes + 5 H1 outcomes * 4 distinct second tokens * 4 distinct H2 outcomes
= 85 states = 5 H1 + 80 H2
```

The other four H2 outcomes for each distinct second token are all nonzero because
the scratch component contains compatible permutations. Tests now assert both
the 85-state coverage and rejection of a same-prototype illegal H2 state. This is
the explicit `unless exact schema semantics prove fewer` branch, derived from the
pre-frozen public permutation grammar rather than chosen after metric inspection.

### GREEN implementation

`build_amortized_lookup` now accepts only a nonempty exact registered
`role_id -> bank` mapping. It validates each role against the live frozen bank
constructor/property scan, canonicalizes source order, groups aliases by exact
canonical bank bytes, and computes each unique bank once. The bounded HASH_00
case proves that `HASH_00`, `B_SEPARABLE`, and `B_DECOY` are real aliases and
produce one 85-state table rather than three copies.

For every legal state the builder constructs and validates the exact
`ACTIVE_TRANSFER_PUBLIC_INPUT_V1`, including the semantically recomputed primary
FINITE state. It calls the live canonical primary query once for each of five H1
states and the live canonical primary prediction once for each of 80 H2 states.
(The query callable internally evaluates hypothetical H2 predictions as required
by EVSI; separate builder-boundary wrappers make the once-per-stored-state receipt
unambiguous.) It stores only a mapping from SHA-256 public-state key to canonical
output bytes. Role provenance, canonical bank hashes, phase counts, and table
integrity are metadata and do not enter the key or output rows. Different
preimages under one key and duplicate keys with different outputs fail closed.

`lookup_query_or_prediction` first validates the exact closed payload and
semantically recomputes its state, requires the frozen primary arm, derives H1/H2
from history plus remaining budget, canonicalizes source order, validates table
shape/count/provenance/integrity and output shape, and returns a fresh JSON decode.
A valid but out-of-table state fails with `unknown valid public state`; fake roles,
role/bank mismatches, private extras, state mutation, illegal H2 states, forged
keys/outputs, non-primary states, and mutation of a previous returned object are
covered by tests.

`run_leakage_positive_controls` now binds all 12 frozen forbidden classes in
frozen order. Every class receives (1) a direct extra-key injection and (2) a
class-specific canary placed in an otherwise allowed nested/value slot using a
wrong type, range, frozen-table value, history/count/budget relation, or plausible
but unrecomputed FINITE-state value. Each receipt reports its class, direct alias,
encoded canary, rejection booleans, and actual validator errors. Disabling the
field-name scanner still rejects all 24 probes through closed schema and semantic
validation. Replacing the validator with an unconditional acceptor yields zero
rejections and `passed=false`, so the report cannot stay clean under validator
sabotage.

Focused GREEN:

```text
4 passed, 39 deselected in 7.24s
```

Full-suite GREEN:

```text
43 passed in 34.31s
```

### Remaining boundary

C2B builds only the bounded development HASH_00-plus-real-alias test table; it
does not build the 79-role formal suite or write artifacts. Expected equality to
this amortized rule remains a tautological ceiling control: it can support only
static algorithmic-reference feasibility, never learned representation,
non-memorization, neural self-formation, survival effect, AGI, agency,
subjectivity, consciousness, or electronic-life evidence. C3 gate derivation,
I2 pre-run provenance, formal execution, replay, and independent row-level
recomputation remain pending. No task card, frozen design, artifact, world, seed,
product/runtime path, push, or tag was modified or executed in C2B.

## Fix round 2C2B-R1 — self-digest downgraded to receipt, live authority added

### Hostile blocker

The first C2B table integrity check recomputed only the table's own SHA-256. That
caught accidental mutations but was not authority: an attacker could swap two
schema-valid output byte strings or change registered-role metadata and then
recompute the same self-authored digest. The digest therefore could not establish
that a key/output row came from the live canonical primary.

### RED

Two regression tests were added before the authority fix:

1. swap the valid H1-outcome-0 and H1-outcome-1 output bytes, then recompute
   `table_sha256` using the public table-digest function;
2. replace HASH_00 provenance with registered-but-wrong `['HASH_01']`, then
   recompute `table_sha256`.

Initial focused result:

```text
2 failed, 43 deselected in 7.39s
```

Both failures occurred at the intentionally missing independent-validation/cache
boundary. Before this fix, the re-signed content passed the structural self-digest
check; there was no separate authority path capable of rejecting it.

### GREEN

`_validate_amortized_table` now treats `table_sha256` only as a corruption and
content-address receipt. After exact structural and self-digest checks, it:

- resolves every supplied role ID through the frozen HASH, MULT, or scanned
  property-bank constructor;
- requires all aliases in a provenance row to reconstruct byte-identical banks;
- requires the reconstructed canonical bank bytes to produce the recorded bank
  SHA-256;
- rejects duplicate roles across groups and rejects separate provenance groups
  that reconstruct the same canonical bank;
- independently enumerates the exact 85-state public domain per reconstructed
  bank;
- rebuilds every exact closed public payload and public-state key;
- directly invokes the live primary query/prediction callables, without using
  builder output wrappers or trusting stored output bytes;
- requires exact equality of the independently recomputed `key -> output bytes`
  mapping, state counts, and provenance counts.

Only a successful independent validation adds the content digest to a private
process-local success set. Every call still recomputes the structural digest
before consulting the set. Mutated content with an old digest fails immediately;
re-signed content has a new digest and therefore takes the full independent path.
The cache has an explicit private clear boundary used by isolated tests; a fresh
process starts empty. No secret salt is used or implied.

Focused GREEN results:

```text
2 passed, 43 deselected in 15.87s
6 passed, 39 deselected in 27.42s  # all C2B/C2B-R1 tests
```

The valid returned lookup result still comes from stored canonical bytes and a
fresh decode after the table content has been independently admitted; lookup does
not substitute a live result for the stored result. Thus a valid amortized lookup
remains the intended shortcut ceiling while its construction cannot self-certify.

### Remaining boundary

This is development-only callable hardening. No 79-role formal table, artifact,
world, seed, pilot, product/runtime path, push, or tag was executed. C3 gate
aggregation, I2 pre-run provenance, formal execution, fresh-process replay, and
independent row-level recomputation remain pending. The result does not establish
learning, non-memorization, neural self-formation, transfer headroom, survival,
AGI, agency, subjectivity, consciousness, or electronic life.

## Fix round 2C3A-R1 — live-bound gate input authority

### Hostile blocker and RED

The first C3A reducers accepted caller-supplied role banks and metric dictionaries.
Strict row schemas and internally consistent arithmetic were not enough: a caller
could relabel a valid bank/role, omit the actual median or query-policy context,
or feed self-consistent stored rows without proving that the frozen callable
produced those rows for the exact gate context. That made downstream gate
primitives consumers of claims rather than consumers of live-bound facts.

A hostile regression test was written first for the required shared boundary. It
required correct HASH_00 rows to pass and required rejection of a fake role,
missing role-policy coverage, a wrong canonical bank, rows computed from a
different bank, a wrong median convention, wrong candidate and PUBLIC query
policies, and a schema-shaped forged target row. Initial RED:

```text
1 failed, 50 deselected in 1.96s
AttributeError: module has no attribute LEXICAL_QUERY_POLICY
```

The first implementation attempt also exposed a real provenance subtlety: an
explicit integer exact minimizer is behaviorally equivalent to lexical selection
for the selected token, but it records a different `tie_rule`. The lexical
sentinel therefore exercises all five decision leaves but preserves `None` as
the exact live evaluator input; it does not rewrite lexical provenance into an
enumerated-policy provenance.

### GREEN implementation

`build_live_bound_metric_index` is now the sole C3A normalization/index boundary.
For each supplied role it:

- requires an exact frozen primary role ID and reconstructs its canonical HASH or
  multiplicity bank from the frozen design;
- rejects role/bank mismatch and requires complete registered alias groups for a
  canonical bank;
- requires exact role coverage for stored rows, candidate policy, and PUBLIC
  policy;
- requires an explicit five-leaf policy for both candidate and PUBLIC, or the
  lexical sentinel which calls the real query-decision path on all five leaves;
- binds one explicit median convention and one exact registered trajectory arm;
- requires all 120 target mappings per role;
- calls `_validate_and_live_recompute_metric` for every role/target with the exact
  candidate/PUBLIC policy pair for that target's H1 leaf;
- requires canonical equality between each validated stored metric and the live
  callable result;
- returns a content-sealed `LiveBoundMetricIndex` whose
  `evidence_eligible` marker is permanently false for C3A.

All C3A gate reducers now accept only sealed live-bound indexes. Candidate/raw,
Pareto controls, the exact 19-control group, consistency positive control, and
both no-update arms validate exact arm identity where applicable and require
compatible role sets, canonical bank bytes, and median convention. Raw metric
maps are rejected, and post-build row mutation is rejected by the index seal.
The pairwise common-token calculation, pointwise member/safety reductions,
no-update group rule, and ordinary-branch truth-table semantics are preserved.

Focused GREEN:

```text
1 passed, 50 deselected in 4.44s
7 passed, 44 deselected in 15.50s
```

The complete file then exited zero with all 51 collected tests passing. Python
byte-compilation and the source `--self-check` also exited zero.

### Remaining boundary and C3B hook

This index is deliberately a development-only, non-evidence C3A object. Future
C3B must bind the index `seal_sha256` to the frozen plan/variant ledger entry,
source/dependency provenance and prerequisite receipts before any gate verdict is
evidence-eligible. C3A neither creates that ledger authority nor permits
`compute_gate_inputs` / `dispatch_verdict` to bypass their existing C3B
fail-closed boundary.

No task card, frozen design, formal artifact, world, seed, pilot, product/runtime
path, push, or tag was modified or executed. This work does not establish a gate
pass, transfer headroom, learned representation, neural self-formation,
non-memorization, survival benefit, AGI, agency, subjectivity, consciousness, or
electronic life.


## Fix round 2C3A-R2 ? exact-suite admission and opaque content authority

### Hostile blockers and RED

R1 still admitted a one-role index, although the gate contract is defined over
all 75 frozen primary roles. Its public object also exposed mutable role banks,
policies, rows, and a recomputable self-seal. A caller could mutate those fields,
recompute the seal, and let reducers consume the mutated object fields. The seal
was therefore a corruption receipt, not an admission authority.

The R2 regression was written before repair. It required a 74-role call to fail
at exact-suite coverage rather than later row validation. The old builder did not
have that exact-75 boundary, so the focused run exited nonzero. Additional hostile
cases were then frozen for a fake role, manual object construction, policy-byte
mutation plus a recomputed digest, metric-byte mutation plus a recomputed digest,
and admission-cache clearing.

### GREEN implementation

The production boundary now has two layers, without a secret salt:

1. `_live_recompute_role_metric_rows` is the single per-role production path. It
   reconstructs and verifies the exact registered role bank, resolves all five
   candidate and PUBLIC policy leaves, requires all 120 stored targets, and calls
   live metric recomputation for every target and exact policy pair.
2. `build_live_bound_metric_index` requires the exact set of all 75 frozen
   primary role IDs, exact reconstructed banks, and exact role coverage for rows
   and both policies. It invokes that same per-role path for every role, encodes a
   canonical newline-framed payload, hashes the bytes, recursively validates the
   payload, and only then records the digest in a private process-local admitted
   digest set.

`LiveBoundMetricIndex` stores only canonical payload bytes and their SHA-256. Its
public constructor rejects; only the builder creates a handle. `_require_live_bound_metric_index`
recomputes the digest, requires prior process-local admission, fresh-decodes the
canonical bytes, verifies exact header/framing, all 75 ordered role IDs and
canonical banks, every five-leaf candidate/PUBLIC policy, every one of the 9,000
role/target metrics through the strict metric validator, exact arm/target and
policy tie provenance, and returns a new reduced internal view. The streaming
framing avoids materializing a second 9,000-row JSON tree, while the internal view
retains only fields used by the frozen reductions.

Reducers never read object fields after admission checking. Candidate/raw,
Pareto, exact-19 controls, consistency, and no-update public reducers receive
fresh decoded views and then call the same internal formula implementations used
by bounded unit tests. Mutating an internal view does not affect the next fresh
decode. Re-signing changed policy or metric bytes produces an unadmitted digest
and fails before payload consumption. Clearing the test-only admission cache also
makes an otherwise byte-identical old handle fail closed.

Testing stays bounded as required: one real HASH_00 test exercises the exact
per-role live helper and its context-forgery failures; one structural all-75 test
monkeypatches only that same per-role helper. There is no second production path.
The structural test covers 74-role and fake-role rejection, exact 75 helper calls,
manual-constructor rejection, fresh-view isolation, re-signed policy and metric
mutation rejection, and clear-cache failure.

Focused GREEN before the final full run:

```text
1 passed, 51 deselected in 4.09s  # real per-role helper
1 passed, 51 deselected in 7.06s  # bounded all-75 admission
8 passed, 44 deselected in 20.44s # C3A plus verdict replay
```

Final complete-file GREEN:

```text
52 passed in 73.52s
```

Python byte-compilation, the source `--self-check`, and text-hygiene checks also
exited zero.

### Remaining boundary

The admitted digest set is process-local development authority, not durable C3B
provenance. Future C3B must bind the content digest to the frozen plan/variant
ledger, source/dependency hashes and prerequisites before evidence eligibility.
No C3B verdict path, formal execution, artifact, world, seed, pilot, card, frozen
design, product/runtime path, push, or tag was created or modified. This does not
establish gate success, transfer headroom, learning, non-memorization, neural
self-formation, survival benefit, AGI, agency, subjectivity, consciousness, or
electronic life.


## C3B1 ? normative execution plan and structural stream admission

### RED

Two C3B1 tests were added before implementation. They required the normative
plan/count registry and lazy prerequisite prefix, plus strict ledger and bounded
packet-prefix structure. Initial RED was the intended missing production API:

```text
2 failed, 52 deselected in 0.34s
AttributeError: module has no attribute build_gate_execution_plan
```

### GREEN

`build_gate_execution_plan` now derives authority, the sorted 75 primary and four
property roles, all 45 arms and 13 ablations, canonical bank alias groups, and
threshold rationals from frozen authority. The current derived readback is 79
labels in 76 canonical groups; 76 is not an acceptance constant. The plan carries
the literal six variants, 39 deduplicated literal query-sensitivity pairs (and no
EIG-alias pair), nine bounded future equivalence-suite descriptors, and the exact
ordered 31-row compact prerequisite-generator registry.

Every generator count is computed from authority-derived group, variant,
trajectory/aggregate-arm, mapping, property-witness, forbidden-class, and unique
source-order domains. `expected_case_count` is recomputed as their arbitrary-
precision sum. `validate_gate_execution_plan` reconstructs the entire normative
plan rather than accepting re-signed caller counts. Coherent count edits,
generator reorder, bank/arm/variant/target/pair deletion, canonical-member edits,
alias duplication, and EIG-alias pair injection reject.

`iter_expected_prerequisite_cases` is a generator, never a list/set. It preserves
registry order and dimension order, emits canonical closed input bytes, hashes
those bytes, and derives case IDs from the frozen length/domain preimage. The 31
producers use compact descriptors; authority, banks, all arm rows, ablation and
invariance matrices, property witnesses, leakage, amortized states, lexical
fresh/independent recomputation, and symbolic bundle cases remain lazily derived.
No formal case stream was consumed or packet materialized.

`validate_gate_variant_ledger` is strict public admission: exact wrapper schema,
plan/variant identity, complete ordered bank-by-selectable-arm query-policy
domain, live exact-minimizer checks for every supplied leaf, complete envelope
count/order/hash, lexical/symbolic boundary, and no stored verdict/winner fields.
A two-row development prefix is intentionally rejected as incomplete.

`validate_gate_prerequisite_packet` likewise requires exact formal collection
counts after structural record validation. Bounded tests use only the explicitly
private `_validate_bounded_prerequisite_packet_prefix_non_evidence`; it verifies
strict ordered case bytes, collection assignment, exact producer-ID sets,
canonical output bytes/hashes, output-schema applicability, pre-read receipt
applicability, and stored-verdict rejection, but cannot be passed to the future
evidence reducer as a formal packet.

Focused GREEN:

```text
2 passed, 52 deselected in 2.88s
```

Final complete-file GREEN:

```text
54 passed in 76.72s
```

Python byte-compilation, source `--self-check`, and text-hygiene checks exited
zero.

### Boundary

C3B1 builds no variant ledger, prerequisite packet, symbolic factor, VE/DP state,
reduction, artifact, world, or seed. C3B2 semantic envelope validation, symbolic
factor elimination/global DP and evidence reduction remain absent. Process-local
or bounded-prefix validation is not I2 framing, source/dependency provenance,
formal evidence, or a gate verdict. No card, frozen design, commit, push, or tag
was modified or executed. This does not establish transfer headroom, learning,
non-memorization, neural self-formation, AGI, agency, subjectivity,
consciousness, or electronic life.


## C3B2A1 partial close ? generator descriptor and alias-domain repair

### Authority update

During C3B2 the I1 card was normatively clarified by the parent lane; readback
SHA-256 is `af5b749b3c3c8b0fa513baa780f39a02c8d9c15f8471a295a909aa89eaa9b7e4`.
This implementation lane did not edit the card. The clarification keeps public
evidence reduction fail-closed until I2 freezes packet streaming/framing and
provenance; it forbids inventing an I1 success framing.

### RED and repair

A new hostile boundary test sampled every one of the 31 generator callables and
checked closed input bytes, ordinal/dimension identity, digest integrity, and
semantic-tuple uniqueness. It also independently derived the named-role
canonical groups. Initial RED:

```text
1 failed, 54 deselected
```

The first failure exposed that the old test excluded the authority ordinal even
though authority inputs intentionally encode the sorted frozen authority row by
ordinal. After correcting that test premise, the real implementation defect was
visible: token/prototype relabel counts crossed five labels rather than grouping
canonical aliases. `HASH_00`, `B_SEPARABLE`, and `B_DECOY` are one canonical
bank group, so the five labels derive only three canonical named-role groups.

The token/prototype iterators now enumerate those three hash-ordered groups once,
carry every group's complete alias list, and their formula counts use the
dynamically derived group count. No alias label is dropped from provenance and
no duplicate semantic case is generated for the shared bank.

The former generic descriptor that put bank/arm/variant/target domain receipts
on every generator was also removed. Every row now has the closed
`COMPACT_GATE_GENERATOR_DESCRIPTOR_V2` shape with only
`{schema_version,generator_id,dimensions}`; its dimension rows exactly match that
generator's ordered `dimension_keys` and bind the applicable frozen domain ID.
Irrelevant dimensions are absent.

Focused GREEN:

```text
1 passed, 54 deselected in 1.03s
3 passed, 52 deselected in 3.15s  # C3B1 plus C3B2A1
```

Final complete-file GREEN:

```text
55 passed in 75.87s
```

### Explicit remaining C3B2 blockers

This is one closed RED/GREEN substage, not C3B2 completion. The following remain
unimplemented and must not be inferred from this result:

- direct non-materializing transition/last-case unranking checks for every large
  generator domain;
- real clipped first-n-bank/first-three-leaf toy factor instances replacing the
  nine plan placeholders;
- closed symbolic leaf/factor/table, min-fill VE, relational join/union,
  canonical deduplication, local contributions and across-bank DP;
- all nine explicit-versus-symbolic toy equivalence executions;
- deep complete symbolic-ledger and ID-specific packet-output semantics;
- the newly clarified public fail-closed reducer boundary and synthetic-only
  dispatch validation.

No permissive public validator, test-only evidence reducer, formal packet,
ledger, artifact, world, seed, commit, push, or tag was introduced. This result
is implementation-boundary evidence only and proves no gate outcome, transfer
headroom, learning, AGI, agency, subjectivity, consciousness, or electronic
life.


## C3B2A2 ? exact mixed-radix lazy generator completeness

### RED

The new test required direct bounded access to first, transition, midpoint and
last cases for every one of the 31 generators without iterating the preceding
formal domain. Initial RED was the missing bounded seek boundary:

```text
1 failed, 55 deselected
AttributeError: no _generator_case_at_ordinal_non_evidence
```

### GREEN

`_generator_case_at_ordinal_non_evidence` now performs deterministic mixed-radix
unranking for every fixed Cartesian domain and a cumulative exact-rank lookup
for the heterogeneous unique-source-order domain. It covers all 31 literal
generators; there is no generic ordinal-only fallback. The public lazy iterator
is a thin ordinal generator over this same production case constructor, so
sequential and bounded-seek bytes cannot diverge.

Each case is checked at construction against a closed generator-specific set of
non-null `PREREQUISITE_CASE_INPUT_V1` fields. Arm, bank, variant, target,
transformation, property, amortized public-state, recomputation and symbolic
bundle dimensions are authority-derived in the descriptor order; canonical bank
aliases occur once and retain their complete role list. Out-of-range ordinals
fail closed.

The bounded test checks every generator at ordinals zero, one, midpoint and last
(deduplicated for singleton domains), verifies canonical bytes/input hashes,
case-ID uniqueness, exact ordinals, semantic dimension tuples and case-kind
non-null fields, and confirms iterator/seek equality for its first two rows. It
does not consume or materialize the formal sequence.

Focused GREEN:

```text
1 passed, 55 deselected in 0.90s
4 passed, 52 deselected in 3.79s  # C3B1 through C3B2A2
```

Final complete-file GREEN:

```text
56 passed in 72.80s
```

### Boundary

This completes lazy generator arithmetic/order coverage only. It does not begin
real toy factors, VE, across-bank DP, symbolic ledger semantics, formal packet
construction or evidence reduction. No formal packet, artifact, world, seed,
commit, push or tag was produced. Current card authority was read back as
`de434f911f3052cf288a01fcdff2cc6ecb17dbacdcfa04a7099d1ea14356d337`;
this lane did not edit it.


## C3B2B1 - closed symbolic operator primitives (private non-evidence)

### Authority and RED

Implementation resumed only after the hostile repair froze the complete
gate-to-contribution algebra, ternary PUBLIC-policy scopes, semantic projection,
fold ordering, toy motif, and operator counterexamples. The final authority
readback used for this substage was:

```text
5aefb07fde2dee95ba714796ab55fe57e894e24114ee03e8d16efbb224b23bd3
```

The retained hostile test first failed at the missing closed local-identity
callable:

```text
1 failed, 56 deselected
AttributeError: no _local_contribution_identity_non_evidence
```

No factor semantics were invented before that authority repair.

### GREEN

The private non-evidence implementation now provides:

- the exact `GATE_LOCAL_CONTRIBUTION_V1` identity and validator, including every
  fixed AND/OR field and all 19 controls in frozen positional order;
- bank-hash/complete-alias matching and fixed AND/OR local contribution merge;
- canonical complete assignment rows, exact relation-row/factor schemas,
  canonical byte hashing, sorting, and deduplication;
- compatible natural joins with left-major/right-minor canonical visitation and
  complete compatible-pair trace preimages;
- union elimination without merging mutually exclusive alternatives, including
  the hostile `A,B,A -> {A,B}` case;
- deterministic min-fill and complete elimination traces, including the frozen
  K2,2 order `a,b,c,d`;
- an exhaustive declared-scope probe that rejects outputs affected by an omitted
  leaf, plus a genuine ternary `T(x,y,p)` counterexample whose output changes
  with independently varied `p`;
- canonical global identity, across-bank AND/OR DP transitions, terminal fact
  derivation, and branches 5--11 through the existing exact branch partition.

Hostile coverage also exercises incompatible joins, compatible shared-variable
joins, wrong-bank rejection, mixed field/control AND/OR extrema, exact duplicate
projection removal, output-factor hashes, deterministic trace ordinals, and
hash-sorted bank/local/state DP traversal.

Focused GREEN:

```text
1 passed, 56 deselected in 0.53s
5 passed, 52 deselected in 4.51s  # C3B1 through C3B2B1
```

Final complete-file GREEN:

```text
57 passed in 79.95s
```

Python byte-compilation, source `--self-check`, and `git diff --check` all
exited zero. The self-check retained `formal_run_authorized=false` and all three
frozen authority receipts matched.

### Remaining C3B2B boundary

This is a closed operator substage, not full C3B2B and not gate evidence. The
real gate-factor descriptors/cells, exact live metric and semantic projections,
three-eligible-bank-per-median admission, deterministic capped motif, independent
explicit oracle, and all nine explicit-versus-VE-plus-DP equivalence rows remain
unimplemented. Consequently the nine execution-plan toy rows remain invalid
placeholders and must be replaced before C3B2B can close; they are not treated as
admitted by this substage. The current generic symbolic-state branch in the
public ledger validator is likewise not an admitted C3B2B validator and must be
replaced by exact closed symbolic validation before that public path may accept a
symbolic ledger.

No formal stream, packet, ledger, artifact, world, seed, experiment, verdict,
commit, push, or tag was created. These tests establish bounded implementation
behavior of private symbolic operators only. They do not prove that real factor
construction is correct, that the symbolic solver is equivalent on the frozen
toy suite, that the formal gate is executable, or that transfer headroom,
learning, AGI, agency, subjectivity, consciousness, or electronic life exists.


## C3B2B2 - real bounded factor layer and nine-row equivalence suite

### RED

The next hostile test required the plan to contain nine nonempty real toy rows,
a callable equivalence receipt, three eligible banks per median, binary-overlap
motif receipts, real ternary descriptors, literal structural anchors, and an
explicit oracle independent of VE operators. Initial RED was:

```text
1 failed, 57 deselected
AttributeError: no _small_instance_equivalence_receipt_non_evidence
```

The implementation card remained byte-identical at:

```text
5aefb07fde2dee95ba714796ab55fe57e894e24114ee03e8d16efbb224b23bd3
```

### Real factor construction

The implementation now derives exact leaf keys and domains from live
`query_decision` minimizer sets for the selected median, bank, arm, and H1
outcome. Authority-derived descriptors enumerate applicable role/target or
role/H1 points and map every literal gate ID to its unary, pair, or ternary arm
scope. PUBLIC remains an independently assigned third leaf for control Pareto,
no-update effect, and mask-effect predicates. Literal B_SEPARABLE and
B_COLLISION anchors use the bank's lexically first leaf and the card's exact
gate spelling.

Complete factor tables enumerate the Cartesian product of their declared live
domains, capped by the frozen 64-row maximum. Cells call the real target metric,
pairwise-common metric, semantic trace/projection, query decision, separable,
collision, decoy, or balanced-marginal producer required by their gate. The
closed contribution starts at the exact identity and each gate updates only its
registered fields in literal gate order. Factor/table validators require exact
schemas, complete ordered assignments, canonical bytes, adjacent hashes,
bank-bound contributions, scope/kind agreement, point-selector exclusivity,
factor-ID recomputation, and complete factor-hash recomputation.

### Motif, explicit oracle, and symbolic comparison

For every median the first three eligible banks were the same ascending hashes:

```text
01bbd7ef4fce7adaf517158185be56f79acac3069a6a06af7f7c38892134207c
038990dd480c7a5492f174ec3b14795e9ca2fb988ef7cc840a4c290b83b41cd4
04ed63771a0ca95ce98d9f3649d8bc28519aaa4b044de67f9ec021e5ed885ffb
```

Each admitted bank had the required F0/F1 binary overlap: three-variable union,
one shared leaf, both compatible and incompatible shared-value row pairs, and
at least two distinct contribution hashes. The capped selector then applied the
frozen optional all/equality, seen/failure, and one-endpoint projection order.
Selected real factors had maximum scope two and maximum table size four; this is
a measured property of the selected motifs, not a coded restriction. The real
authority descriptor set separately contains the mandatory ternary predicates,
while the B1 operator suite covers genuine ternary sensitivity.

The explicit oracle enumerates each complete three-leaf assignment and performs
factor-table lookup plus contribution merge in factor-hash order. Its code
object is checked against all VE helper names. The symbolic path converts the
same real factors into relations and runs min-fill elimination. Local reachable
contribution bytes match exactly. A separate explicit across-bank loop then
matches symbolic outer-DP terminal state rows and reachable branch lists for all
nine median x bank-count rows.

The former empty plan placeholders are replaced by real
`TOY_FACTOR_INSTANCE_V1` hashes and nonempty sorted leaf-key lists. Suite rows
remain in frozen median-major, count-minor order and the plan binds their exact
canonical suite hash.

### Measured runtime and verification

One clean measured build reported:

```text
lower               19.388387499988312 s
midpoint_integer    19.008608600008300 s
upper               19.067145500011975 s
total                61.088985599984880 s
eligible banks       3 per median (preflight stops after the required third)
maximum scope        2
maximum table rows   4
```

Focused GREEN:

```text
1 passed, 57 deselected in 62.02s
```

Final complete-file GREEN, which intentionally reloads the module in separate
tests and therefore recomputes the bounded suite more than once:

```text
58 passed in 382.62s
```

Python byte-compilation, source `--self-check`, and `git diff --check` exited
zero. Self-check retained `formal_run_authorized=false` and exact frozen
authority matches.

### Boundary

This closes the bounded real-factor and nine-row positive-control layer only.
It does not execute the formal 76-bank symbolic DP, materialize a formal stream,
validate a complete symbolic ledger, consume a packet, reduce gate evidence, or
produce an artifact or verdict. The public symbolic-ledger validator still
requires its later exact deep-schema closure before formal use.

No world, seed, pilot, threshold tuning, artifact, commit, push, or tag was
created. Nine bounded equivalence rows do not prove general VE correctness,
transfer headroom, learning, AGI, agency, subjectivity, consciousness, or
electronic life.


## C3B2B2-R1 and C3B2C - hostile repair, deep closure, and I1 fail-closed boundary

### Normative authority and fixed scope

The finalized I1 implementation-card authority used for this closeout is:

~~~
5aefb07fde2dee95ba714796ab55fe57e894e24114ee03e8d16efbb224b23bd3
~~~

Only the exact four I1 paths are present in the worktree: the I1 card, source,
tests, and this report. The frozen 001D card, collision record, and
FROZEN_DESIGN.json remain byte-identical at their pinned hashes. No artifact,
formal packet, complete ledger, world, seed, pilot, output directory, push, or
tag was created.

### C3B2B2 hostile repairs

Two retained hostile tests were written before their production fixes:

1. the source-delete factor had to invoke the registered ABL_SOURCE_DELETE
   callable and fail if that path was disconnected, rather than compare two
   direct canonical-PUBLIC calls;
2. the toy motif had to bind the first structurally compatible F1 and make the
   bank ineligible if that exact F1 failed its compatibility/contribution
   receipt, rather than skip to a later passing factor;
3. VE had to sort original incident factors by their complete real
   factor_sha256, not by a relation-only surrogate hash.

Observed REDs included the registered-source-delete spy failure and the missing
factor_sha256s VE interface. Focused GREEN after the repairs:

~~~
2 passed, 58 deselected in 0.90s
~~~

The real nine-row factor/equivalence positive control remained admitted with the
fixed F1 rule:

~~~
1 passed, 58 deselected in 126.76s
~~~

The selected bank identities changed after the fixed-first-F1 correction;
therefore earlier B2B2 bank hashes are historical diagnostics and are not
reported as current frozen result evidence.

### C3B2C1 - exact ledger and symbolic-state validation

RED was observed before implementation:

~~~
AttributeError: no _validate_query_policy_row_non_evidence
~~~

A second retained RED showed that nonempty junk symbolic lists such as
leaf_variable_rows=[{}] could pass the old shallow wrapper.

The completed validators now require:

- every lexical and symbolic ledger policy row to equal the live recomputed
  lexical choice, not merely any exact minimizer;
- complete ordered policy and envelope domains;
- envelope bank aliases/hash, target, stratum, distance, source occurrence,
  scorer truth, one metric row, empty artifact receipts, and byte-exact live
  metric recomputation;
- exactly six ledgers in normative variant order, with symbolic policy and
  envelope hashes byte-anchored to the same-median lexical ledger;
- nonempty reachable ordinary branches and exactly one branch for a lexical
  ledger;
- exact symbolic leaf-variable coverage and live minimizer domains;
- complete real factor descriptors/tables, live cell recomputation, factor
  hashes, global factor order, min-fill VE traces, local-state rows, outer-DP
  transitions, terminal rows, reachable branches, initial identity, and the
  exact nine-row equivalence-suite hash.

The symbolic validator accepts only the closed JSON wire representation of
canonical byte fields and recomputes the complete graph/DP content. A nonempty
list or matching self-hash is not sufficient.

Focused final C3B2C1 GREEN:

~~~
1 passed, 63 deselected in 118.64s
~~~

### C3B2C2 - deep prerequisite packet semantics

The initial retained test observed:

~~~
2 failed, 60 deselected in 209.96s
~~~

The failures were the missing ledger-row callable and acceptance of an empty
BANK_COVERAGE_OUTPUT_V1 payload with a matching wrapper hash.

The bounded-prefix validator now enforces exact producer ID, deterministic
producer-function mapping, singleton wrapper call count, producer-specific
output-schema ID, canonical output bytes/hash, and closed ID-specific child
schemas. It validates authority, bank, arm-coverage, semantic comparison,
source-order lineage, property, leakage, amortized comparison, and recompute
wrappers. Fresh/independent recompute receipts have a closed schema, exact
producer/input linkage, canonical receipt hash, child-output hashes, and the
strict ordering:

~~~
recompute_start_ordinal < recompute_complete_ordinal < stored_bundle_read_ordinal
~~~

A valid bounded bank prefix passes the private non-evidence helper; an empty
object under the bank wrapper, an arbitrary producer function, and an inverted
pre-read order are rejected. The public packet validator still rejects any
incomplete formal collection.

### C3B2C3 - public reducer refusal and synthetic-only dispatch

The public APIs were tested before implementation and failed with:

~~~
AttributeError: no reduce_gate_evidence
AttributeError: no dispatch_gate_reduction
~~~

reduce_gate_evidence(plan, ledgers, packet) now has the exact positional
boundary. It validates the plan, six ledger headers/order/anchors, every complete
ledger, and the bounded packet structure, then raises
FormalRunNotAuthorized before any GATE_REDUCTION_V1 can be returned. Its AST
call graph contains neither the synthetic truth-table helper nor the dispatch
callable.

dispatch_gate_reduction is separate. It validates the exact closed reduction
shape, hashes, coverage summary, explanation-row schemas, rational/hash fields,
derived cores/joints, structural control match, median map/sensitivity,
ordinary branch, claim ceiling, and stored verdict. It recomputes first-true
priority exactly:

~~~
leakage -> instrument invalid -> median sensitive -> query sensitive
        -> ordinary branch 5..11
~~~

It is a synthetic dispatch-coverage boundary only and does not turn a supplied
object into evidence.

Focused GREEN:

~~~
2 passed, 62 deselected in 0.27s
~~~

### Final verification

Focused C3B1/C3B2 run:

~~~
12 passed, 52 deselected in 842.99s
~~~

Complete I1 test file:

~~~
64 passed in 924.41s
~~~

Python byte compilation, source self-check, and git diff --check all exited
zero. The no-artifact self-check reports all three frozen authority hashes
matching, 75 primary plus four property roles, 45 arms, 13 ablations, 11
verdicts, 24/24 leakage positive controls rejected, and
formal_run_authorized=false.

Final implementation bytes before this report append:

~~~
source  abb91bcccd218c38b100059fccc54235b1d46bee55e8389ce502a40454ea6a6f
tests   09c163707a6e45af2acaad849a01fb24b677d5a06ece26cde1179da3b470575a
card    5aefb07fde2dee95ba714796ab55fe57e894e24114ee03e8d16efbb224b23bd3
~~~

### Review and independence boundary

Earlier statistical, data-flow, and hostile roles were same-model subagents and
are internal role separation only, not external independent audit. Their
retained source-delete/F1/factor-order blockers were fixed and regression-tested.
The configured subagent quota was exhausted before a new post-C3B2C reviewer
could run. The root lane therefore performed a final read-only AST/data-flow,
exact-path, full-test, self-check, hash, and hostile-schema pass. This is still
same-model internal review; no external or model-independent reviewer is
claimed.

### Final I1 verdict and claim ceiling

I1 implementation verdict:

~~~
I1_IMPLEMENTATION_COMPLETE_LOCAL_ONLY__FORMAL_RUN_NOT_AUTHORIZED
~~~

This means the static exact evaluator, private symbolic machinery, strict
validators, fail-closed evidence boundary, and synthetic dispatch coverage are
implemented and locally verified. It does not mean that the formal 001D
preflight ran or passed.

The next allowed action is a separate 001D-I2-PRE-RUN-PROVENANCE card/commit
that binds finalized I1 bytes, Python and pytest versions, standard-library
dependency receipt, exact formal command, artifact allowlist, packet-stream
framing/incremental hash, and independent recomputation path. I1 itself does not
authorize that run.

This result proves no transfer headroom, learned representation,
non-memorization, self-learned transfer-selection method, neural emergence,
held-out adaptation, survival benefit, AGI, agency, consciousness, subjectivity,
emotion, companion readiness, or electronic life.
