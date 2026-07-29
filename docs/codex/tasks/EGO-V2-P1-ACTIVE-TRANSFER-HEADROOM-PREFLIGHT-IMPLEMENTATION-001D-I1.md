# EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-IMPLEMENTATION-001D-I1

> **For agentic workers:** execute the task blocks in order with test-first red/green cycles. Do not generate formal evidence until a separate post-implementation pre-run provenance card binds finalized source/test/dependency hashes.

## Task contract

- **Task ID:** `EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-IMPLEMENTATION-001D-I1`
- **Task type:** implementation-only TDD realization of the frozen 001D exact static evaluator.
- **Layer:** engineering implementation of a bounded learning/adaptation mechanism preflight; no product behavior.
- **Repository root:** `D:\Project\AIProject\MyProject\Ego`
- **Branch:** `codex/ego-v2-active-transfer-headroom-001d`
- **Parent commit:** `3101b5f93dc465299bffc36654d11c476310e9f5`
- **Current stage:** implement callable computation paths and tests only. Formal artifact generation and verdict adjudication are forbidden in I1.
- **Problem definition:** implement the frozen 001D finite Bayesian/decision-theoretic evaluator without adding inference, arm, bank, threshold, schema, or verdict freedom.
- **Hypothesis:** the frozen design can be represented as deterministic standard-library Python callables whose bank construction, public-state transition, inference, acquisition, decisions, metrics, baselines, ablations, controls, dispatch, replay preparation, and failure paths are testable without world/seed input.
- **Primary baseline:** `PUBLIC_L1_RISK_DP` exactly as frozen.
- **Strong invalidating baseline:** `BANK_CONSISTENCY_L1_RISK_DP` plus the full 19-arm structural invalidating set.
- **Ceiling control:** `CANDIDATE_RULE_AMORTIZED_LOOKUP`, outside the 45 learner-arm registry and expected to byte-match the primary in-suite.
- **Ablation:** all 13 frozen ablation/invariance IDs; tests must exercise actual registered call paths, not literals.
- **Trace/replay requirement:** implementation exposes row/state serialization and pure recomputation callables. A later run card must invoke a fresh process and an independent implementation path before consuming stored verdicts.
- **Acceptance gate:** exact authority readback; all required tests first observed failing for missing behavior then passing; 75+4 bank roles, 45 arms, 13 ablations, 11 verdicts and schema fields match frozen design; positive-control failures are detected; source deletion aliases the canonical scratch callable; no formal artifacts are written.
- **Claim ceiling:** implementation existence and local test evidence only. No mechanism effectiveness, headroom result, learning, non-memorization, product effect, neural emergence, held-out effect, survival benefit, AGI, agency, consciousness, subjectivity, emotion, companion readiness, or electronic-life evidence.
- **Stop condition:** stop on any parent hash drift, design ambiguity, dependency addition, hidden-truth access by an arm, dynamically synthesized unregistered arm, literal pass report, test-only alternate logic path, artifact write, world/seed access, or need to change frozen thresholds/banks/verdicts.
- **Rollback plan:** revert only this successor's uncommitted/committed files with a successor revert commit. Never amend/reset/rewrite 001D or R5--R7 evidence.
- **Auto-Remote-Anchor:** `forbidden`.

## Frozen authority

| Role | Path | SHA-256 |
|---|---|---|
| 001D card | `docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D.md` | `c9a7d71dcd92b0bc4571a4e5aa975e04fc97485d47b23b826894f13cac96072e` |
| 001D collision | `docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/COLLISION_RECORD.md` | `75e870cd638e58949e48ff0a3ea42101d71279196905cc461b1aa996762a0ae1` |
| 001D design | `docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/FROZEN_DESIGN.json` | `f54b998bf952f662b92f4734517cdb1405b63a4f75258eb6c5de917174970916` |

The implementation must load and validate `FROZEN_DESIGN.json`; it may not duplicate a smaller permissive design dictionary. Current parent hashes are normative; future producer/test hashes do not yet exist and therefore are not authority fields in I1.

## Exact paths and dependency policy

Allowed files for I1:

1. `docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-IMPLEMENTATION-001D-I1.md`
2. `docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md`
3. `scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py`
4. `scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py`

No other path may change. Runtime dependency policy is Python standard library only. Test dependency is the repository's existing `pytest`; no install, lockfile, environment, or configuration change is authorized.

The source file is the sole production implementation path. Tests import that exact file with `importlib.util`; they may not contain a second evaluator. Shared test helpers may construct small banks and expected primitive values, but may not reproduce a gate or verdict implementation.

## Required public interfaces

The source must expose these callable boundaries; signatures may add type aliases but not semantic parameters:

```python
load_frozen_design() -> dict
authority_receipts() -> list[dict]
validate_frozen_registry(design: dict) -> dict
canonical_mapping_bytes(mapping: tuple[int, ...]) -> bytes
canonical_bank_bytes(bank: tuple[tuple[int, ...], ...]) -> bytes
mapping_space() -> tuple[tuple[int, ...], ...]
build_hash_bank(index: int) -> tuple[tuple[int, ...], ...]
build_multiplicity_bank(partition: tuple[int, ...]) -> tuple[tuple[int, ...], ...]
scan_property_banks() -> dict[str, dict]
source_counts(bank) -> tuple[int, ...]
local_counts(bank) -> tuple[int, ...]
build_state(arm_id: str, bank, public_history, *, median_convention: str) -> dict
validate_public_input(payload: dict) -> dict
validate_state(payload: dict) -> dict
query_decision(arm_id: str, bank, public_history, *, median_convention: str) -> dict
prediction_decision(arm_id: str, bank, public_history, *, median_convention: str) -> dict
evaluate_target(bank, target_mapping, arm_id: str, *, median_convention: str, query_policy=None) -> dict
evaluate_bank(bank_role_ids, bank, *, median_convention: str, query_policies=None) -> list[dict]
build_amortized_lookup(banks) -> dict
lookup_query_or_prediction(table: dict, public_payload: dict) -> dict
build_gate_execution_plan() -> dict
validate_gate_execution_plan(plan: dict) -> dict
iter_expected_prerequisite_cases(plan: dict)
validate_gate_variant_ledger(plan: dict, ledger: dict) -> dict
validate_gate_prerequisite_packet(plan: dict, packet: dict) -> dict
reduce_gate_evidence(plan: dict, ledgers: list[dict], packet: dict) -> dict
dispatch_gate_reduction(reduction: dict) -> str
run_leakage_positive_controls() -> dict
build_development_report(*, exhaustive: bool) -> dict
main(argv: list[str] | None = None) -> int
```

`_synthetic_dispatch_truth_table_non_evidence` may exist only as a private pure
truth-table test helper. The formal evidence reducer never calls it, and its
synthetic facts are never evidence inputs.

`build_development_report(exhaustive=False)` is a no-artifact diagnostic that validates authority, registries, primitive bank construction, property-role existence, schema rejection, and callable reachability. `exhaustive=True` is reserved for the later run card and I1 tests must assert that calling it raises `FormalRunNotAuthorized`.

`main` in I1 accepts only `--self-check`; it prints a compact diagnostic JSON to stdout and writes no file. Any artifact/output-dir/formal flag is rejected.

## TDD implementation plan

### Task 1 — Authority, frozen registry, and CLI refusal

**RED:** add tests that import the absent source, verify the three authority hashes, require exactly 75 primary roles, four property roles, 45 unique arm records, 13 unique ablations, 11 ordered verdicts, and assert formal/exhaustive CLI paths are rejected.

**Expected red command:**

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "authority or registry or formal" -q
```

It must fail because the production module/callables do not exist, not because of a test syntax/import typo.

**GREEN:** implement design loading, SHA receipts, registry cross-reference validation, `FormalRunNotAuthorized`, no-artifact `--self-check`, and formal refusal. Re-run the same tests.

### Task 2 — Canonical grammar and hostile banks

**RED:** test 120 lexicographic mappings, compact bytes, hash/multiplicity determinism, duplicate retention, alias canonicalization, exact partitions/role IDs, property witness predicates, lowest-index scan, and a positive control where a label-insensitive balanced-marginal shortcut is rejected.

**Expected red command:**

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "mapping or bank or property" -q
```

**GREEN:** implement only the bank and property callables required by these tests. Property scanning must derive results; no expected scan index or bank bytes may be embedded in production code.

### Task 3 — Closed schema and canonical state transitions

**RED:** test every exact schema key set, reduced rational normalization, wrong key/type/range rejection, same-arm H1/H2 truth noninterference, cross-arm exogenous equality, source-order canonicalization, and exact incoming/sealed family contribution arrays for every inference transition including consistency fallback, no-update, H2 mask, flat, no-local, sham, and transfer-then-scratch.

**Expected red command:**

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "schema or state or history" -q
```

**GREEN:** implement strict validators and state construction. State is semantically recomputed before validation; no state field is trusted because it is present.

### Task 4 — Exact L1 decisions and acquisition

**RED:** test weighted-median lower/midpoint/upper endpoints, half-even negative/positive ties, identical minimal L1 risk, exact lower-5% quantile, scratch fallback, hypothetical-H2 LCB recomputation, L1-EVSI exclusion of queried tokens, EIG integer-product ordering, lexical ties, and exact EIG/maximum-outcome-entropy alias equality under all three required inferences.

**Expected red command:**

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "median or lcb or evsi or eig or entropy" -q
```

**GREEN:** implement decision/acquisition paths with integers and `fractions.Fraction` only. No float may affect a choice, score, gate, or verdict.

### Task 5 — Full arm registry, rows, decomposition, and baselines

**RED:** test each of the 45 registered records is dispatched through a real callable; extra arm rejection; observed-token copying; denominators 20/12/8/16; full/common/query-asymmetry identity; same-H2 scratch comparison; all 120 targets; distinct-member versus entry weighting; source deletion exact alias; all 19 structural controls; and four-fixed-branch uniform expectation without a synthetic prediction.

**Expected red command:**

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "arm or target or metric or baseline or decomposition" -q
```

**GREEN:** implement arm dispatch, target/bank evaluation, exact rational metric rows, and the callable baseline paths. No test-only dispatch or precomputed pass row is allowed.

### Task 6 — Ablations, invariances, leakage, and amortized ceiling

**RED:** test all 13 IDs invoke registered paths; source delete uses canonical scratch callable identity; local/no-update/mask/postquery/sham/flatten transforms have frozen semantics; source order, token relabel, prototype relabel, and EIG alias invariances have positive and negative controls; forbidden direct/encoded fields are rejected; amortized table keys contain only canonical public state and byte-match candidate outputs.

**Expected red command:**

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "ablation or invariant or leakage or amortized" -q
```

**GREEN:** implement actual transform/recompute paths and separate amortized builder/lookup callables. The leakage positive control must fail if the scanner is replaced by an unconditional clean report.

