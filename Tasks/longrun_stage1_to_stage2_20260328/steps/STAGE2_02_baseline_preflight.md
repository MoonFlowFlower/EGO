# STAGE2_02_baseline_preflight

```yaml
step_id: STAGE2-02
type: baseline
status: pending
```

## real_goal

Verify that the current MVP11.5 readiness toolchain is executable before rerunning mixed Layer 2 readiness.

## success_criteria

- response intent checker tests execute
- mixed Layer 2 rerun harness executes
- intent alignment E2E executes
- baseline results and any failures are written to a report

## authority_source

- `steps/STAGE2_01_mvp11_5_execution_contract.json`

## current_layer

```yaml
current_layer: verification
main_chain_status: shadow
```

## required_artifacts

- `reports/02_baseline_preflight.md`

## required_tests

- `./EgoCore/.venv/bin/python -m pytest -s -q OpenEmotion/tests/test_response_intent_checker.py`
- `cd OpenEmotion && ../EgoCore/.venv/bin/python tests/test_t07_3_mixed_layer2_rerun.py`
- `./EgoCore/.venv/bin/python -m pytest -s -q OpenEmotion/tests/testbot/test_intent_alignment_e2e.py`

## promotion_blockers

- harness cannot run
- checker or E2E baseline broken

## next_minimal_closure_action

If baseline passes, run the real mixed Layer 2 rerun.
