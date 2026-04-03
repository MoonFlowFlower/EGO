# SELF_MODEL_REPLAY_CONTRACT

## Goal

定义 self-model revision 的持久化、审计和 replay contract，保证 `MVP13` 的变化可复核、可解释、可回退。

## Required Revision Fields

每次更新至少写出：
- `model_version`
- `revision_id`
- `timestamp`
- `update_source`
- `trace_reference`
- `before_snapshot`
- `after_snapshot`
- `diff`
- `confidence_class`
- `gate_verdict`

## Replay Contract

- replay 输入：
  - base owner snapshot
  - ordered revision log
- replay 输出：
  - reconstructed owner snapshot
  - reconstructed `model_version`
- 判定：
  - same base + same revision log -> same reconstructed state

## Audit Contract

- 每次 writeback 都必须留下 audit trail
- audit trail 必须能追到 source event / trace
- 无 audit trail 的状态不可用于 proof

## Rollback Contract

- 任何进入 `hold_for_review` 或 `reject` 的更新不得污染 stable owner snapshot
- `rollback_to_last_stable` 必须指向明确 revision 边界
- rollback 本身也必须写 audit

## Hard Rules

- replay contract 不得依赖 legacy mirror artifacts
- replay contract 不得依赖自由文本解释代替 diff
- replayable 先于 expressive wording