### Task 7 — Gate inputs, Boolean dispatch, replay preparation, and full tests

**RED:** use the private non-evidence truth-table helper to prove branches 5--11 exhaustive/disjoint and first-true priority, then separately test the closed plan/ledger/prerequisite validators and evidence reducer; test lazy case-generator bounded prefixes and exact count/digest formulas without materializing the formal sequence, source-order proof-by-construction plus its bypass sabotage, literal gate/role pair registries, leaf-factor schemas, deterministic min-fill order, compatible joins, union elimination, byte deduplication, all nine bounded explicit-enumeration positive controls, median/query sensitivity, raw-tail versus selection versus attribution, bounded versus strict, structural control match, exact streaming coverage failure, rejection of stored winners/verdicts, and rejection of a full actual-bank arm-policy Cartesian path. Bounded prefix/count tests are implementation checks, never synthetic success evidence.

**Expected red command:**

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -k "gate or verdict or replay" -q
```

**GREEN:** implement exact gate-input reduction and dispatch only. Do not execute the exhaustive 75+4 x 120 formal evaluation and do not write artifacts.

Finally run:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py -q
python -m py_compile scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py
python scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py --self-check
git diff --check
```

## Implementation completion and provenance phase

I1 completion requires:

1. exact four-path changed set for the implementation commit;
2. test report recording each red failure reason and final green command;
3. no formal artifacts, output directory, seed/world input, or stored verdict;
4. same-model internal code/data-flow/hostile review plus a final read-only review;
5. local commit only, no push/tag.

After I1 is final and reviewed, a separate `001D-I2-PRE-RUN-PROVENANCE` card must bind:

- finalized I1 card hash;
- finalized producer hash;
- finalized test hash;
- exact Python/pytest versions and standard-library-only dependency receipt;
- exact formal command and artifact allowlist;
- independent recomputation implementation/path hash;
- stop conditions for drift before formal execution.

I1 itself may not create I2 evidence or run the formal preflight.

## What I1 cannot prove

Passing implementation tests proves neither the frozen statistical hypothesis nor any effect. The amortized lookup is intentionally expected to match in-suite. Only a later hash-bound formal run can adjudicate the bounded algorithmic reference, and only a later fresh-bank learned candidate can address non-memorization or self-learned adaptation.

## Pre-C3 normative clarification — closed gate-reduction authority repair

### I1/I2 reducer boundary clarification

This paragraph resolves the remaining phase contradiction discovered before a
successful C3B evidence reduction existed.  In I1, the complete prerequisite
packet is an ordered stream, while its framing, incremental packet hash,
finalized producer/source/dependency hashes, and formal construction are
explicitly deferred to I2.  Therefore I1 has no authority to create the
`prerequisite_packet_sha256` required by `GATE_REDUCTION_V1` and must not
manufacture a materialized-JSON substitute.

Accordingly, in I1:

* `reduce_gate_evidence(plan, ledgers, packet)` must expose the public boundary,
  validate every portion that can be validated without consuming a formal
  packet, and then fail closed with `FormalRunNotAuthorized` before returning a
  `GATE_REDUCTION_V1` result;
* its successful evidence-producing path remains unreachable until the separate
  I2 pre-run provenance card freezes the packet-stream framing and digest,
  finalized source/test/dependency hashes, formal command, and independent
  producer path;
* bounded tests may exercise factor construction, relational elimination,
  across-bank DP, terminal branch derivation, reduction primitives, strict
  validators, and reducer failure paths through explicitly private
  `_non_evidence` helpers, but such helpers must not accept a formal packet,
  emit `GATE_REDUCTION_V1`, or be called by a later evidence route;
* `dispatch_gate_reduction` may be tested only for closed-schema validation and
  recomputation of dispatch priority from a supplied reduction-shaped object;
  that test is synthetic dispatch coverage, not evidence that the public
  reducer succeeded.

This phase boundary supersedes the Task 7 wording that otherwise appears to
require a successful evidence-reducer fixture inside I1.  I1 tests must instead
require the public reducer to fail closed for the unbound I2 provenance/stream
contract.  This clarification changes no frozen bank, arm, threshold, factor,
branch, verdict, scientific predicate, or formal result.

This section repairs implementation-card underspecification found before any C3
gate code or formal result existed. It does not change a frozen 001D bank, arm,
ablation, threshold, scientific predicate, verdict, or claim ceiling. It adds no
result-dependent freedom. C3 remains inside the same four I1 allowed paths; no
formal run, artifact, commit, push, or tag is authorized here.

### Closed `ARM_TARGET_METRIC_V1`

A trajectory metric row has exactly these keys and rejects every extra key:

```text
schema_version
arm_id
target_mapping
selected_query_token
public_selected_query_token
query_decision
public_query_decision
prediction_decision
public_prediction_decision
same_history_scratch_prediction_decision
used_transfer
candidate_own_unqueried_tokens
baseline_own_unqueried_tokens
common_unqueried_tokens
candidate_token_losses_raw
baseline_token_losses_raw
same_history_scratch_token_losses_raw
candidate_full_loss_raw
baseline_full_loss_raw
candidate_own_unqueried_loss_raw
baseline_own_unqueried_loss_raw
candidate_common_unqueried_loss_raw
baseline_common_unqueried_loss_raw
same_history_scratch_loss_raw
full_improvement_raw
common_raw
query_asymmetry_raw
same_history_forward_raw
metric_denominators
metric_rationals
```

`target_mapping` is a five-int permutation. The two selected-query fields are
integer-or-null. The three query objects use the exact frozen
`QUERY_DECISION_V1` key set, including `{token_index,int_score}` exact-score
rows. The three prediction objects use the exact frozen
`PREDICTION_DECISION_V1` key set. `used_transfer` equals the candidate
prediction's five-boolean field. Each token-index or raw-token-loss vector has
length five and exact integer entries. `metric_denominators` has exactly
`{full,own_unqueried,common_unqueried,same_history_forward}`.
`metric_rationals` has exactly:

```text
candidate_full_endpoint_mae
baseline_full_endpoint_mae
full_endpoint_improvement
candidate_own_unqueried_forward_mae
baseline_own_unqueried_forward_mae
candidate_common_unqueried_forward_mae
baseline_common_unqueried_forward_mae
common_unqueried_forward_improvement
candidate_same_history_forward_mae
same_history_scratch_forward_mae
same_history_forward_improvement
common_contribution_to_full_improvement
query_asymmetry_contribution_to_full_improvement
```

Every rational is exact reduced `{n,d}`. The reducer recomputes all losses,
denominators, decomposition identities, and rationals from prediction bytes and
verifier truth. Presence of these fields is never sufficient evidence.

### Four closed C3 schemas

All four schemas reject missing or extra keys. Nested canonical-JSON byte fields
must decode to the named closed schema or to the ID-specific tuple defined
below; they are not free-form dictionaries.

`GATE_EXECUTION_PLAN_V1` has exactly:

```text
schema_version
authority_sha256
primary_role_ids
property_role_ids
arm_ids
ablation_ids
bank_groups
median_conventions
query_sensitivity_execution_mode
variant_registry
query_sensitivity_pairs
small_instance_equivalence_suite
small_instance_equivalence_suite_sha256
prerequisite_case_plan
thresholds
ordinary_branch_ids
```

Each `bank_groups` row has exactly
`{canonical_bank_sha256,canonical_bank,role_ids,canonical_member,target_mappings}`.
The hash fields are lowercase 64-hex SHA-256 strings; mappings are closed
five-int permutations; role IDs are sorted exact registered strings; targets
are the complete sorted 120-mapping space. `authority_sha256` is the SHA-256 of
canonical JSON bytes of the sorted three-row `{path,sha256}` frozen-authority
preimage, not an opaque caller label. `thresholds` has exactly the frozen
threshold key set and exact reduced `{n,d}` values. `median_conventions` is
exactly `[lower,midpoint_integer,upper]`; `query_sensitivity_execution_mode` is
the literal `symbolic_global_policy_dp_v1`; and `ordinary_branch_ids` is exactly
`[5,6,7,8,9,10,11]`. There is no run-time feasibility choice and no alternate
concrete-global execution mode.
The producer reconstructs all 75 primary plus four property role labels from
the frozen constructors, groups by canonical bank bytes, and requires every
alias label in its complete group. Current authority reconstructs 79 labels into
76 groups, but `76` is a readback, not a coded acceptance constant: role and
group counts are always derived. `canonical_member` is fixed before evaluation
as the lexicographically smallest distinct source mapping. All 120 targets and
all 45 arms remain required per group.

`variant_registry` is exactly these six rows, in this order, with no generated
or caller-selected seventh row:

```text
{variant_id:MEDIAN_LOWER__LEXICAL,median_convention:lower,variant_kind:lexical}
{variant_id:MEDIAN_LOWER__SYMBOLIC_GLOBAL_POLICY_DP_V1,median_convention:lower,variant_kind:symbolic_global_policy_dp_v1}
{variant_id:MEDIAN_MIDPOINT_INTEGER__LEXICAL,median_convention:midpoint_integer,variant_kind:lexical}
{variant_id:MEDIAN_MIDPOINT_INTEGER__SYMBOLIC_GLOBAL_POLICY_DP_V1,median_convention:midpoint_integer,variant_kind:symbolic_global_policy_dp_v1}
{variant_id:MEDIAN_UPPER__LEXICAL,median_convention:upper,variant_kind:lexical}
{variant_id:MEDIAN_UPPER__SYMBOLIC_GLOBAL_POLICY_DP_V1,median_convention:upper,variant_kind:symbolic_global_policy_dp_v1}
```

Thus `L=len(variant_registry)=6`. Every ledger/packet
`execution_plan_sha256` is `SHA256(canonical_json_bytes(the complete validated
GATE_EXECUTION_PLAN_V1))`; `authority_sha256` remains the hash of the sorted
three-row authority preimage above. Every other `*_sha256` in this section is
`SHA256` of the named canonical bytes, never a label or a hash of an unnamed
subset.

Here `canonical_json_bytes(x)` means UTF-8 of standard-library
`json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False,
allow_nan=False)`. The authority preimage is exactly the three
`{path,sha256}` rows sorted by `path`; policy, envelope, equivalence-suite, and
ledger hashes cover their complete validated row/list/object respectively.
`symbolic_dp_sha256` covers the complete validated `GATE_SYMBOLIC_QUERY_DP_V1`;
`prerequisite_packet_sha256` covers the complete validated packet. No object
includes its own hash field in its own preimage; wrapper hashes cover the
already-hashed child object.

Each `query_sensitivity_pairs` row has exactly
`{pair_id,gate_ids,left_arm_id,right_arm_id,role_ids}`. Define the following
literal arm aliases (these aliases are plan-builder constants, not caller
input):

