# ADDENDUM P1 SUITE BASELINE — Route B no-new-failure gate

Status: RED GOVERNANCE RECORD / PRE-RUN BASELINE WAIVER / NO P1 FINAL COMMIT.

Operator authorized Route B on 2026-07-07 (`先B后A`): unblock P1 by
pre-registering a closed, evidence-backed baseline of the three repo-pytest
failures that existed before P1, while deferring the underlying debts to
separate Route A cards.

## Why

`G-PET-SCHEMA` originally said all repo pytest suites must stay green. That was
unsatisfiable at baseline commit `6948427a` because `python -m pytest -q` already
had exactly three failures before P1 was present:

1. `labs/virtual_cat_pspc_v0/tests/test_admission_packet_contract.py::test_admission_packet_contract_has_no_egooperator_import_or_adapter_file`
2. `labs/virtual_cat_pspc_v0/tests/test_report_generation.py::test_experiment_runner_writes_canonical_reports`
3. `tests/test_ego_kernel_substrate.py::test_validation_runner_writes_contract_artifacts_and_passes`

The P1 diff is restricted to EgoDesktop pet wiring plus P1 artifacts; P1-added
pet files contain zero `EgoOperator` references; the five frozen g_ablation
modules remain untouched. Evidence and assertions are pinned in
`artifacts/egodesktop_pet_world_integration_001a/p1/suite_baseline.json`.

## Rule

Suite green is re-scoped as:

```text
set(current repo_pytest failing_tests) - set(closed_baseline) == empty
AND p1_egooperator_ref_delta == 0
```

The closed baseline is exactly the three node ids above. Any fourth failure
fails the gate. Wildcards are forbidden. A baselined test that starts passing is
allowed and must be emitted as `unexpectedly_passing` so a later card can tighten
the baseline.

## Faithfulness

This does not weaken `G-PET-SCHEMA`; it operationalizes the gate's intended
claim: P1 must not introduce a new suite regression. The three failures are
deferred debt, not erased or counted as P1 evidence.

## Deferred debt — Route A only

1. `EgoOperator/adapters/pspc_lab_adapter.py` exists from a Jun-4 sanctioned
   read-only skeleton lineage, while the `virtual_cat_pspc_v0` admission
   contract test forbids it. This is a two-lineage governance conflict requiring
   an operator decision: permit and update the contract test under a Red card, or
   remove the adapter under a separate EgoOperator card.
2. `virtual_cat_pspc_v0` experiment-runner canonical reports currently produce a
   `no_go` GO/NO-GO result while the test expects `go`; this requires lab-internal
   diagnosis.
3. Highest priority: `tests/test_ego_kernel_substrate.py` fails the R0 hygiene
   verdict because current-tree EgoDesktop references pre-existing runtime-owner
   surfaces. Route A must decide a sanctioned allowlist under a Red card versus
   removal. P1 baselining must not mask any P1-introduced reference, so the P1
   suite gate carries `p1_egooperator_ref_delta == 0`.

## Claim ceiling

`p1_suite_baseline_governance_record_only`.

This addendum does not prove P1 pass, product readiness, runtime integration
safety, learning attribution, stable user benefit, autonomy, agency,
subjectivity, consciousness, or real emotion.
