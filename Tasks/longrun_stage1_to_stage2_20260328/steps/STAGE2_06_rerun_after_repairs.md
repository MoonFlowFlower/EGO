# STAGE2_06_rerun_after_repairs

```yaml
step_id: STAGE2-06
type: rerun_after_repairs
status: pending
```

## real_goal

Rerun the mixed Layer 2 readiness chain after bounded repairs and recompute readiness again.

## success_criteria

- repaired system reruns mixed Layer 2 successfully
- readiness is recomputed again
- batch either advances to admission or stops with a blocker dossier

## authority_source

- `runtime/stage2_readiness_decision.json`
- repair reports from `reports/`

## current_layer

```yaml
current_layer: verification
main_chain_status: shadow
```

## required_artifacts

- `reports/06_rerun_after_repairs.md`
- refreshed `runtime/stage2_readiness_decision.json`

## required_tests

- rerun chain
- readiness recompute chain

## promotion_blockers

- readiness still not met after 2 loops

## next_minimal_closure_action

Either move to admission review or stop with a blocker dossier.