```text
C = ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK
R = ARM_I_TRANSFER__A_L1_EVSI__D_L1_MEDIAN
P = ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1
K19 = the frozen 19 invalidating_control_ids in frozen-design order
PRIMARY75 = the exact sorted 75 strings in plan.primary_role_ids
ALL79 = the exact sorted union of plan.primary_role_ids and plan.property_role_ids
```

The exact pair generator matrix is below. Each bracket is the literal ordered
`gate_ids` list; `PRIMARY75` rows carry exactly 75 role IDs, property rows carry
the displayed singleton, and `ALL79` rows carry exactly all 79 role IDs.

| pair family | left/right generator | literal `gate_ids` | exact `role_ids` |
|---|---|---|---|
| conservative/PUBLIC | `(C,P)` | `[MEMBER_FORWARD_CONSERVATIVE,SOURCE_DELETE]` | `PRIMARY75` |
| raw/PUBLIC | `(R,P)` | `[MEMBER_FORWARD_RAW]` | `PRIMARY75` |
| structural controls | `(C,K)` for each `K` in `K19`; when `K=ARM_I_CONSISTENCY__A_L1_EVSI__D_L1_MEDIAN` append the second ID | `[CONTROL_PARETO:<K>]`, or `[CONTROL_PARETO:<K>,CONSISTENCY_POSITIVE_NON_EQUIVALENCE]` for that exact consistency arm | `PRIMARY75` |
| local-delete effect | `(C,ARM_I_TRANSFER_NO_LOCAL__A_L1_EVSI__D_LCB05_FALLBACK)` | `[CAUSAL_EFFECT:ABL_LOCAL_SHIFT_DELETE]` | `PRIMARY75` |
| no-update EVSI effect | `(C,ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK)` | `[CAUSAL_EFFECT:ABL_NO_UPDATE]` | `PRIMARY75` |
| no-update passive effect | `(C,ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK)` | `[CAUSAL_EFFECT:ABL_NO_UPDATE]` | `PRIMARY75` |
| active-delete effect | `(C,ARM_I_TRANSFER__A_PASSIVE__D_LCB05_FALLBACK)` | `[CAUSAL_EFFECT:ABL_ACTIVE_DELETE]` | `[B_SEPARABLE]` |
| mask effect | `(C,ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK)` | `[CAUSAL_EFFECT:ABL_QUERY_OUTCOME_MASK]` | `PRIMARY75` |
| postquery-delete effect | `(C,ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1)` | `[CAUSAL_EFFECT:ABL_POSTQUERY_SOURCE_DELETE]` | `PRIMARY75` |
| sham LCB effect | `(C,ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK)` | `[CAUSAL_EFFECT:ABL_SHAM_ROTATION]` | `PRIMARY75` |
| sham raw effect | `(C,ARM_I_SHAM__A_L1_EVSI__D_L1_MEDIAN)` | `[CAUSAL_EFFECT:ABL_SHAM_ROTATION]` | `PRIMARY75` |
| flatten effect | `(C,ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK)` | `[CAUSAL_EFFECT:ABL_MULTIPLICITY_FLATTEN]` | `[MULT_6]` |
| no-update EVSI failure | `(ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK,P)` | `[MEMBER_FAILURE:ABL_NO_UPDATE]` | `PRIMARY75` |
| no-update passive failure | `(ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK,P)` | `[MEMBER_FAILURE:ABL_NO_UPDATE]` | `PRIMARY75` |
| mask failure | `(ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK,P)` | `[MEMBER_FAILURE:ABL_QUERY_OUTCOME_MASK]` | `PRIMARY75` |
| postquery-delete failure | `(ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1,P)` | `[MEMBER_FAILURE:ABL_POSTQUERY_SOURCE_DELETE]` | `PRIMARY75` |
| sham LCB failure | `(ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK,P)` | `[MEMBER_FAILURE:ABL_SHAM_ROTATION]` | `PRIMARY75` |
| sham raw failure | `(ARM_I_SHAM__A_L1_EVSI__D_L1_MEDIAN,P)` | `[MEMBER_FAILURE:ABL_SHAM_ROTATION]` | `PRIMARY75` |
| decoy | `(ARM_I_TRANSFER__A_EIG__D_L1_MEDIAN,R)` | `[PROPERTY_B_DECOY]` | `[B_DECOY]` |
| balanced marginal | `(ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN,ARM_I_CONSISTENCY__A_MAX_OUTCOME_ENTROPY__D_L1_MEDIAN)` | `[PROPERTY_B_BALANCED_MARGINAL]` | `[B_BALANCED_MARGINAL]` |
| multiplicity | `(C,ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK)` | `[PROPERTY_MULT_6]` | `[MULT_6]` |

Identical `(gate_ids,left,right,role_ids)` rows produced twice are deduplicated
before sorting. `pair_id` is exactly
`SHA256(UTF8("QPAIR" + U+001F + compact_json(sorted(gate_ids)) + U+001F +
left_arm_id + U+001F + right_arm_id + U+001F +
compact_json(sorted(role_ids))))`. No aggregate or no-query arm is admitted.
The reachable query-sensitivity domain is only ordinary branches 5--11.
`INV_EIG_ENTROPY_ALIAS` is checked exclusively by its prerequisite cases and
never contributes a query-sensitivity pair or reachable-branch factor.

`prerequisite_case_plan` has exactly
`{schema_version,generator_rows,expected_case_count,case_order,case_id_digest_algorithm}`.
Each generator row has exactly
`{generator_id,case_kind,scope_id,dimension_descriptor,dimension_keys,count_formula_id,expected_count,expected_producer_ids,packet_collection}`.
`dimension_descriptor` is a closed ID-specific canonical object containing only
the dimensions and exact enum/range/generator IDs already frozen in the matrix
and mapping table below; arbitrary predicates, callbacks, or materialized case
lists are rejected. `expected_case_count` is the exact arbitrary-precision sum
of all generator-row counts. `case_order` is exactly
`generator_rows list order, then lexicographic product in descriptor dimension
order`. `case_id_digest_algorithm` is exactly
`SHA256_LENGTH_PREFIXED_CASE_IDS_V1`, namely streaming SHA-256 over
`uint32_be(len(UTF8(case_id))) || UTF8(case_id)` in that order.

`iter_expected_prerequisite_cases(plan)` lazily yields rows with exactly
`{case_id,case_kind,scope_id,canonical_input_bytes,input_sha256,expected_producer_ids}`.
Its bytes decode to `PREREQUISITE_CASE_INPUT_V1` with exactly
`{schema_version,generator_id,case_kind,scope_id,canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id,transformation_id,public_state_key,ordinal}`;
unused slots are null under case-kind-specific validation. `case_id` is
`SHA256(UTF8(generator_id + U+001F + case_kind + U+001F) || canonical_input_bytes)`, and
`input_sha256` is the SHA-256 of the bytes alone. Plan construction and I1
validation must never materialize this iterator as a list or set.

Let `B=len(bank_groups)`, `L=len(variant_registry)=6`, `T=42` trajectory arms,
and `G=3` aggregate arms. The exact enums are:

```text
case_kind = AUTHORITY_HASH | BANK_COVERAGE | ARM_ROW_COVERAGE | ABLATION_SEMANTIC |
  INVARIANCE_SEMANTIC | PROPERTY_WITNESS | LEAKAGE_POSITIVE_CONTROL |
  AMORTIZED_PUBLIC_STATE | FRESH_PROCESS_TRAJECTORY_RECOMPUTE |
  FRESH_PROCESS_AGGREGATE_RECOMPUTE | INDEPENDENT_TRAJECTORY_RECOMPUTE |
  INDEPENDENT_AGGREGATE_RECOMPUTE | SYMBOLIC_LOCAL_CONTRIBUTION |
  SYMBOLIC_LOCAL_AGGREGATE
transformation_id = NONE | SOURCE_ORDER:<zero_based_lexical_rank> |
  SOURCE_ORDER_CALL_CHAIN:<arm_id> | SOURCE_ORDER_SABOTAGE |
  TOKEN_PERM:<zero_based_lexical_rank> | PROTOTYPE_PERM:<zero_based_lexical_rank> |
  EIG_ENTROPY:<inference_id>:<h1_outcome> |
  PROPERTY_POLICY:<policy_sha256> | PROPERTY_H1:<role_id>:<h1_outcome> |
  LEAKAGE:<forbidden_class>:<DIRECT|ENCODED> |
  AMORTIZED:<H1|H2>:<canonical_public_state_sha256> |
  SYMBOLIC_LOCAL_BUNDLE:<symbolic_local_bundle_sha256> |
  SYMBOLIC_GLOBAL_DP_BUNDLE:<symbolic_global_dp_bundle_sha256>
```

`generator_rows` is this literal ordered registry; no other generator ID is
legal. Each `dimension_keys` list is the strict outer-to-inner lexicographic
order (with `ordinal` last), and each named count formula is a closed evaluator
over its descriptor, not an expression string:

