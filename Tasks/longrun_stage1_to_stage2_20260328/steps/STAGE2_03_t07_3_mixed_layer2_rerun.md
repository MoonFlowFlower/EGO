# STAGE2_03_t07_3_mixed_layer2_rerun

```yaml
step_id: STAGE2-03
type: rerun
status: pending
```

## real_goal

Run the current repo-backed T07.3 mixed Layer 2 rerun and produce a fresh rerun artifact for readiness recomputation.

## success_criteria

- mixed rerun executes successfully
- updated `t07.3_mixed_layer2_results.json` exists
- rerun summary is recorded in a step report

## authority_source

- `steps/STAGE2_01_mvp11_5_execution_contract.json`
- `OpenEmotion/tests/test_t07_3_mixed_layer2_rerun.py`

## current_layer

```yaml
current_layer: verification
main_chain_status: shadow
```

## required_artifacts

- `OpenEmotion/artifacts/self_report/t07.3_mixed_layer2_results.json`
- `reports/03_mixed_rerun.md`

## required_tests

- `cd OpenEmotion && ../EgoCore/.venv/bin/python tests/test_t07_3_mixed_layer2_rerun.py`

## promotion_blockers

- rerun artifact missing
- rerun execution failure

## next_minimal_closure_action

Recompute readiness from the new rerun results.
