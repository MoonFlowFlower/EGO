# Ranking Robustness Audit

## Scope

本审计只回答一个问题：

- 在不实现 prototype 的前提下，当前 `MVS-aligned compact` 是否仍是稳健的一号 build-first 候选

它不回答：

- sentience / consciousness
- runtime 主链接入是否已经成立
- replay conversation 是否已经通过

## Inputs

- candidate set:
  - `baseline_chat`
  - `narrative_identity_shell`
  - `identity_only`
  - `trace_only`
  - `operational_self_loop_core`
  - `mvs_aligned_compact`
  - `active_inference_self_model`
- formal gate:
  - 只有通过 `T1-T5 + composite >= 0.74` 的候选才允许赢得 build-first ranking
- audit script:
  - [run_operational_selection_robustness.py](/mnt/d/Project/AIProject/MyProject/Ego/scripts/codex/run_operational_selection_robustness.py)
- raw artifact:
  - [SELF_MODEL_SELECTION_ROBUSTNESS_CURRENT.json](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/SELF_MODEL_SELECTION_ROBUSTNESS_CURRENT.json)
  - [SELF_MODEL_SELECTION_ROBUSTNESS_CURRENT.md](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/SELF_MODEL_SELECTION_ROBUSTNESS_CURRENT.md)

## Audit Design

- random seeds: `5`
  - `20260409`
  - `20260410`
  - `20260411`
  - `20260412`
  - `20260413`
- held-out splits: `3`
  - `balanced`
  - `identity_stress`
  - `repair_stress`
- weight scenarios: `35`
  - process mix `±10%` / `±20%`
  - per-target weight perturbation `±10%` / `±20%`
  - per-process-dimension perturbation `±20%`
- total ranking scenarios:
  - `5 x 3 x 35 = 525`

## Results

### Win rate by candidate

- `MVS-aligned compact`: `0.9867`
- `Active-inference self-model`: `0.0133`
- `Operational self-loop core`: `0.0000`
- 其他候选：`0.0000`

### Rank variance

- `MVS-aligned compact`
  - mean rank: `1.0133`
  - rank variance: `0.0132`
  - min/max rank: `1 / 2`
- `Active-inference self-model`
  - mean rank: `1.9867`
  - rank variance: `0.0132`
  - min/max rank: `1 / 2`
- `Operational self-loop core`
  - mean rank: `3.0000`
  - rank variance: `0.0000`

### Sensitivity to weight changes

- `MVS-aligned compact`
  - weight rank change rate: `0.0137`
  - mean weight score delta: `0.0006`
- `Active-inference self-model`
  - weight rank change rate: `0.0137`
  - mean weight score delta: `0.0018`
- `MVS` 只在 `7` 个 `process_minus_20` 场景里被 `active-inference` 反超
- `MVS` 在 baseline weights 的 `15/15` 个 seed/split 组合里都是第一

## Robustness Rule

当前采用的稳健性判据：

- `MVS` 必须赢下全部 baseline-weight seed/split runs
- overall win rate `>= 0.50`
- top2 rate `>= 0.95`
- challenger overall win rate `<= 0.35`

## Conclusion

- 当前结论：`yes`
- 正式口径：
  - `MVS-aligned compact remains the robust build-first choice under the current synthetic audit.`

## Ceiling

这份报告能证明：

- `MVS-aligned compact` 不只是单次 held-out eval 的偶然赢家
- 在当前 synthetic ranking setup 下，它对 seeds / splits / weights 有稳定优势

这份报告不能证明：

- replay conversation 效果
- OpenEmotion runtime 主链接入后的真实收益
- sentience / consciousness / 主观体验

## Decision impact

- 可以继续保留：
  - `current best build-first candidate under current eval setup = MVS-aligned compact`
  - `current backup/challenger under current eval setup = active-inference self-model`
- 还不能继续保留：
  - broad `build now` 宣称
  - prototype implementation without replay validator