```text
GEN_AUTHORITY_HASH | FROZEN_AUTHORITY | [ordinal] | COUNT_AUTHORITY_3_V1
GEN_BANK_COVERAGE | BANK_COVERAGE | [canonical_bank_sha256,ordinal] | COUNT_BANKS_V1
GEN_ARM_ROW_COVERAGE | ARM_ROW_COVERAGE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_ARM_ROWS_V1
GEN_ABL_SOURCE_DELETE | ABL_SOURCE_DELETE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_ABL_LOCAL_SHIFT_DELETE | ABL_LOCAL_SHIFT_DELETE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_ABL_NO_UPDATE | ABL_NO_UPDATE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_ABL_ACTIVE_DELETE | ABL_ACTIVE_DELETE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_ABL_QUERY_OUTCOME_MASK | ABL_QUERY_OUTCOME_MASK | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_ABL_POSTQUERY_SOURCE_DELETE | ABL_POSTQUERY_SOURCE_DELETE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_ABL_SHAM_ROTATION | ABL_SHAM_ROTATION | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_ABL_MULTIPLICITY_FLATTEN | ABL_MULTIPLICITY_FLATTEN | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_MATRIX_PRODUCT_V1
GEN_INV_SOURCE_ORDER_ENUM | INV_SOURCE_ORDER | [canonical_bank_sha256,transformation_id,ordinal] | COUNT_UNIQUE_SOURCE_ORDERS_V1
GEN_INV_SOURCE_ORDER_LINEAGE | INV_SOURCE_ORDER | [arm_ids,ordinal] | COUNT_TRAJECTORY_ARMS_42_V1
GEN_INV_SOURCE_ORDER_SABOTAGE | INV_SOURCE_ORDER | [ordinal] | COUNT_ONE_V1
GEN_INV_TOKEN_RELABEL | INV_TOKEN_RELABEL | [variant_id,canonical_bank_sha256,arm_ids,target_mapping,transformation_id,ordinal] | COUNT_TOKEN_RELABEL_V1
GEN_INV_PROTOTYPE_RELABEL | INV_PROTOTYPE_RELABEL | [variant_id,canonical_bank_sha256,arm_ids,target_mapping,transformation_id,ordinal] | COUNT_PROTOTYPE_RELABEL_V1
GEN_INV_EIG_ENTROPY_ALIAS | INV_EIG_ENTROPY_ALIAS | [variant_id,canonical_bank_sha256,arm_ids,transformation_id,ordinal] | COUNT_EIG_ALIAS_V1
GEN_ABL_NO_QUERY | ABL_NO_QUERY | [variant_id,canonical_bank_sha256,arm_ids,target_mapping,ordinal] | COUNT_NO_QUERY_V1
GEN_PROPERTY_B_SEPARABLE | B_SEPARABLE | [variant_id,canonical_bank_sha256,transformation_id,ordinal] | COUNT_PROPERTY_POLICY_V1
GEN_PROPERTY_B_COLLISION | B_COLLISION | [variant_id,canonical_bank_sha256,transformation_id,ordinal] | COUNT_PROPERTY_POLICIES_V1
GEN_PROPERTY_B_DECOY | B_DECOY | [variant_id,canonical_bank_sha256,arm_ids,transformation_id,ordinal] | COUNT_PROPERTY_H1_V1
GEN_PROPERTY_B_BALANCED_MARGINAL | B_BALANCED_MARGINAL | [variant_id,canonical_bank_sha256,arm_ids,transformation_id,ordinal] | COUNT_PROPERTY_H1_V1
GEN_PROPERTY_MULT_6 | MULT_6 | [variant_id,canonical_bank_sha256,arm_ids,target_mapping,ordinal] | COUNT_PROPERTY_MULT6_V1
GEN_LEAKAGE_POSITIVE_CONTROL | LEAKAGE_POSITIVE_CONTROL | [transformation_id,ordinal] | COUNT_LEAKAGE_24_V1
GEN_AMORTIZED_PUBLIC_STATE | AMORTIZED_PUBLIC_STATE | [canonical_bank_sha256,public_state_key,ordinal] | COUNT_AMORTIZED_85B_V1
GEN_FRESH_TRAJECTORY_RECOMPUTE | FRESH_PROCESS_TRAJECTORY_RECOMPUTE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_LEXICAL_TRAJECTORY_ROWS_V1
GEN_FRESH_AGGREGATE_RECOMPUTE | FRESH_PROCESS_AGGREGATE_RECOMPUTE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_LEXICAL_AGGREGATE_ROWS_V1
GEN_INDEPENDENT_TRAJECTORY_RECOMPUTE | INDEPENDENT_TRAJECTORY_RECOMPUTE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_LEXICAL_TRAJECTORY_ROWS_V1
GEN_INDEPENDENT_AGGREGATE_RECOMPUTE | INDEPENDENT_AGGREGATE_RECOMPUTE | [variant_id,canonical_bank_sha256,target_mapping,arm_ids,ordinal] | COUNT_LEXICAL_AGGREGATE_ROWS_V1
GEN_SYMBOLIC_LOCAL_CONTRIBUTION | SYMBOLIC_LOCAL_CONTRIBUTION | [variant_id,canonical_bank_sha256,ordinal] | COUNT_SYMBOLIC_BANK_BUNDLES_V1
GEN_SYMBOLIC_LOCAL_AGGREGATE | SYMBOLIC_LOCAL_AGGREGATE | [variant_id,ordinal] | COUNT_SYMBOLIC_GLOBAL_BUNDLES_V1
```

The plan validator requires unique `generator_id`, unique
`(generator_id,scope_id)` domain, the exact list order above, exact
`dimension_keys`, and formula-derived `expected_count`. Because every canonical
input contains its generator ID and every generator enumerates a strictly
lexicographically increasing unique dimension tuple, canonical case preimages
are provably disjoint across generators and unique within each generator. Case
IDs inherit that uniqueness under the frozen SHA-256 collision-resistance
assumption; validators also compare full canonical bytes pairwise, so a hash
collision cannot make unequal records pass.

The case-to-packet/data-flow map is exact. `base` below means the five non-null
fields `schema_version,generator_id,case_kind,scope_id,ordinal`; every field not listed in a
row is null. Ordinals are zero-based in the canonical generator order.

| `case_kind` | packet collection | exact `expected_producer_ids` | exact additional non-null input fields beyond `base` |
|---|---|---|---|
| `AUTHORITY_HASH` | `authority_receipts` | `[AUTHORITY_HASH_RECOMPUTE]` | none |
| `BANK_COVERAGE` | `bank_receipts` | `[BANK_CONSTRUCTOR_RECOMPUTE]` | `canonical_bank_sha256,role_ids` |
| `ARM_ROW_COVERAGE` | `arm_coverage_receipts` | `[ARM_ROW_LIVE_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id` |
| `ABLATION_SEMANTIC` | `ablation_semantic_records` | `[ABLATION_LIVE_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id,transformation_id` |
| `INVARIANCE_SEMANTIC` / source-order enumeration | `invariance_records` | `[INVARIANCE_REFERENCE_RECOMPUTE,INVARIANCE_TRANSFORM_RECOMPUTE]` | `canonical_bank_sha256,role_ids,transformation_id` |
| `INVARIANCE_SEMANTIC` / source-order call-chain | `invariance_records` | `[SOURCE_ORDER_DYNAMIC_SPY_RECOMPUTE,SOURCE_ORDER_AST_DATAFLOW_AUDIT]` | `arm_ids,transformation_id` |
| `INVARIANCE_SEMANTIC` / source-order sabotage | `invariance_records` | `[SOURCE_ORDER_SABOTAGE_PROBE]` | `transformation_id` |
| `INVARIANCE_SEMANTIC` / token, prototype | `invariance_records` | `[INVARIANCE_REFERENCE_RECOMPUTE,INVARIANCE_TRANSFORM_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id,transformation_id` |
| `INVARIANCE_SEMANTIC` / `INV_EIG_ENTROPY_ALIAS` | `invariance_records` | `[INVARIANCE_REFERENCE_RECOMPUTE,INVARIANCE_TRANSFORM_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,variant_id,transformation_id` |
| `PROPERTY_WITNESS` / `B_SEPARABLE,B_COLLISION` | `property_records` | `[PROPERTY_WITNESS_RECOMPUTE]` | `canonical_bank_sha256,role_ids,variant_id,transformation_id` |
| `PROPERTY_WITNESS` / `B_DECOY,B_BALANCED_MARGINAL` | `property_records` | `[PROPERTY_WITNESS_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,variant_id,transformation_id` |
| `PROPERTY_WITNESS` / `MULT_6` | `property_records` | `[PROPERTY_WITNESS_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id,transformation_id` |
| `LEAKAGE_POSITIVE_CONTROL` | `leakage_records` | `[LEAKAGE_VALIDATOR_PROBE]` | `transformation_id` |
| `AMORTIZED_PUBLIC_STATE` | `amortized_records` | `[LIVE_PRIMARY_OUTPUT_RECOMPUTE,AMORTIZED_LOOKUP_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,public_state_key,transformation_id` |
| `FRESH_PROCESS_TRAJECTORY_RECOMPUTE` | `replay_records` | `[FRESH_PROCESS_TRAJECTORY_ROW_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id` |
| `FRESH_PROCESS_AGGREGATE_RECOMPUTE` | `replay_records` | `[FRESH_PROCESS_AGGREGATE_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id` |
| `INDEPENDENT_TRAJECTORY_RECOMPUTE` | `independent_recompute_records` | `[INDEPENDENT_PATH_TRAJECTORY_ROW_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id` |
| `INDEPENDENT_AGGREGATE_RECOMPUTE` | `independent_recompute_records` | `[INDEPENDENT_PATH_AGGREGATE_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,target_mapping,variant_id` |
| `SYMBOLIC_LOCAL_CONTRIBUTION` | `replay_records` | `[FRESH_PROCESS_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE,INDEPENDENT_PATH_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE]` | `canonical_bank_sha256,role_ids,arm_ids,variant_id,transformation_id` |
| `SYMBOLIC_LOCAL_AGGREGATE` | `replay_records` | `[FRESH_PROCESS_SYMBOLIC_DP_AGGREGATE_RECOMPUTE,INDEPENDENT_PATH_SYMBOLIC_DP_AGGREGATE_RECOMPUTE]` | `variant_id,transformation_id` |

For the property rows, `scope_id` is the displayed literal role ID;
`transformation_id` is exactly `PROPERTY_POLICY:<policy_sha256>` for
`B_SEPARABLE/B_COLLISION`, `PROPERTY_H1:<role_id>:<h1_outcome>` for
`B_DECOY/B_BALANCED_MARGINAL`, and `NONE` for `MULT_6`. For symbolic local
cases, `arm_ids` is the complete sorted union of query-pair arms and the bundle
contains every factor cell, VE trace row, and final local-state row for that
bank/variant. The symbolic aggregate bundle contains every outer-DP transition
and terminal row for that variant.

The 13 ablation/invariance generators are this closed matrix; `all groups`
means every derived canonical bank group including every alias in its complete
`role_ids`, never one representative label. `all variants` means the exact six
registry rows. `lexical medians` means the three lexical variant rows only.

| # / scope_id | variants | groups/roles | arms or inference pairs | targets | transformations |
|---|---|---|---|---|---|
| 1 `ABL_SOURCE_DELETE` | all variants | all groups | `P` | all 120 | `NONE` |
| 2 `ABL_LOCAL_SHIFT_DELETE` | all variants | all groups | `ARM_I_TRANSFER_NO_LOCAL__A_L1_EVSI__D_LCB05_FALLBACK` | all 120 | `NONE` |
| 3 `ABL_NO_UPDATE` | all variants | all groups | `ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK`; `ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK` | all 120 | `NONE` |
| 4 `ABL_ACTIVE_DELETE` | all variants | all groups | `ARM_I_TRANSFER__A_PASSIVE__D_LCB05_FALLBACK` | all 120 | `NONE` |
| 5 `ABL_QUERY_OUTCOME_MASK` | all variants | all groups | `ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK` | all 120 | `NONE` |
| 6 `ABL_POSTQUERY_SOURCE_DELETE` | all variants | all groups | `ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1` | all 120 | `NONE` |
| 7 `ABL_SHAM_ROTATION` | all variants | all groups | `ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK`; `ARM_I_SHAM__A_L1_EVSI__D_L1_MEDIAN` | all 120 | `NONE` |
| 8 `ABL_MULTIPLICITY_FLATTEN` | all variants | all groups | `ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK` | all 120 | `NONE` |
| 9 `INV_SOURCE_ORDER` | none | all groups for order proof; none for call-chain proof | no learner arm for order proof; each of 42 trajectory arms once for call-chain proof | none | every unique source-entry order per bank; 42 downstream call-chain receipts; one sabotage positive control |
| 10 `INV_TOKEN_RELABEL` | all variants | the unique canonical bank groups whose complete `role_ids` intersect exactly `HASH_00,B_SEPARABLE,B_COLLISION,B_DECOY,B_BALANCED_MARGINAL`; each group occurs once and carries its complete alias-role list | exactly `C,P,ARM_I_CONSISTENCY__A_L1_EVSI__D_L1_MEDIAN` | all 120 | all 120 lexical token permutations |
| 11 `INV_PROTOTYPE_RELABEL` | all variants | the same deduplicated canonical bank groups, each once with its complete alias-role list | the same three arms | all 120 | all 120 lexical prototype permutations |
| 12 `INV_EIG_ENTROPY_ALIAS` | three median conventions | every bank group; the scope union is `ALL79`, while each case carries only that bank group's complete `role_ids` | `ARM_I_TRANSFER__A_EIG__D_LCB05_FALLBACK`/`ARM_I_TRANSFER__A_MAX_OUTCOME_ENTROPY__D_LCB05_FALLBACK`; `ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1`/`ARM_I_SCRATCH__A_MAX_OUTCOME_ENTROPY__D_SCRATCH_L1`; `ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN`/`ARM_I_CONSISTENCY__A_MAX_OUTCOME_ENTROPY__D_L1_MEDIAN` | five H1 outcomes `0..4` (target null) | matching `EIG_ENTROPY` ID |
| 13 `ABL_NO_QUERY` | lexical medians | all groups | exactly the three frozen no-query arms | all 120 | `NONE` |

