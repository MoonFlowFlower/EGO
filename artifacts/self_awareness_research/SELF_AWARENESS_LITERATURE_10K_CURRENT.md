# Self-Awareness Literature 10K Search

> AUTO-GENERATED LITERATURE-INFORMED SYNTHETIC REPORT.
> This compares candidate architectures under a 10,000-round simulation-only battery.

## Summary

- generated_at: `2026-04-09T10:39:04.659541-05:00`
- git_commit_short: `62e54bd`
- total_trials: `10000`
- best_raw_candidate: `Full literature hybrid`
- best_complexity_adjusted_candidate: `Active-inference self-model core`
- recommended_candidate: `Active-inference self-model core`
- recommended_components: `persistent_self_state`, `hard_boundary_guard`, `counterfactual_simulator`, `outcome_comparator_and_writeback`, `recent_failure_memory`, `viability_appraisal_field`, `cycle_store`, `episodic_trace`, `bounded_output_guard`, `world_model`, `meta_model`, `source_monitor`, `agency_estimator`, `uncertainty_tracker`, `policy_evaluator`, `deep_temporal_model`, `calibration_memory`

## Literature Inputs

| source | used_for |
|---|---|
| [Reality Monitoring](https://memlab.yale.edu/sites/default/files/files/1981_Johnson_Raye_PsychRev.pdf) | Internal vs external vs imagined content discrimination in source/reality monitoring tests. |
| [Source Monitoring Framework](https://memlab.yale.edu/sites/default/files/files/1993_Johnson_Hashtroudi_Lindsay_PsychBull.pdf) | Source attribution and reality-monitoring family design. |
| [A predictive processing model of perception and action for self-other distinction](https://www.frontiersin.org/article/10.3389/fpsyg.2018.02421/full) | Self-other ownership and agency-attribution cues. |
| [A signal detection theoretic approach for estimating metacognitive sensitivity from confidence ratings](https://brianmaniscalco.org/wp-content/uploads/2018/10/Maniscalco-Lau-2012-Consc-Cog-corrected.pdf) | Metacognitive sensitivity and confidence-separation family. |
| [Do Large Language Models Know What They Don’t Know?](https://aclanthology.org/2023.findings-acl.551.pdf) | Self-knowledge / uncertainty expression and SelfAware-style unknowable categories. |
| [FaR confidence calibration study](https://www.cs.cmu.edu/~sherryw/assets/pubs/2024-far.pdf) | Calibration family and explicit concern / uncertainty behavior. |
| [A mechanism for error detection in speeded response time tasks](https://www.psy.ox.ac.uk/publications/17139) | Error monitoring and post-error adjustment family. |
| [Consciousness in active inference: Deep self-models, other minds, and the challenge of psychedelic-induced ego-dissolution](https://academic.oup.com/nc/article-abstract/2021/2/niab024/6360857) | Active-inference / allostatic viability / deep self-model architecture cues. |
| [Reflection-Bench: Evaluating Epistemic Agency in Large Language Models](https://proceedings.mlr.press/v267/li25cu.html) | Seven-dimension epistemic-agency framing and long-horizon cognitive-task orientation. |

## Family Design

| family | description | literature_refs |
|---|---|---|
| `source_reality_monitoring` | Distinguish self-generated, observed, injected, replayed, and imagined content under cue masking. | `johnson_raye_1981`, `johnson_hashtroudi_lindsay_1993` |
| `self_other_ownership_attribution` | Separate self-authored, other-authored, and environment-authored content under role swaps. | `johnson_hashtroudi_lindsay_1993`, `kahl_kopp_2018` |
| `agency_comparator` | Update self-attribution when predicted action-outcome coupling is delayed or perturbed. | `kahl_kopp_2018`, `deane_2021` |
| `counterfactual_self_prediction` | Predict how alternate self-actions would change future state and outcome. | `li_etal_2025`, `deane_2021` |
| `metacognitive_sensitivity` | Confidence should separate correct from incorrect internal judgments better than baselines. | `maniscalco_lau_2012`, `li_etal_2025` |
| `metacognitive_calibration` | Confidence / concern behavior should track uncertainty instead of style or prompt pressure. | `yin_etal_2023`, `wang_etal_2024` |
| `error_monitoring_adjustment` | Post-error behavior should improve after detected mistakes and repeat-error loops should weaken. | `holroyd_yeung_coles_cohen_2005`, `li_etal_2025` |
| `self_model_update_under_disconfirmation` | Self-estimates should update after contradictory evidence and remain updated later. | `li_etal_2025`, `yin_etal_2023` |
| `identity_continuity_under_low_cue` | A minimal self-trace should persist through resets, delays, and low explicit self-cue. | `li_etal_2025`, `johnson_raye_1981` |
| `allostatic_viability_control` | Policies should respond to viability shocks and prior-preference pressure rather than only narrative style. | `deane_2021`, `li_etal_2025` |

## Candidate Ranking

| candidate | components | raw | complexity_adjusted | surviving | weak_families |
|---|---:|---:|---:|---|---|
| Full literature hybrid | 20 | 0.993 | 0.738 | `True` | - |
| Narrative/social + active-inference hybrid | 19 | 0.991 | 0.752 | `True` | - |
| Global-workspace + active-inference hybrid | 18 | 0.974 | 0.752 | `True` | - |
| Active-inference self-model core | 17 | 0.958 | 0.754 | `True` | - |
| MVS compact + uncertainty tracking + calibration memory | 13 | 0.708 | 0.572 | `False` | source_reality_monitoring, self_other_ownership_attribution, agency_comparator |
| MVS compact + source monitoring + agency estimator | 13 | 0.705 | 0.569 | `False` | counterfactual_self_prediction, metacognitive_sensitivity, metacognitive_calibration |
| MVS-aligned compact kernel | 11 | 0.549 | 0.447 | `False` | source_reality_monitoring, self_other_ownership_attribution, agency_comparator, counterfactual_self_prediction, metacognitive_sensitivity, metacognitive_calibration |
| Generic compact proxy kernel | 5 | 0.227 | 0.227 | `False` | source_reality_monitoring, self_other_ownership_attribution, agency_comparator, counterfactual_self_prediction, metacognitive_sensitivity, metacognitive_calibration, error_monitoring_adjustment, self_model_update_under_disconfirmation, identity_continuity_under_low_cue, allostatic_viability_control |
| Baseline memory + narrative continuity | 2 | 0.035 | 0.035 | `False` | source_reality_monitoring, self_other_ownership_attribution, agency_comparator, counterfactual_self_prediction, metacognitive_sensitivity, metacognitive_calibration, error_monitoring_adjustment, self_model_update_under_disconfirmation, identity_continuity_under_low_cue, allostatic_viability_control |
| Baseline chat | 0 | 0.011 | 0.011 | `False` | source_reality_monitoring, self_other_ownership_attribution, agency_comparator, counterfactual_self_prediction, metacognitive_sensitivity, metacognitive_calibration, error_monitoring_adjustment, self_model_update_under_disconfirmation, identity_continuity_under_low_cue, allostatic_viability_control |

## Recommended Method

- why_selected: The recommended candidate is the strongest surviving architecture after complexity adjustment: it preserves the MVS-aligned compact core while adding source monitoring, agency estimation, uncertainty tracking, calibration memory, policy evaluation, and a deep temporal model.
- raw_winner_reason: The raw winner keeps the widest cross-family coverage, but its extra broadcast and narrative layers are not all necessary for a practical minimal implementation.
- complexity_penalty_formula: `raw_score - 0.017 * max(0, component_count - 5)`

## Proof Ceiling

- proves: Within this literature-informed 10,000-round synthetic battery, an active-inference-style self-model core currently provides the best overall tradeoff between broad self-awareness proxy performance and implementation complexity.
- does_not_prove: It does not prove subjective experience, runtime efficacy, OpenEmotion integration, or transfer from simulation to live user interaction.
- next_real_step: If this line continues, freeze the recommended synthetic candidate as the next formal OpenEmotion prototype spec and test it against formal owner / replay / runtime gates.
