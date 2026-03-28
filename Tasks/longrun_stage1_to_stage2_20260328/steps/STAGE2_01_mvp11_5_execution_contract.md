# STAGE2_01_mvp11_5_execution_contract

```yaml
step_id: STAGE2-01
type: contract_refresh
status: pending
```

## real_goal

Replace stale MVP11.5 T07 shadow-readiness commands with the current executable contract backed by real tests, artifacts, and reports in this repo.

## success_criteria

- stale commands are explicitly deprecated for this batch
- a machine-readable execution contract points only to real repo-backed tests, artifacts, and reports
- later steps can use the refreshed contract without consulting obsolete T07 commands

## authority_source

- `OpenEmotion/tasks/MVP11_5/T07_shadow_rerun_readiness.yaml`
- `OpenEmotion/tests/test_t07_3_mixed_layer2_rerun.py`
- `OpenEmotion/tests/test_response_intent_checker.py`
- `OpenEmotion/tests/testbot/test_intent_alignment_e2e.py`
- `OpenEmotion/artifacts/self_report/`
- `OpenEmotion/artifacts/roadmap/evidence/MVP11_5_T07.3.md`

## current_layer

```yaml
current_layer: representation
main_chain_status: shadow
```

## required_artifacts

- `steps/STAGE2_01_mvp11_5_execution_contract.json`
- `reports/01_execution_contract_refresh.md`

## required_tests

- path existence check
- contract review

## promotion_blockers

- stale commands still referenced
- execution contract missing real outputs

## next_minimal_closure_action

Lock the executable contract and move to baseline preflight.