`INV_SOURCE_ORDER` is proof-by-construction with exact count
`sum_b unique_source_order_count(b) + 42 + 1`. The first subgenerator enumerates
every unique source-entry order for every canonical bank and requires
`_validate_bank(order)` to equal the canonical bank bytes. The second emits one
call-chain proof per trajectory arm that `build_state`, `query_decision`, and
`prediction_decision` receive only `_validate_bank` output before any count,
posterior, acquisition, or decision callable. Determinism in canonical
bank-plus-history then proves downstream order invariance, so crossing these
proofs with six variants or 120 targets would add no information. The final
case deliberately bypasses canonicalization and must be rejected by the
invariance comparator. This removes no source order and changes no scientific
threshold or result.

For `COUNT_TOKEN_RELABEL_V1` and `COUNT_PROTOTYPE_RELABEL_V1`, let `N` be the
number of unique canonical bank groups obtained by the five-label projection
above (currently `N=3`, derived rather than hard-coded).  Each count is exactly
`L*N*3*120*120`; aliases never create duplicate cases.

The non-matrix generators are also closed: exactly three `AUTHORITY_HASH` cases
from the frozen authority rows sorted by path, with `scope_id=FROZEN_AUTHORITY`,
ordinal `0..2`, every other `PREREQUISITE_CASE_INPUT_V1` slot null, and sole
expected producer ID `AUTHORITY_HASH_RECOMPUTE`; `B` bank cases; `L*B*120*(T+G)`
arm/row cases; leakage is exactly the frozen 12 forbidden classes crossed with
`DIRECT,ENCODED` (24 cases); amortization is exactly, per bank, five H1 states
plus `5*4*4=80` H2 states (85B cases). Property scopes are exactly:

```text
B_SEPARABLE: its recorded lexical-first satisfying policy, every median
B_COLLISION: every legal policy and its recorded lexical-first loss witness, every median
B_DECOY: its recorded lowest witnessing H1, transfer EIG/L1 pair, every median
B_BALANCED_MARGINAL: its recorded lowest witnessing H1 and unequal-joint receipt,
                     consistency EIG/MAX_OUTCOME_ENTROPY pair, every median
MULT_6: C versus the flat arm, every target and every median
```

Fresh-process and independent-path generators each cover every lexical ledger
envelope: `3*B*120*T` trajectory rows and `3*B*120*G` aggregate rows. They also
generate one symbolic-local bundle case per symbolic median/bank covering every
factor-table cell, VE join/eliminate trace, and final local-state row, plus one
symbolic-aggregate bundle case per symbolic median covering every outer-DP
transition and terminal row. Each bundle case carries its exact fresh-process
and independent-path producer pair as frozen in the mapping table. A symbolic summary
without all local and aggregate recomputations is invalid. The validator
streams the complete expected sequence and requires exact order, count,
length-prefixed case-ID digest, pairwise record equality, and exact producer
IDs without constructing a global set. The three authority cases map only to
`authority_receipts`, decode only as `AUTHORITY_HASH_OUTPUT_V1`, and are included
in `coverage_summary.expected_case_count`.

`GATE_VARIANT_LEDGER_V1` has exactly:

```text
schema_version
execution_plan_sha256
variant_id
median_convention
variant_kind
query_policy_rows
query_policy_sha256
symbolic_dp_state
symbolic_dp_sha256
reachable_ordinary_verdicts
envelope_rows
envelope_rows_sha256
```

`variant_kind` is exactly `lexical` or `symbolic_global_policy_dp_v1`.
`query_policy_rows` rows have exactly
`{canonical_bank_sha256,arm_id,choices_by_h1_outcome}`; the choices are a
five-int exact-minimizer policy. Every ledger contains the complete sorted table
for every canonical bank and every selectable trajectory arm; there are no
omitted-row lexical defaults or override semantics. A lexical ledger chooses
every recomputed lexical policy. A symbolic ledger contains the identical
lexical table and `query_policy_sha256` as its same-median lexical anchor, then
represents all global legal policy worlds only through the mandatory DP. No
concrete-global ledger kind exists. Its `envelope_rows` and
`envelope_rows_sha256` must likewise byte-match the same-median lexical ledger;
alternative-world evidence exists only in the enumerated local contributions
and their DP aggregates.

`GATE_SYMBOLIC_QUERY_DP_V1` has exactly
`{schema_version,median_convention,leaf_variable_rows,factor_rows,ve_trace_rows,local_state_rows,transition_rows,initial_state_bytes,initial_state_sha256,terminal_state_rows,reachable_ordinary_verdicts,equivalence_suite_sha256}`.
A leaf variable is exactly `(canonical_bank_sha256,arm_id,h1_outcome)`, where
the arm is in the sorted union of query-pair left/right arms and `h1_outcome` is
`0..4`; its domain is the complete sorted exact-minimizer token set, of size at
most four. Full per-bank arm-policy Cartesian enumeration is forbidden. Rows
are exactly:

```text
leaf_variable_rows:
  {variable_key,canonical_bank_sha256,arm_id,h1_outcome,domain_tokens}
factor_rows:
  {factor_id,factor_kind,canonical_bank_sha256,role_id,target_mapping,h1_outcome,
   gate_ids,scope_variable_keys,table_rows,factor_sha256}
table_rows:
  {assignment_bytes,assignment_sha256,partial_contribution_bytes,
   partial_contribution_sha256}
ve_trace_rows:
  {step_ordinal,eliminated_variable_key,selection_key,input_factor_sha256s,
   join_trace_rows,elimination_trace_rows,output_factor_bytes,output_factor_sha256}
join_trace_rows:
  {left_factor_sha256,right_factor_sha256,left_row_bytes,left_row_sha256,
   right_row_bytes,right_row_sha256,joined_row_bytes,joined_row_sha256}
elimination_trace_rows:
  {source_row_bytes,source_row_sha256,projected_row_bytes,projected_row_sha256}
local_state_rows:
  {canonical_bank_sha256,contribution_bytes,contribution_sha256,
   source_relation_row_sha256s}
transition_rows:
  {bank_ordinal,from_state_bytes,from_state_sha256,
   local_contribution_bytes,local_contribution_sha256,
   to_state_bytes,to_state_sha256}
terminal_state_rows:
  {state_bytes,state_sha256,ordinary_branch}
```

`variable_key` is exactly
`canonical_bank_sha256+U+001F+arm_id+U+001F+decimal_h1_outcome`.
`factor_kind` is `UNARY_GATE`, `PAIR_GATE`, or `TERNARY_GATE`. For every scope
unit in the query-pair registry, the producer constructs one deterministic
factor over the one, two, or three policy leaves required by the closed
contribution registry below. A third leaf is mandatory when a predicate uses
both named arms and the independently variable `PUBLIC_L1_RISK_DP` policy;
silently fixing PUBLIC to lexical is forbidden. Primary/multiplicity gates use every named
target; H1/property-only gates use their exact named H1 outcome with target
null. `CAUSAL_EFFECT:ABL_ACTIVE_DELETE` is also target-bearing and uses exactly
the complete sorted distinct-member support of B_SEPARABLE, with no nonmember
factor. Exactly one of `target_mapping,h1_outcome` is non-null. `factor_kind` is
determined only by the cardinality of the sorted deduplicated scope-variable
set; repeated arm roles collapse to one leaf (for example a control K equal to
P does not create a duplicate PUBLIC variable). The table
enumerates the complete domain product (at most 64 assignments). `assignment_bytes` decodes
to the sorted complete list of `{variable_key,query_token}` for that factor.
Each table cell invokes the real arm rows for that assignment and emits a
closed `GATE_LOCAL_CONTRIBUTION_V1`: unrelated Boolean fields are their fixed
identities, while the named gate field carries the recomputed target fact.
Every partial contribution for one bank carries that bank's hash and its exact
complete sorted alias-role list, so these identity fields must match at joins.
Query-independent structural/property receipts (`B_SEPARABLE` and
`B_COLLISION`) attach to that bank's lexically first leaf variable as identical
unary rows across its full domain; this preserves the exact fact without adding
a free variable or a constant-factor exception. The two literal `gate_ids` are
respectively `[PROPERTY_B_SEPARABLE]` and `[PROPERTY_B_COLLISION]`; `role_id` is
the matching property role; `target_mapping` is null; `h1_outcome` is exactly
the outcome encoded by the selected lexically first anchor leaf; and the scope
is exactly that singleton leaf. No alternate property gate spelling or anchor
outcome is legal.
`factor_id` is
`SHA256(UTF8("FACTOR"+U+001F+compact_json(gate_ids)+U+001F+role_id+U+001F+
compact_json(target_mapping)+U+001F+compact_json(h1_outcome)+U+001F+
compact_json(scope_variable_keys)))`.
`factor_sha256` hashes the complete factor with that field omitted. All
`*_bytes` columns are canonical JSON bytes and every adjacent hash must match.
Every original and intermediate relation row decodes to
`VE_RELATION_ROW_V1` with exactly
`{scope_variable_keys,assignment_bytes,contribution_bytes,contribution_sha256}`;
every `output_factor_bytes` decodes to `VE_RELATION_FACTOR_V1` with exactly
`{schema_version,scope_variable_keys,relation_rows}`. Assignment keys must equal
the scope exactly and be in variable-key order.

#### Closed gate-to-contribution registry

