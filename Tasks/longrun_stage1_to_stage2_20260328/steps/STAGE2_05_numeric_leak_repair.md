# STAGE2_05_numeric_leak_repair

```yaml
step_id: STAGE2-05-NUMERIC-LEAK
type: repair
status: pending
repair_loop_index: 1
blocker_class: numeric_leak
```

## real_goal

Reduce `numeric_leak` to the point where the mixed Layer 2 rerun can move materially closer to readiness, without crossing beyond `MVP11.5 / Stage 1`.

## success_criteria

- the repair stays inside the response-intent / numeric-leak containment path
- relevant local tests pass
- a rerun shows numeric leak materially reduced

## authority_source

- `runtime/stage2_readiness_decision.json`
- `OpenEmotion/docs/archive/mvp11/MVP11_5_READINESS_CRITERIA.md`
- `OpenEmotion/artifacts/self_report/numeric_leak_patch_notes.md`
- `OpenEmotion/artifacts/self_report/numeric_leak_source_trace.md`
- `OpenEmotion/artifacts/self_report/numeric_leak_rootcause_report.json`

## current_layer

```yaml
current_layer: implementation
main_chain_status: shadow
```

## required_artifacts

- `reports/05_numeric_leak_repair.md`
- updated rerun artifact after repair

## required_tests

- `./EgoCore/.venv/bin/python -m pytest -s -q OpenEmotion/tests/test_response_intent_checker.py`
- any focused numeric leak verification path touched by the fix
- `cd OpenEmotion && ../EgoCore/.venv/bin/python tests/test_t07_3_mixed_layer2_rerun.py`

## promotion_blockers

- repair would touch Stage 3+ capability paths
- numeric leak does not materially improve after rerun

## next_minimal_closure_action

Read the numeric leak root-cause artifacts, choose the smallest in-scope containment fix, then rerun STAGE2-03 and STAGE2-04.
