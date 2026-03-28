# Stage1 Blocker Dossier

## Current Formal State

- batch: `stage1_to_stage2_20260328`
- current formal stage: `Stage 1`
- readiness decision: `not_ready`
- next repair candidate: `numeric_leak`

## Confirmed Blockers

1. `numeric_leak`
   - readiness requires `numeric_leak = 0`
   - current mixed rerun surfaced `38` numeric leak violations
2. `overall_violation_rate`
   - current value `0.71`
   - too high for readiness-grade mixed baseline
3. `sample_size`
   - current mixed rerun produced `100`
   - readiness guidance suggests cumulative `>= 200`
4. `certainty_upgrade`
   - still high in mixed runtime-path results
5. `commitment_upgrade`
   - still high in mixed runtime-path results

## Scope Guard

- Do not enter `Stage 3 / MVP12`.
- Repairs must stay inside `MVP11.5 / Stage 1`.
- First repair should target the smallest blocker with the clearest authority contract:
  - `numeric_leak`