Let `C`, `R`, and `P` be the conservative, raw, and PUBLIC arms defined above;
`A` is the exact ablation arm named by a gate row and `K` the exact named
control. Let `m_X(t)` be a freshly recomputed `ARM_TARGET_METRIC_V1` for arm
`X` at target `t`, with the factor assignment binding both its candidate-policy
leaf and its PUBLIC-policy leaf. `F_X` is
`candidate_full_endpoint_mae`; `Bc_X` and `Bs_X` are respectively the
PUBLIC-relative common and same-history improvements in `m_X`; and `PCM(X,Y)`
is X's pairwise-common MAE over `U(X,Y)`. Exact thresholds are
`tauF=21875/1000000` and `tau=4375/1000000`. Member,
canonical-member, and D2--D5 applicability are recomputed from the plan bank,
role, and target; caller-supplied applicability flags are forbidden.

Every contribution starts from the closed identity: all `*_all` and equality
fields are `true`; all `*_seen`, `*_failure_seen`, and `strict_witness_seen`
fields are `false`; and the 19 control rows are in frozen-control order with
`full_no_worse_all=true`, `member_common_no_worse_all=true`,
`strict_witness_seen=false`, and `metric_rationals_equal_all=true`. A named
factor may modify only the fields listed below. All unlisted fields retain the
identity, and no stored predicate is accepted.

| gate ID | exact policy scope | exact point contribution |
|---|---|---|
| `MEMBER_FORWARD_CONSERVATIVE` | `{C,P}` | On each exact member: AND the conservative full/common/same fields with `F_P-F_C>=tauF`, `Bc_C>=0`, and `Bs_C>=0`. On the canonical member additionally AND its common/same fields with `Bc_C>=tau` and `Bs_C>=tau`. On D2--D5 targets AND bounded safety with `F_C-F_P<=tau` and strict safety with `F_C<=F_P`. |
| `MEMBER_FORWARD_RAW` | `{R,P}` | The identical member/canonical updates for the five raw fields; on D2--D5 targets AND raw bounded safety with `F_R-F_P<=tau`. |
| `SOURCE_DELETE` | `{C,P}` plus source-delete semantic prerequisite | On each exact member OR `source_delete_member_failure_seen` when the deleted/P arm violates any applicable member or canonical subpredicate, and AND `source_delete_reduction_all` with `(F_P-F_C)-(F_P-F_P)>=tauF`. The separate ablation trace must byte-match canonical P or the packet is invalid; a metric alone cannot prove callable identity. |
| `CONTROL_PARETO:<K>` | `{C,K,P}` | On every primary target update K's row: AND full no-worse with `F_K<=F_C`, OR strict with `F_K<F_C`, and AND metric equality with canonical-byte equality of the complete recomputed `metric_rationals` objects. On exact members additionally AND common no-worse with `PCM(K,C)<=PCM(C,K)` and OR strict with strict `<`. P is in scope because complete metric-rational equality contains PUBLIC-relative fields. |
| `CONSISTENCY_POSITIVE_NON_EQUIVALENCE` | `{C,K}` for the canonical consistency K | On every primary target AND `consistency_full_no_regression_all` with `F_C<=F_K`; on exact members OR the common-advantage witness with `PCM(K,C)-PCM(C,K)>=tau`. |
| `CAUSAL_EFFECT:ABL_LOCAL_SHIFT_DELETE` | `{C,A}` plus live semantic traces | On D2 targets OR `local_delete_witness_seen` iff canonical H1/H2 posterior/state bytes differ and either the query decision differs or at least one unqueried prediction differs. |
| `CAUSAL_EFFECT:ABL_ACTIVE_DELETE` | `{C,A}` | On B_SEPARABLE exact members OR `active_delete_witness_seen` iff both live query decisions have singleton minimizer sets, their selected queries differ, and `PCM(A,C)-PCM(C,A)>=tau`. |
| `MEMBER_FAILURE:ABL_NO_UPDATE`, `MEMBER_FAILURE:ABL_QUERY_OUTCOME_MASK`, `MEMBER_FAILURE:ABL_POSTQUERY_SOURCE_DELETE`, `MEMBER_FAILURE:ABL_SHAM_ROTATION` | `{A,P}` | For the exact named arm, OR only its dedicated failure field when any applicable exact-member or canonical-member subpredicate fails. The two no-update and two sham arms map to separate fields and never substitute for one another. |
| `CAUSAL_EFFECT:ABL_NO_UPDATE`, `CAUSAL_EFFECT:ABL_QUERY_OUTCOME_MASK` | `{C,A,P}` | On primary canonical members OR the exact arm's effect field iff `(Bc_C-Bc_A>=tau) OR (Bs_C-Bs_A>=tau)`. This PUBLIC-relative OR is ternary and must not lexical-anchor P. |
| `CAUSAL_EFFECT:ABL_POSTQUERY_SOURCE_DELETE` | `{C,A}` | On primary canonical members OR `postquery_effect_witness_seen` iff `Bs_C-Bs_A>=tau`. |
| `CAUSAL_EFFECT:ABL_SHAM_ROTATION` | `{C,A}` | Contribution identity only. Frozen 001D defines sham semantic execution and two member-failure predicates, but no sham-effect threshold; inventing one is forbidden. |
| `CAUSAL_EFFECT:ABL_MULTIPLICITY_FLATTEN`, `PROPERTY_MULT_6` | `{C,A}` plus live semantic traces | These aliases update the same `property_mult6_all` field by AND with byte equality of H1/final semantic state, query scores/minimizers/choice, and prediction for every MULT_6 target. Duplicate identical contributions are byte-deduplicated. |
| `PROPERTY_B_DECOY` | named EIG/raw pair at the frozen H1 | AND `property_decoy_all` with recomputation that both exact-minimizer sets are singletons and their selected tokens differ. |
| `PROPERTY_B_BALANCED_MARGINAL` | named consistency EIG/entropy pair at the frozen H1 | AND `property_balanced_all` with the scanned unequal-joint witness, all four eligible tokens tied as EIG exact minimizers, and byte-identical score rows, minimizer set, and choice for the entropy alias. |
| anchored `B_SEPARABLE` structural factor | bank's lexically first leaf | AND `property_separable_all` with fresh `_separable_witness` recomputation for the frozen policy. |
| anchored `B_COLLISION` structural factor | bank's lexically first leaf | AND `property_collision_all` with fresh `_collision_witnesses` recomputation for every legal policy, including the compatible-pair, equal-outcome, and remaining loss-relevant-token conditions. |

Metric rows alone are insufficient for source-delete callable identity,
local-delete state change, MULT_6 semantic equality, or the structural property
predicates. Those cells must invoke and validate the exact live semantic or
property producer named above. A factor cell missing a required producer is
invalid, not identity. When one factor row carries multiple `gate_ids`, its cell
is the identity merged with every listed update in literal `gate_ids` order.

`SEMANTIC_BEHAVIOR_PROJECTION_V1` is the exact existing
`_behavior_semantic_payload` projection over a validated
`LIVE_SEMANTIC_TRACE_V1`: remove top-level `arm_id`; remove
`arm_id,inference_id,acquisition_id,decision_id,transition_id` from both
`state_h1` and `state_final`; remove `arm_id` from `query_decision` and
`prediction_decision`; retain every other field unchanged. Local-delete state
change means the projected `state_h1` differs OR the projected `state_final`
differs. Its behavioral change means the projected query decision differs OR
`prediction_decision.prediction_micro[token]` differs by exact value on at least one token in exact
`U(C,A)={1,2,3,4}-{qC,qA}`. MULT_6 equality means byte equality of the complete
canonical `SEMANTIC_BEHAVIOR_PROJECTION_V1`. Full unprojected cross-arm bytes
may not be used for either predicate. Whenever `X=P`, `m_P` binds the same P
leaf as both candidate and PUBLIC policy, so its PUBLIC-relative benefits are
recomputed as exact zero rather than assumed.

For each bank, construct the factor graph whose vertices are its leaf variables
and whose edges join variables co-occurring in a factor. At every step choose
the variable with lexicographically minimum
`selection_key=[missing_edges_among_current_neighbors,current_neighbor_count,
variable_key]`. Sort all incident factors by hash, relationally join compatible
assignment rows, and merge their partial contributions by the fixed AND/OR
rules below. After every binary join, canonical-byte deduplicate rows. Eliminate
the chosen variable by deleting it from each assignment and taking the union of
the resulting rows without merging mutually exclusive alternatives, then
canonical-byte deduplicate again. Add fill edges among its current neighbors,
remove it, and repeat. `join_trace_rows` and `elimination_trace_rows` retain
every source/result canonical preimage and hash; the output factor is the exact
post-elimination relation. After the final variable, join any remaining
empty-scope factors. The resulting empty-scope relation is exactly the sorted
reachable local-contribution set recorded in `local_state_rows`; no lossy
Boolean summary or policy sampling is permitted.

The byte-exact fold order is fixed. Incident factors are sorted by complete
factor SHA-256. The first is the accumulator and each next factor is
natural-joined to it. For each binary join, accumulator rows and right-factor
rows are each sorted by canonical row bytes and visited left-major/right-minor.
Only compatible pairs emit `join_trace_rows`, in that visitation order; the
joined relation is canonical-byte deduplicated and sorted before the next fold.
Elimination visits source rows in canonical-byte order, emits one trace row per
source row, removes the selected variable without merging mutually exclusive
contributions, then byte-deduplicates and sorts projected rows. Scopes are
always sorted variable-key lists. Remaining empty-scope factors use the same
factor-hash and row fold. These ordering rules govern trace bytes as well as the
final relation.

All schema lists also have one canonical order: `leaf_variable_rows` by
`variable_key`; formal `factor_rows` by `factor_id`; each factor's `table_rows`
by `assignment_bytes`; `ve_trace_rows` by `step_ordinal`; `local_state_rows` by
`(canonical_bank_sha256,contribution_bytes)`; `transition_rows` by
`(bank_ordinal,from_state_bytes,local_contribution_bytes,to_state_bytes)`;
`terminal_state_rows` by `state_bytes`; and every
`source_relation_row_sha256s` as a sorted duplicate-free hash list. Canonical
JSON never substitutes for these array-order rules.

`GATE_LOCAL_CONTRIBUTION_V1` has exactly these fields:

```text
schema_version canonical_bank_sha256 role_ids
conservative_member_full_all conservative_member_common_all
conservative_member_same_history_all conservative_canonical_common_all
conservative_canonical_same_history_all raw_member_full_all
raw_member_common_all raw_member_same_history_all raw_canonical_common_all
raw_canonical_same_history_all conservative_bounded_safety_all
conservative_strict_safety_all raw_bounded_safety_all
source_delete_member_failure_seen source_delete_reduction_all
active_delete_witness_seen local_delete_witness_seen
no_update_evsi_member_failure_seen no_update_evsi_effect_witness_seen
no_update_passive_member_failure_seen no_update_passive_effect_witness_seen
mask_member_failure_seen mask_effect_witness_seen
postquery_member_failure_seen postquery_effect_witness_seen
sham_lcb_member_failure_seen sham_raw_member_failure_seen
property_separable_all property_collision_all property_decoy_all
property_balanced_all property_mult6_all control_relations
consistency_common_advantage_witness_seen consistency_full_no_regression_all
```

