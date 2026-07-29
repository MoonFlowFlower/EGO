# 001E-I1 TDD Report

Status: `I1_IMPLEMENTATION_COMPLETE_LOCAL_ONLY__FORMAL_RUN_NOT_AUTHORIZED`

Date: 2026-07-29

## Verdict

The frozen `CAOT-BOOL-v2` exact reference evaluator, independent recomputation
path, bounded controls/ablations, leakage checks, source-owned bounded streams,
replay primitives, strict receipts, and fail-closed formal boundary are
implemented and locally tested. No complete 16,384-pair population was run and
no 001E result or evidence artifact was generated.

This is an implementation result, not a scientific or learning result.

## Layer

- Engineering implementation layer.
- Bounded mechanism-fixture support only.
- `science_weight=0`.
- Lineage discontinuity is preserved: this lane does not repair, rescore, or
  reopen R5--R7, 001D/I1/I2/X1, or CAOT-v1.

## Repository readback

- Repository root: `D:\Project\AIProject\MyProject\Ego`
- Branch: `codex/ego-v2-compositional-causal-transfer-001e`
- I1 base commit: `2ed241f9ab9ff5fa1f20ff37e42804e9c1cd4cbb`
- Implementation-card commit / pre-I1-report HEAD:
  `74776a1be40a0137521c046bf14dd7d64e3c582b`
- Auto-Remote-Anchor: `forbidden`; no push or tag was attempted.

## Frozen authority readback

| Authority | SHA-256 |
|---|---|
| 001E task card | `83fb2a5b7e2a26f5dc9408962768f4329f3c5932405b82142394804c7e9a3619` |
| collision record | `265d530c584bd38cf76b11c374475cb9678b37ec889484c35a4cbc25c23659b4` |
| frozen design | `8a60c0e8521b02d7423fa5320ba8013e29c128e27aaec1a4a3ee4674fac0027d` |
| I1 implementation card | `59e43ac6168f4da7288474b269f4f7474f77c631a5ad6f04ae6d24d463c6575a` |

All four values matched the bytes read during final local verification.

## Files changed by I1 implementation

- `scripts/codex/check_ego_v2_compositional_causal_transfer_preflight_001e.py`
- `scripts/codex/recompute_ego_v2_compositional_causal_transfer_preflight_001e.py`
- `scripts/codex/tests/test_check_ego_v2_compositional_causal_transfer_preflight_001e.py`
- `docs/codex/tasks/ego-v2-p1-compositional-causal-transfer-preflight-001e/I1_TDD_REPORT.md`

Final pre-report source hashes:

- primary: `066894eb709cee8a5b331f33443f4b2cc65c875308bb4b48dbf3cbea827af7cc`
- independent: `a0e2cc97fe142a503bfff3112433a8a91c60e3c999837bb300fc7dde46011944`
- tests: `b161b351aa1b0fd4d9515d26d69c29e37e1df75115da769d8fa8d79a27c1dffc`

## Implemented bounded surface

- 128 Boolean programs and eight three-bit compositions with exact GF(2)
  evaluation and seven-term traces.
- Exact `Fraction` arithmetic for scratch, exact-source, local-shift, mixture
  conditioning, prediction, Brier risk, EVSI, query minimizers, and tie
  envelopes.
- 23 registered controls, of which 19 are invalidating equal-access controls;
  transition-table, successor-map, and FSM-planner arms fail closed as not
  applicable to this schema.
- 11 registered ablations/invariances/positive controls.
- Complete materialized candidate-rule lookup ceiling: 256 H1 query states,
  3,584 H2 prediction states, 3,840 total states; table SHA-256
  `de268283c551a488a9d319386015cae2fa47f0bed7fe36450bc477f0bb22523f`.
- Source-owned primary, fresh-replay, and independent-recompute stream
  producers. The bounded fixture used three actual pairs:
  `(0,0)`, `(37,36)`, and `(85,127)`.
- Strict evidence receipt schemas, input and receipt hashing, code-path hashes,
  aggregation-rule identifiers, row/tamper rejection, and complete-population
  coverage checks.
- Both formal entrypoints and the evidence-shaped gate/verdict receipt paths
  unconditionally raise `FORMAL_EXECUTION_NOT_AUTHORIZED_001E_I1`.

## TDD record

Representative RED observations retained during implementation:

1. Focused import failed because the primary module did not exist.
2. Independent-path test reached `14 passed, 1 failed`; the independent
   recomputation callable was missing.
3. Evidence-chain test failed with `KeyError: 'status'` before strict receipts
   were implemented.
4. Control-completeness test failed because `INVALIDATING_CONTROL_IDS` did not
   yet exist.
5. Stream-lineage test expected rejection but the initial interface accepted
   caller-supplied rows rather than owning evaluation.
