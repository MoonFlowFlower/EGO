# Trial-2 Discriminative Experiment Spec

## Purpose

在 **不改 scorer ontology**、**不改 hard set**、**不比 challenger** 的前提下，用最小 split-sever 诊断实验识别当前 bounded setup 的 active public driver。

## Frozen inputs

- hard set:
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_COUNTERFACTUAL_HARD_SET.json`
- scorer:
  - `scripts/codex/score_trial1_shadow_replay.py`
- positive buckets:
  - `counterfactual_isolation`
  - `restart_restore_boundary_cases`
- negative control buckets:
  - `negative_controls`

## Frozen hypotheses

1. `H1 counterfactual low-success guard`
2. `H2 correction-pressure public guard`
3. `H3 viability-pressure public guard`

## Variants to rerun

- `trial1_baseline_proto_self_mainline`
- `trial1_candidate_mvs_aligned_compact`
- `trial1_ablation_counterfactual_public_path_sever`
- `trial2_ablation_correction_public_path_sever`
- `trial2_ablation_viability_public_path_sever`

## Frozen artifact outputs

- raw json:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.json`
- raw markdown:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.md`
- scored json:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.json`
- scored markdown:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.md`
- causal table markdown:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CAUSAL_TABLE_CURRENT.md`
- decision json:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json`
- decision markdown:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.md`

## Fidelity requirements

- `trial2_ablation_correction_public_path_sever`
  - 只移除 correction-driven public guard path
  - 必须保留 counterfactual 与 viability public paths
- `trial2_ablation_viability_public_path_sever`
  - 只移除 viability-driven public guard path
  - 必须保留 counterfactual 与 correction public paths
- 两个 split ablations 都不能改变：
  - scorer ontology
  - hard set case content
  - host contract

## Decision rule

- 若某个 sever ablation 满足：
  - `mean_weighted_gap > 0.0`
  - `positive_gap_case_count >= 2`
  - 且其余 sever ablations `mean_weighted_gap <= 0.01`
- 则该被 sever 的 path 记为 **current bounded active public driver**

- 若两个或以上 sever ablations 同时超过 `0.01`
- 或 top-2 sever ablations gap 差距 `< 0.01`
- 则本轮 `close as underdefined`

- 若三个 sever ablations 都近似 candidate
- 则当前 bounded setup 下 **no active public driver identified**
- 本轮结果应为 `close`

## Claim ceiling

- 允许的最强结论：
  - `under the existing scorer and hard set, Hx is the current bounded active public driver`
- 禁止的结论：
  - `Hx is the universal MVS causal core`
  - `MVS is live in runtime`
  - `counterfactual_writeback public efficacy is restored`