`control_relations` is exactly 19 rows, frozen-control order, each
`{control_arm_id,full_no_worse_all,member_common_no_worse_all,strict_witness_seen,metric_rationals_equal_all}`.
Canonical global-state bytes have the same field set except bank identity and
roles: every `*_all` and equality field has identity `true` and merges by AND;
every `*_seen`, `*_failure_seen`, and `strict_witness_seen` field has identity
`false` and merges by OR; the 19 control rows merge positionally by frozen arm
ID. No extrema, witness, property, consistency, or control fact may be omitted.

Banks are processed in ascending `canonical_bank_sha256`. With `I` the
canonical identity bytes and `Local_i` the sorted distinct contributions:

```text
Reach_0 = {I}
Reach_(i+1) = sort_unique_bytes({merge(s,l): s in Reach_i, l in Local_i})
```

Every edge is serialized in `transition_rows`; terminal rows apply the exact
branches 5--11 below to every state in `Reach_B`. `reachable_ordinary_verdicts`
is the sorted unique terminal branch list. The lexical envelope remains the
ledger's row evidence; the DP carries every local contribution and aggregate.
The terminal derives `conservative_member_and_forward` as the AND of its five
conservative member/canonical fields and derives `raw_member_and_forward`
analogously. `attribution_gate` is the AND of source-delete failure/reduction,
active/local witnesses, both named no-update failure/effect pairs, mask and
postquery failure/effect pairs, both sham failures, and all five property
fields. A control matches iff its two no-worse fields and either its strict or
exact-equality field hold; `control_match` is true iff any of the 19 matches or
the two consistency-positive fields do not both hold. These derived values then
enter the exact seven branch formulas below; no stored terminal predicate is
accepted.

`small_instance_equivalence_suite` is exactly nine bounded toy rows: each
median crossed with bank counts 1, 2, and 3. The toys validate the symbolic
solver rather than completeness of the formal factor registry, so they use the
following deterministic capped real-factor motif instead of evaluating every
factor in a bank.

For each median, scan bank groups in ascending hash order. Every factor ordering
in this motif uses ascending `factor_id`. A bank is eligible
only if its real factor descriptors contain two binary factors `F0,F1` such
that: `F0` is the lexicographically smallest binary factor with distinct leaves
and domain product greater than one; `F1` is the lexicographically smallest
different binary factor sharing exactly one F0 leaf and introducing a third
leaf; their union is exactly three variables; and the Cartesian product
`F0.table_rows x F1.table_rows` contains at least one compatible and at least
one incompatible row pair on the shared variable, while the union of both
tables contains at least two distinct `partial_contribution_sha256` values.
Select the first `n` eligible banks and fail plan
construction rather than weakening the motif. The retained leaf set per bank is
the sorted three-variable union.

Before the nine suite rows are accepted, the plan builder performs a bounded
descriptor/table preflight and requires at least three eligible bank groups for
each median. Failure is a plan-construction error, never permission to change
the motif or reuse a bank.

Retain at most five real factors per selected bank, in this exact
selection/dedup order: `F0`; `F1`; the smallest not-yet-selected factor wholly over the retained
variables that changes an `*_all` or equality field; the smallest such factor
not already selected that changes an `*_seen` or `*_failure_seen` field; and the smallest not-yet-selected factor with
exactly one retained endpoint, projected by fixing every outside leaf to its
lexical-minimum real-domain token. Missing optional third/fourth/fifth rows are
omitted; `F0,F1` are mandatory. Canonical-byte deduplicate after selection.
Ternary factors are permitted when wholly inside the motif; the projected
fifth factor is necessarily unary and an empty projected scope is rejected.
This selection is deterministic and is not a
run-time algorithm choice.

Each suite row is exactly
`{suite_id,median_convention,bank_count,leaf_variable_keys,toy_instance_sha256,explicit_algorithm_id,symbolic_algorithm_id}`.
`toy_instance_sha256` hashes `TOY_FACTOR_INSTANCE_V1` with exactly
`{schema_version,median_convention,bank_group_sha256s,leaf_variable_rows,factor_rows}`.
The algorithm IDs are `explicit_toy_assignment_enumeration_v1` and
`symbolic_leaf_factor_elimination_plus_global_dp_v1`; `suite_id` is
`SHA256(UTF8("DPEQ"+U+001F+median_convention+U+001F+decimal_bank_count+U+001F)
|| canonical_toy_instance_bytes)`. Explicit ground truth enumerates every
assignment of the at most nine retained variables (`<=4^9` assignments), looks
up the retained factor cells directly in factor-SHA order, merges contributions
without calling the VE join/eliminate/min-fill implementation, and requires
byte-identical reachable local
contributions, across-bank terminal states, terminal branch rows, and reachable
branch list from factor elimination plus the outer DP.
`small_instance_equivalence_suite_sha256` hashes the canonical nine-row list;
every symbolic `equivalence_suite_sha256` must equal it. Lexical ledgers have
null symbolic fields and one reachable branch. Symbolic ledgers require the
canonical DP bytes and matching hash. This bounded positive control is required
but does not mathematically prove arbitrary factor-elimination implementation
correctness.
I1 additionally requires private non-evidence operator counterexamples: mixed
AND/OR plus positional-control merge; compatible and incompatible
shared-variable joins including bank-hash/alias mismatch rejection; elimination
of alternatives `A,B,A` to exactly `{A,B}` without merging mutually exclusive
alternatives; the K2,2 graph `{a-c,a-d,b-c,b-d}` with fill-aware order
`a,b,c,d`; and a declared-scope probe that varies each leaf independently and
rejects any changed output from a leaf omitted from the factor scope.
The operator suite must also include a genuine ternary control `T(x,y,p)` whose
output changes with `p` while `x,y` are fixed, require declared scope exactly
`{x,y,p}`, and reject a `{x,y}` implementation or any implementation that
lexically anchors `p`. This is mandatory even if no selected real toy factor is
ternary.
No single-bank perturbation is a completeness claim. Every embedded
`VERIFIER_PRIVATE_ENVELOPE_V1.artifact_receipts` remains exactly `[]`.
Median and query-policy identity are bound only by this ledger wrapper and its
canonical hashes, never by adding fields to the frozen envelope.

`reduce_gate_evidence(plan, ledgers, packet)` has this exact positional order.
It validates the plan first, then the exact six ledgers in `variant_registry`
order, then the packet. Within each ledger, policy rows use
`(canonical_bank_sha256,arm_id)` order and envelopes use the exact regenerated
case-key order. Reordered, missing, duplicate, or extra ledgers/rows are invalid.

`GATE_PREREQUISITE_PACKET_V1` has exactly:

```text
schema_version
execution_plan_sha256
authority_receipts
bank_receipts
arm_coverage_receipts
ablation_semantic_records
property_records
invariance_records
leakage_records
amortized_records
replay_records
independent_recompute_records
```

The collection fields are consumed as ordered record streams. I1 may validate
bounded synthetic prefixes and generator arithmetic but must not construct a
formal packet or materialize any complete collection; a later I2 may bind the
stream source, framing, and incremental packet hash before execution.

Every row in every packet collection is
`PREREQUISITE_CASE_RECORD_V1` with exactly
`{schema_version,case_id,case_kind,scope_id,canonical_input_bytes,input_sha256,producer_records}`.
The first six fields must byte-match the next lazily generated plan case. `producer_records`
is a sorted nonempty list of `PREREQUISITE_PRODUCER_RECORD_V1` with exactly
`{producer_id,producer_function,code_path_sha256,call_count,output_schema_id,canonical_output_bytes,output_sha256,pre_read_order_receipt_bytes,pre_read_order_receipt_sha256}`.
Its producer-ID set must exactly match the plan row. No generic `dict`, open
receipt, or unchecked payload is allowed.

`output_schema_id` is an exact enum selecting an existing closed schema
(`FINITE_ACTIVE_TRANSFER_STATE_V1`, `QUERY_DECISION_V1`,
`PREDICTION_DECISION_V1`, `ARM_TARGET_METRIC_V1`, or
`AGGREGATE_METRIC_V1`) or one of these closed wrappers:

```text
AUTHORITY_HASH_OUTPUT_V1
  {schema_version,path,expected_sha256,actual_sha256}
BANK_COVERAGE_OUTPUT_V1
  {schema_version,canonical_bank_sha256,canonical_bank,role_ids,canonical_member,target_mappings}
ARM_COVERAGE_OUTPUT_V1
  {schema_version,variant_id,canonical_bank_sha256,target_mapping,arm_id,metric_schema_id,metric_sha256}
LIVE_SEMANTIC_TRACE_V1
  {schema_version,arm_id,public_history,state_h1,query_decision,state_final,prediction_decision}
ABLATION_COMPARISON_OUTPUT_V1
  {schema_version,ablation_id,arm_id,reference_behavior_bytes,intervened_behavior_bytes,invocation_receipt}
INVARIANCE_COMPARISON_OUTPUT_V1
  {schema_version,ablation_id,transformation_bytes,reference_behavior_bytes,inverse_mapped_behavior_bytes,invocation_receipt}
SOURCE_ORDER_LINEAGE_OUTPUT_V1
  {schema_version,receipt_kind,arm_id,canonical_bank_sha256,call_rows,
   ast_dataflow_receipt,canary_receipt}
PROPERTY_WITNESS_OUTPUT_V1
  {schema_version,property_role_id,witness_id,witness_tuple_bytes}
LEAKAGE_VALIDATION_OUTPUT_V1
  {schema_version,forbidden_class,case_kind,error_type,error_message}
AMORTIZED_COMPARISON_OUTPUT_V1
  {schema_version,state_key,canonical_public_input_bytes,live_output_bytes,lookup_output_bytes}
RECOMPUTE_OUTPUT_V1
  {schema_version,recompute_kind,case_key,canonical_row_or_aggregate_bytes}
```

For `SOURCE_ORDER_LINEAGE_OUTPUT_V1`, `receipt_kind` is exactly
`DYNAMIC_SPY`, `AST_DATAFLOW`, or `SABOTAGE`. `call_rows` are sorted by
`(ordinal,caller_function,callee_function)` and each has exactly
`{ordinal,caller_function,callee_function,input_bank_sha256,validated_bank_sha256,downstream_bank_sha256}`.
`SOURCE_ORDER_DYNAMIC_SPY_RECOMPUTE`, `SOURCE_ORDER_AST_DATAFLOW_AUDIT`, and
`SOURCE_ORDER_SABOTAGE_PROBE` must respectively emit those three receipt kinds
under this wrapper and no other output schema.
The frozen public roots are `[build_state,query_decision,prediction_decision]`
and the frozen downstream function-name list is
`[_validate_bank,source_counts,local_counts,build_state,query_decision,prediction_decision]`.
For each of the 42 trajectory arms, the dynamic spy must cover every applicable
edge in those paths and every row must satisfy
`validated_bank_sha256==downstream_bank_sha256==canonical_bank_sha256`.