6. Final hostile test failed because `_make_evidence_receipt` could mint a
   pass-shaped computed-gate receipt and `dispatch_verdict` could consume it.

The last retained RED command was:

```powershell
python -m pytest scripts/codex/tests/test_check_ego_v2_compositional_causal_transfer_preflight_001e.py -k "gate_receipts_are_computed" -q
```

Observed RED: `1 failed, 20 deselected`; expected
`FormalExecutionNotAuthorizedError` was not raised.

After the minimum fail-closed patch, the same command returned:

```text
1 passed, 20 deselected in 31.79s
```

Final focused verification:

```powershell
python -m py_compile scripts/codex/check_ego_v2_compositional_causal_transfer_preflight_001e.py scripts/codex/recompute_ego_v2_compositional_causal_transfer_preflight_001e.py scripts/codex/tests/test_check_ego_v2_compositional_causal_transfer_preflight_001e.py
python -m pytest scripts/codex/tests/test_check_ego_v2_compositional_causal_transfer_preflight_001e.py -q
git diff --check
```

Result: byte compilation passed; `21 passed in 47.46s`; `git diff --check`
returned clean output.

Relevant predecessor regression command covered:

- `test_check_ego_v2_conservative_transfer_static_headroom_001c_r6.py`
- `test_check_ego_v2_conservative_transfer_public_action_feasibility_001c_r7.py`
- `test_check_ego_v2_active_transfer_headroom_preflight_001d.py`
- `test_check_ego_v2_active_transfer_headroom_hostile_counterexample_001d_x1.py`

Result: `114 passed in 791.83s`.

## Baseline results

No formal baseline result exists. Bounded invocation tests show that all 23
registered controls are callable or explicitly fail closed as N/A, scratch
inference reports zero source-table inference reads, and `SOURCE_DELETE`
matches scratch on tested fixtures.

The complete finite candidate-rule lookup is an explicit claim ceiling: the
reference candidate's public behavior can be materialized over this frozen
finite surface. Therefore this evaluator cannot by itself distinguish learned
generalization from lookup amortization.

Also, `EXACT_SOURCE_ONLY_ACTIVE_WITH_SCRATCH_FALLBACK` and
`SOURCE_CONSISTENCY_WITH_SCRATCH_FALLBACK` share the same exact/fallback
implementation branch in this reference. They are not behaviorally independent
controls here.

## Ablation results

No formal population ablation result exists. Bounded tests invoked all 11
registered arms, checked source deletion against scratch, checked row
permutation and variable relabeling invariance, and rejected both hidden-truth
positive controls.

`SERIALIZED_STATE_RESET` and `SERIALIZED_STATE_SWAP` change serialized bytes but
do not change behavior in the tested reference. This exact evaluator is
stateless; these checks do not establish state-history dependence.

## Replay result

No formal 16,384-row replay result exists. On the three-pair bounded fixture,
the primary producer, fresh replay producer, and separately implemented
recompute producer each generated their own rows through their own call paths.
Tampered and incomplete streams were rejected. A three-row stream is explicitly
rejected by formal-integrity coverage checks.

## Review and independence boundary

- Statistical/method audit: final exact-blocker verdict `PASS`.
- Data-flow audit: `PASS` after source-owned stream repair.
- Hostile admission audit: `PASS` for the I1 implementation-only boundary after
  formal gate execution was made unreachable.

These are same-model internal role separations, not external independent audits.
The independent recomputation module is a separate code path, not an
independent researcher or independently trained model.

## Stop conditions triggered

- The route/task authority forbids formal experiment execution in I1.
- Accordingly, the complete population, formal gate reduction, verdict
  production, artifact generation, threshold tuning, world/seed runs, push,
  and tag were not performed.
- No implementation stop condition requiring rollback was triggered.

## Artifacts generated

None. In particular,
`artifacts/EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-001E` is absent.

## Claim ceiling

This report supports only implementation existence, exact arithmetic on the
tested finite fixtures, bounded primary/replay/recompute agreement, registry
coverage, leakage/tamper rejection, and a fail-closed formal boundary.

The next action, if separately authorized by the live route, is a distinct
pre-run provenance/run card that binds the finalized implementation hashes,
runtime/dependency receipts, exact formal command, artifact allowlist, complete
control and ablation execution, replay, and independent row recomputation.

## What this does not prove

It does not prove reference headroom, positive transfer, negative-transfer
avoidance, baseline non-equivalence, causal-schema induction, non-memorization,
meta-learning, online adaptation, a learned or neural transfer selector,
spontaneous method formation, survival benefit, AGI, agency, subjectivity,
consciousness, emotion, companion readiness, or electronic life. The current
001E/I1 system is an exact hard-coded evaluator/reference infrastructure; it is
not the self-learning neural mechanism that is the longer-term target.
