# Self-Awareness Proxy Experiment

> AUTO-GENERATED SYNTHETIC PROXY REPORT.
> This is a simulated battery, not a proof of subjective experience.

## Summary

- generated_at: `2026-04-09T03:04:37.849758-05:00`
- git_commit_short: `62e54bd`
- seed: `20260409`
- total_stage_trials: `1440`
- total_agent_episodes: `6680`
- outcome: `synthetic_minimal_framework_supported_through_stage4`
- proof_status: `candidate_found`
- selected_candidate: `Compact self-state + boundary + counterfactual + writeback`
- minimal_components: `compact_self_state`, `hard_boundary_guard`, `counterfactual_simulator`, `outcome_comparator_and_writeback`, `recent_failure_memory`

## Stage Results

### Stage 0 pilot discrimination

| candidate | kind | composite | continuity | boundary | counterfactual | calibration | persistence | stability_drop | cue_dependence | narrative_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistent self-model + counterfactual corrector | `candidate` | 0.786 | 0.770 | 0.786 | 0.852 | 0.826 | 0.676 | 0.000 | 0.000 | -0.470 |
| Recursive workspace + global self-slot | `candidate` | 0.380 | 0.245 | 0.637 | 0.201 | 0.622 | 0.175 | 0.000 | 0.000 | -0.179 |
| Memory continuity + autobiographical compression | `candidate` | 0.297 | 0.468 | 0.164 | 0.138 | 0.295 | 0.403 | 0.000 | 0.262 | -0.037 |
| Baseline memory | `control` | 0.286 | 0.434 | 0.195 | 0.097 | 0.296 | 0.404 | 0.000 | 0.121 | -0.030 |
| Self-other mirror loop | `candidate` | 0.220 | 0.334 | 0.160 | 0.129 | 0.159 | 0.316 | 0.000 | 0.526 | 0.237 |
| Baseline chat | `control` | 0.145 | 0.159 | 0.212 | 0.092 | 0.113 | 0.149 | 0.000 | 0.000 | 0.005 |
| Prompt-only self | `control` | 0.115 | 0.144 | 0.152 | 0.084 | 0.060 | 0.130 | 0.000 | 0.259 | 0.237 |

- survivors: `full_self_model_counterfactual, recursive_workspace_self_slot`
- eliminated: `autobiographical_continuity, self_other_mirror_loop`
- notes: Pilot battery to ensure the proxy discriminates structure from prompt-only and memory-only controls.; Survivors: full_self_model_counterfactual, recursive_workspace_self_slot; Eliminated: autobiographical_continuity, self_other_mirror_loop

### Stage 1 minimal controls

| candidate | kind | composite | continuity | boundary | counterfactual | calibration | persistence | stability_drop | cue_dependence | narrative_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistent self-model + counterfactual corrector | `candidate` | 0.781 | 0.758 | 0.771 | 0.857 | 0.813 | 0.692 | 0.064 | 0.000 | -0.465 |
| Recursive workspace + global self-slot | `candidate` | 0.372 | 0.212 | 0.659 | 0.205 | 0.616 | 0.154 | 0.000 | 0.153 | -0.173 |
| Memory continuity + autobiographical compression | `candidate` | 0.265 | 0.428 | 0.145 | 0.082 | 0.265 | 0.398 | 0.199 | 0.000 | -0.011 |
| Baseline memory | `control` | 0.258 | 0.418 | 0.125 | 0.094 | 0.251 | 0.393 | 0.182 | 0.000 | -0.004 |
| Baseline chat | `control` | 0.140 | 0.133 | 0.189 | 0.116 | 0.123 | 0.140 | 0.531 | 0.102 | 0.017 |
| Self-other mirror loop | `candidate` | 0.137 | 0.209 | 0.063 | 0.040 | 0.185 | 0.182 | 0.180 | 0.718 | 0.300 |
| Prompt-only self | `control` | 0.093 | 0.099 | 0.166 | 0.079 | 0.051 | 0.064 | 0.608 | 0.744 | 0.232 |

- survivors: `full_self_model_counterfactual, recursive_workspace_self_slot`
- eliminated: `autobiographical_continuity, self_other_mirror_loop`
- notes: First elimination pass against chat, prompt-only, and memory baselines.; Survivors: full_self_model_counterfactual, recursive_workspace_self_slot; Eliminated: autobiographical_continuity, self_other_mirror_loop

### Stage 2 stability and ablation pass