`ast_dataflow_receipt` is null except for `AST_DATAFLOW`, where it has exactly
`{source_path,source_sha256,root_function_names,downstream_function_names,validated_assignment_name,ast_dump_sha256,raw_bank_reachability_violations}`;
the lists equal the frozen lists above, `validated_assignment_name` is exactly
`validated_bank`, and `raw_bank_reachability_violations` is exactly `[]`. It
audits that raw parameter `bank` cannot reach a frozen downstream call before
assignment from `_validate_bank(bank)` in each public root. This is a bounded
code-path/data-flow receipt, not a theorem about arbitrary Python execution.

`canary_receipt` is null except for `SABOTAGE`, where it has exactly
`{original_order_sha256,reversed_order_sha256,detector_error_type,detector_error_message}`.
The sabotage monkeypatches `_validate_bank` to identity and routes its result to
the order-sensitive canary
`SHA256(canonical_json_bytes(list(bank)))`; reversing a non-palindromic bank
must change the canary hash, and the clean invariance validator must raise the
frozen detection error. Equal hashes, missing exception, or empty error type is
a positive-control failure. Other receipt-kind fields are respectively null or
empty as required by the closed validator.

History and state/query/prediction children use their existing exact schemas.
Property witness tuples use the exact ID-dependent frozen encoding; leakage
class/kind use the exact 12-by-2 registry; amortized bytes decode to the exact
query or prediction schema. `recompute_kind` is the closed enum
`TRAJECTORY_ROW|AGGREGATE_METRIC|SYMBOLIC_LOCAL_CONTRIBUTION|SYMBOLIC_DP_AGGREGATE`;
its bytes decode respectively to `ARM_TARGET_METRIC_V1`, `AGGREGATE_METRIC_V1`,
`SYMBOLIC_LOCAL_RECOMPUTE_BUNDLE_V1` with exactly
`{schema_version,factor_rows,ve_trace_rows,local_state_rows}`, or
`SYMBOLIC_DP_RECOMPUTE_BUNDLE_V1` with exactly
`{schema_version,transition_rows,terminal_state_rows,reachable_ordinary_verdicts}`.
Every `invocation_receipt` inside an applicable output has
exactly `{producer_function,input_sha256,code_path_sha256,call_count,output_sha256}`;
`call_count` is recomputed against the case's required callable coverage.

Replay and independent producer records additionally require the pre-read
fields below; every other case requires both pre-read fields to be null.
`producer_id` is exactly one of
`FRESH_PROCESS_TRAJECTORY_ROW_RECOMPUTE`,
`FRESH_PROCESS_AGGREGATE_RECOMPUTE`,
`INDEPENDENT_PATH_TRAJECTORY_ROW_RECOMPUTE`,
`INDEPENDENT_PATH_AGGREGATE_RECOMPUTE`,
`FRESH_PROCESS_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE`,
`INDEPENDENT_PATH_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE`,
`FRESH_PROCESS_SYMBOLIC_DP_AGGREGATE_RECOMPUTE`, or
`INDEPENDENT_PATH_SYMBOLIC_DP_AGGREGATE_RECOMPUTE`. The four lexical recompute
case kinds require their exact singleton producer. Each of the two symbolic
bundle kinds requires the exact fresh/independent pair in the mapping table. The canonical
pre-read receipt has exactly
`{producer_id,input_sha256,recompute_start_ordinal,recompute_complete_ordinal,stored_bundle_read_ordinal,recomputed_output_sha256,stored_bundle_sha256}`,
its SHA-256 must match, and it must satisfy
`start < complete < stored_bundle_read`. This is an auditable ordering receipt,
not an external timestamp, signature, or cryptographic proof of independence.
Every ID-specific byte payload is reconstructed and semantically validated by
the reducer. Packet records are consumed in exact case order and compared
one-for-one with `iter_expected_prerequisite_cases(plan)` while streaming count
and case-ID digest; every observed row must equal the expected row at the same
ordinal. Thus any reorder, duplicate, missing row, early EOF, surplus row,
count mismatch, or digest mismatch is invalid without an adjacent-only
shortcut. No global expected/observed set
may be materialized. Stored equality/pass booleans are forbidden.

`GATE_REDUCTION_V1` has exactly:

```text
schema_version
execution_plan_sha256
variant_ledger_sha256s
prerequisite_packet_sha256
coverage_summary
metric_extrema
causal_effect_witnesses
control_comparison_witnesses
property_witnesses
private_truth_leakage
instrument_invalid
raw_upside
raw_bounded_safety
conservative_member_and_forward
conservative_bounded_safety
conservative_strict_safety
bounded_core
strict_core
attribution_gate
bounded_joint
strict_joint
pareto_match_arm_ids
consistency_positive_non_equivalence
control_match
ordinary_branch_by_median
median_sensitive
query_sensitive
ordinary_branch
verdict
claim_ceiling
```

`coverage_summary` has exactly
`{expected_case_count,observed_case_count,expected_case_id_digest,observed_case_id_digest,first_case_mismatch_ordinal,expected_case_id_at_mismatch,observed_case_id_at_mismatch,expected_ledger_count,observed_ledger_count,missing_variant_ids,extra_variant_ids,duplicate_variant_ids}`.
Counts are nonnegative integers; mismatch fields are all null on exact streaming
equality and otherwise record only the first mismatch. Variant ID lists are
sorted and duplicate-free; case-ID sets/lists are never materialized.

Each `metric_extrema` row has exactly
`{metric_id,direction,value,arm_id,bank_role_id,canonical_bank_sha256,target_mapping,stratum,variant_id}`.
`direction` is `minimum` or `maximum`, and `value` is reduced `{n,d}`.
Each `causal_effect_witnesses` row has exactly
`{predicate_id,ablation_id,arm_id,bank_role_id,canonical_bank_sha256,target_mapping,metric_id,reference_value,intervened_value,effect_value,threshold,variant_id}`.
Each `control_comparison_witnesses` row has exactly
`{control_arm_id,comparison_kind,bank_role_id,canonical_bank_sha256,target_mapping,candidate_value,control_value,difference,variant_id}`.
Each `property_witnesses` row has exactly
`{property_role_id,witness_id,canonical_bank_sha256,target_mapping,arm_ids,named_rationals,semantic_hashes,variant_id}`;
`named_rationals` rows are exactly `{metric_id,value}` and `semantic_hashes`
rows are exactly `{receipt_id,sha256}`. All mappings, IDs, hash types, rational
types, enum values, nullability, and sort orders are checked against the plan.
These are computed explanation receipts; no `passed`, winner, gate, or verdict
boolean is allowed inside them.

This is computed output only. No field from a stored reduction, winner, gate,
or verdict may be an input to recomputation.

### Exact row reduction and pairwise common set

All threshold arithmetic uses `fractions.Fraction`. Distinct exact members are
equal-weight pointwise units; source occurrence remains diagnostic. For arms
`A,B`, pairwise common-unqueried comparison always uses

```text
U(A,B) = {1,2,3,4} minus {qA,qB}
MAE(A | A,B) = sum token_loss(A,t), t in U(A,B)
               / (4 * |U(A,B)| * 1000000)
```

Thus same-query comparisons have denominator 12 and different-query comparisons
have denominator 8. Active-delete, Pareto controls, and explicit consistency
non-equivalence use this shared pairwise set, not two arms' separately
PUBLIC-relative common fields. Benefit-reduction predicates whose frozen wording
names reduction of an arm's PUBLIC or same-history benefit compare the fully
recomputed named benefits.

The member, canonical-member, bounded-safety, strict-safety, ablation-effect,
and consistency thresholds remain exactly those in frozen 001D. The 19 Pareto
controls are the exact frozen list. The no-strict-improvement equality alternative
means canonical bytes of the complete recomputed `metric_rationals` object are
identical for every applicable role/target; arm IDs or full row bytes are not
part of that equality.

Positive consistency non-equivalence requires at least one exact member with
pairwise common advantage at least `4375/1000000` and no positive conservative
full-MAE regression versus the canonical consistency arm on any primary target.
Otherwise `control_match=true`. Amortized equality is an instrument prerequisite
and claim cap; it does not itself set structural `control_match=true`.

Both registered `ABL_NO_UPDATE` arms must independently fail the complete
member-and-forward gate, and each must independently reduce a primary canonical
member's named common or same-history benefit by at least `4375/1000000`. This is
the conservative preregistered resolution; one failing arm cannot stand in for
the other.

### Prerequisites, sensitivity, and ordinary branches

Missing or mismatched formal replay or independent-path row/aggregate evidence
sets `instrument_invalid=true` in the evidence reducer. A separate pure
synthetic truth-table helper may test dispatch exhaustiveness without those
files, but it is explicitly non-evidence and cannot call or impersonate the
evidence reducer.

`B_COLLISION` is derived, not asserted: for every legal policy the reducer
recomputes a witness leaf retaining at least two distinct compatible source
mappings and a remaining loss-relevant token. No learner output has a source-ID
or full-support-identification field, and no verifier boolean claiming support
identification is accepted as evidence.

For each median, the lexical ledger defines the normative ordinary branch.
Median sensitivity means the lexical ordinary branch differs across lower,
midpoint, and upper. Query sensitivity follows the frozen **any alternative**
quantifier: for a fixed median, form one global legal policy world by choosing
one complete exact-minimizer policy for every selectable trajectory arm on every
canonical bank, use each registered gate pair's two selected policies in that
comparison, and compute the eventual ordinary branch. Query sensitivity is true
iff the exact reachable ordinary-verdict set contains a branch different from
that median's lexical branch. The set is obtained only by the mandatory
`symbolic_global_policy_dp_v1` using the exact per-bank leaf-factor elimination
and across-bank DP above, after its exact nine-suite equivalence check;
there is no run-time concrete-enumeration alternative. Single-bank substitutions
cannot establish completeness. Priority remains
leakage, instrument invalidity, median sensitivity, query sensitivity, then
ordinary branches.

The ordinary formulas are exactly:

```text
raw_upside = raw_member_and_forward
bounded_core = conservative_member_and_forward and conservative_bounded_safety
strict_core = conservative_member_and_forward and conservative_strict_safety
bounded_joint = bounded_core and attribution_gate
strict_joint = strict_core and attribution_gate

5  raw_upside and not raw_bounded_safety and not bounded_core
6  raw_upside and raw_bounded_safety and not bounded_core
7  not raw_upside and not bounded_core
8  bounded_core and not attribution_gate
9  bounded_joint and not strict_core
10 strict_joint and control_match
11 strict_joint and not control_match
```

Coverage validation precedes every conjunction, so empty evidence can never
satisfy a universal predicate. Failure to cover the exact plan is instrument
invalid, not a negative or positive ordinary science result.
