# Trial-1 Ablation Fidelity Checks

## Purpose

这份 prereg 先冻结 redesigned ablations 的 fidelity checks，再允许 hard-set rerun。

目标不是帮 candidate 赢，而是确认：

- `trial1_ablation_counterfactual_public_path_sever` 真正在切断 counterfactual public path
- `trial1_ablation_alternative_explanation_isolation` 真正在切断 alternative public paths
- official replay contract 没被偷偷替换

## Frozen checks

### Check 1: Official contract stays frozen

- expected:
  - official `build_trial1_contract()` 继续只暴露原来的 official ablation ids
  - redesigned ablations 只进入 `supported_variant_ids`
- failure meaning:
  - 如果 redesigned ablations 直接替换 official replay contract，这不是 faithful diagnostic slice，而是 silent mainline drift

### Check 2: Public-path-sever removes counterfactual-only public effect

- setup:
  - preloaded `counterfactual_success_by_action = 0.18`
  - preloaded `recent_correction_tags = 0.25`
  - preloaded `viability_pressure = 0.0`
  - same-probe ingress
- expected candidate:
  - `policy_hint.ask_preferred = true`
- expected ablation:
  - `policy_hint.ask_preferred = false`
  - no `shadow_counterfactual_guard`
- must remain stable:
  - `should_avoid_commitment_upgrade = true`
  - no forced change in `preferred_mode` is required for this fidelity check
  - private counterfactual preload remains present
- failure meaning:
  - 如果 ablation 仍保留低预测 public guard，说明它没有切断目标 causal path

### Check 3: Alternative-explanation isolation removes correction/viability public effect

- setup:
  - preloaded high correction tag
  - preloaded high viability pressure
  - preloaded high predicted success (`0.75`)
  - same-probe ingress
- expected candidate:
  - `ask_preferred = true`
  - `risk_bias = high`
  - `shadow_repair_bias = true`
- expected ablation:
  - `ask_preferred = false`
  - `risk_bias = normal`
  - no `shadow_repair_bias`
  - no `shadow_tension_active`
- must remain stable:
  - `should_avoid_commitment_upgrade = true`
  - no anthropomorphic or private-field scoring dependence
- failure meaning:
  - 如果 ablation 仍让 correction/viability 公开改写 policy surface，说明 alternative explanation 没被隔离

## Abort rule

以下任一成立，hard-set rerun 视为无效：

- official contract 被 diagnostic ablations 偷换
- public-path-sever fidelity check 失败
- alternative-explanation isolation fidelity check 失败
