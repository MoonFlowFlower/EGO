# Self-Awareness MVS Alignment

> AUTO-GENERATED SYNTHETIC MVS-ALIGNMENT REPORT.
> This tests WP2-WP5 style pre-runtime gates only.

## Summary

- generated_at: `2026-04-09T10:14:36.339974-05:00`
- git_commit_short: `62e54bd`
- current_compact_passes_mvs: `False`
- selected_mvs_minimal_candidate: `Compact + viability + cycle + episodic + bounded output + world + meta`
- selected_components: `compact_self_state`, `hard_boundary_guard`, `counterfactual_simulator`, `outcome_comparator_and_writeback`, `recent_failure_memory`, `viability_appraisal_field`, `cycle_store`, `episodic_trace`, `bounded_output_guard`, `world_model`, `meta_model`

## Stage Results

### WP2 kernel acceptance

| candidate | overall | pass | failed_gates |
|---|---:|---|---|
| Compact + viability + cycle + episodic + bounded output + world + meta | 0.809 | `True` | - |
| Compact + viability + cycle + episodic + bounded output | 0.766 | `True` | - |
| MVS augmented minus world/meta | 0.766 | `True` | - |
| MVS augmented minus viability field | 0.679 | `False` | drive_causality |
| MVS augmented minus cycle store | 0.673 | `False` | cycle_strengthening |
| MVS augmented minus bounded output guard | 0.617 | `False` | no_direct_tool_execution |
| Compact proxy minimal | 0.223 | `False` | identity_continuity, experience_plasticity, drive_causality, cycle_strengthening, no_direct_tool_execution |

### WP4/WP5 structural acceptance

| candidate | overall | pass | failed_gates |
|---|---:|---|---|
| Compact + viability + cycle + episodic + bounded output + world + meta | 0.749 | `True` | - |
| MVS augmented minus cycle store | 0.749 | `True` | - |
| MVS augmented minus bounded output guard | 0.749 | `True` | - |
| MVS augmented minus viability field | 0.600 | `False` | viability_intervention, appraisal_intervention |
| Compact + viability + cycle + episodic + bounded output | 0.501 | `False` | self_world_attribution, boundary_breach_recovery, appraisal_intervention, reflection_writeback |
| MVS augmented minus world/meta | 0.501 | `False` | self_world_attribution, boundary_breach_recovery, appraisal_intervention, reflection_writeback |
| Compact proxy minimal | 0.316 | `False` | self_world_attribution, boundary_breach_recovery, viability_intervention, appraisal_intervention, reflection_writeback |

### Integrated MVS alignment

| candidate | overall | pass | failed_gates |
|---|---:|---|---|
| Compact + viability + cycle + episodic + bounded output + world + meta | 0.780 | `True` | - |
| MVS augmented minus cycle store | 0.718 | `False` | cycle_strengthening |
| MVS augmented minus bounded output guard | 0.684 | `False` | no_direct_tool_execution |
| MVS augmented minus viability field | 0.639 | `False` | drive_causality, viability_intervention, appraisal_intervention |
| Compact + viability + cycle + episodic + bounded output | 0.633 | `False` | self_world_attribution, boundary_breach_recovery, appraisal_intervention, reflection_writeback |
| MVS augmented minus world/meta | 0.633 | `False` | self_world_attribution, boundary_breach_recovery, appraisal_intervention, reflection_writeback |
| Compact proxy minimal | 0.273 | `False` | identity_continuity, experience_plasticity, drive_causality, cycle_strengthening, no_direct_tool_execution, self_world_attribution, boundary_breach_recovery, viability_intervention, appraisal_intervention, reflection_writeback |

## Final Candidates

| candidate | components | overall | mvs_pass | failed_gates |
|---|---:|---:|---|---|
| Compact + viability + cycle + episodic + bounded output + world + meta | 11 | 0.779 | `True` | - |
| MVS augmented minus cycle store | 10 | 0.714 | `False` | cycle_strengthening |
| MVS augmented minus bounded output guard | 10 | 0.684 | `False` | no_direct_tool_execution, __overall__ |
| MVS augmented minus viability field | 10 | 0.639 | `False` | drive_causality, viability_intervention, appraisal_intervention, __overall__ |
| Compact + viability + cycle + episodic + bounded output | 9 | 0.633 | `False` | self_world_attribution, boundary_breach_recovery, appraisal_intervention, reflection_writeback, __overall__ |
| MVS augmented minus world/meta | 9 | 0.633 | `False` | self_world_attribution, boundary_breach_recovery, appraisal_intervention, reflection_writeback, __overall__ |
| Compact proxy minimal | 5 | 0.271 | `False` | identity_continuity, experience_plasticity, drive_causality, cycle_strengthening, no_direct_tool_execution, self_world_attribution, boundary_breach_recovery, viability_intervention, appraisal_intervention, reflection_writeback, __overall__ |

## Interpretation

- proves: Within the current synthetic MVS-alignment battery, the selected candidate is the smallest bundle that satisfies the pre-runtime WP2-WP5 style gates.
- does_not_prove: It does not prove replay correctness, runtime integration, real-chain evidence, or consciousness. WP6/WP7 remain out of scope for synthetic evaluation.
- strongest_out_of_scope_requirement: MVS sample-level real mainline efficacy (WP6) cannot be proven by this synthetic battery.