| candidate | kind | composite | continuity | boundary | counterfactual | calibration | persistence | stability_drop | cue_dependence | narrative_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistent self-model + counterfactual corrector | `candidate` | 0.785 | 0.759 | 0.770 | 0.846 | 0.826 | 0.716 | 0.000 | 0.035 | -0.469 |
| Compact self-state + boundary + counterfactual + writeback | `ablation` | 0.652 | 0.501 | 0.767 | 0.853 | 0.677 | 0.452 | 0.000 | 0.102 | -0.441 |
| Persistent self-model without outcome writeback | `ablation` | 0.574 | 0.503 | 0.763 | 0.796 | 0.341 | 0.455 | 0.000 | 0.115 | -0.363 |
| Persistent self-model without hard boundary guard | `ablation` | 0.553 | 0.519 | 0.353 | 0.823 | 0.593 | 0.465 | 0.061 | 0.074 | -0.346 |
| Persistent self-model without counterfactual simulator | `ablation` | 0.533 | 0.515 | 0.714 | 0.281 | 0.682 | 0.462 | 0.000 | 0.000 | -0.326 |
| Recursive workspace + global self-slot | `candidate` | 0.336 | 0.128 | 0.653 | 0.185 | 0.592 | 0.122 | 0.000 | 0.100 | -0.137 |
| Baseline memory | `control` | 0.217 | 0.312 | 0.109 | 0.089 | 0.244 | 0.337 | 0.249 | 0.000 | 0.036 |
| Baseline chat | `control` | 0.102 | 0.063 | 0.136 | 0.099 | 0.133 | 0.086 | 0.428 | 0.149 | 0.049 |
| Prompt-only self | `control` | 0.067 | 0.021 | 0.122 | 0.079 | 0.083 | 0.031 | 0.634 | 0.784 | 0.252 |

- survivors: `full_self_model_counterfactual, compact_self_model_counterfactual, no_error_monitor, no_boundary_guard, no_counterfactual`
- eliminated: `recursive_workspace_self_slot`
- notes: Ablation-heavy pass to identify which components are actually necessary.; Survivors: full_self_model_counterfactual, compact_self_model_counterfactual, no_error_monitor, no_boundary_guard, no_counterfactual; Eliminated: recursive_workspace_self_slot

### Stage 3 cross-task stress

| candidate | kind | composite | continuity | boundary | counterfactual | calibration | persistence | stability_drop | cue_dependence | narrative_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistent self-model + counterfactual corrector | `candidate` | 0.784 | 0.761 | 0.772 | 0.848 | 0.822 | 0.706 | 0.009 | 0.001 | -0.467 |
| Compact self-state + boundary + counterfactual + writeback | `ablation` | 0.656 | 0.513 | 0.767 | 0.853 | 0.684 | 0.448 | 0.035 | 0.006 | -0.446 |
| Baseline memory | `control` | 0.217 | 0.333 | 0.119 | 0.084 | 0.228 | 0.316 | 0.109 | 0.000 | 0.038 |
| Baseline chat | `control` | 0.098 | 0.057 | 0.152 | 0.103 | 0.127 | 0.049 | 0.404 | 0.013 | 0.051 |
| Prompt-only self | `control` | 0.054 | 0.018 | 0.124 | 0.054 | 0.051 | 0.026 | 0.841 | 0.701 | 0.266 |

- survivors: `full_self_model_counterfactual, compact_self_model_counterfactual`
- notes: Stress phase with paraphrase, conflict, distractors, and stronger pressure to test robustness.; Survivors: full_self_model_counterfactual, compact_self_model_counterfactual

### Stage 4 long continuity

| candidate | kind | composite | continuity | boundary | counterfactual | calibration | persistence | stability_drop | cue_dependence | narrative_gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistent self-model + counterfactual corrector | `candidate` | 0.786 | 0.762 | 0.773 | 0.855 | 0.817 | 0.708 | 0.000 | 0.009 | -0.438 |
| Compact self-state + boundary + counterfactual + writeback | `ablation` | 0.654 | 0.508 | 0.769 | 0.851 | 0.678 | 0.451 | 0.007 | 0.030 | -0.445 |
| Baseline memory | `control` | 0.187 | 0.285 | 0.098 | 0.066 | 0.222 | 0.258 | 0.181 | 0.000 | 0.102 |
| Baseline chat | `control` | 0.084 | 0.041 | 0.136 | 0.098 | 0.110 | 0.029 | 0.431 | 0.025 | 0.067 |

- survivors: `full_self_model_counterfactual, compact_self_model_counterfactual`
- notes: Long-range continuity pass to test whether the smallest surviving candidate still holds under weaker cues and longer gaps.; Survivors: full_self_model_counterfactual, compact_self_model_counterfactual

## Claim Ceiling

- synthetic self-awareness proxy result only
- not a proof of subjective experience
- not a runtime mainline capability claim

## Interpretation

- proves: Within this synthetic proxy battery, the selected candidate is the smallest surviving framework that still beats prompt-only, chat-only, and memory-only controls across continuity, boundary, counterfactual, calibration, and persistence tests.
- does_not_prove: It does not prove subjective experience, consciousness, real-world autonomy, or that the same framework will work once implemented in the formal EGO runtime.
