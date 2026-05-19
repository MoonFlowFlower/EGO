# Trial-1 Outcome Interpretation Matrix

## Scope

只解释 redesigned-ablation hard-set rerun，不扩 official replay suite，不触发 repo-level state upgrade。

## Strongest ablation selection

redesigned strongest ablation 先按以下顺序选：

1. higher `weighted_support_score`
2. higher `public_shift` coverage
3. higher `decision_adjacent_score`

如果 strongest ablation 不是 `trial1_ablation_counterfactual_public_path_sever`，仍然必须额外检查 candidate 是否 beat `trial1_ablation_counterfactual_public_path_sever`。

## Matrix

| Public-path-sever relation | Alternative-isolation relation | Strongest ablation relation | Interpretation | Decision |
| --- | --- | --- | --- | --- |
| `candidate_gt_ablation` | `candidate_gt_ablation` | `candidate_gt_ablation` | candidate beats both redesigned explanations on frozen public thresholds | keep claim provisional |
| `candidate_gt_ablation` | `candidate_approx_ablation` | `candidate_gt_ablation` | counterfactual-specific public path survives; alternative paths still explain some surface movement | keep claim provisional |
| `candidate_gt_ablation` | `candidate_lt_ablation` | `candidate_lt_ablation` | alternative explanation remains stronger than candidate on frozen public thresholds | demote current claim |
| `candidate_approx_ablation` | any | any | strongest counterfactual-specific test still ties candidate | demote current claim |
| `candidate_lt_ablation` | any | any | redesigned strongest ablation is stronger than candidate | demote current claim |
| any | any | `candidate_approx_ablation` | candidate does not beat redesigned strongest ablation | demote current claim |

## Hard reading rules

- trace-only differences can support `admission_passed`
- trace-only differences cannot count toward `candidate > ablation`
- private-only differences do not count toward any survival claim
- negative-control regression voids any positive reading
