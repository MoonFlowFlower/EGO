# SELF_MODEL_UPDATE_GATE

## Goal

定义 `self_model_delta` / `self_model_update_candidates` 如何从 `proto_self_v2` 进入 formal owner store，并确保更新受治理、可审计、可回退。

## Formal Write Path

1. `proto_self_v2` 产出：
   - `self_model_delta`
   - `self_model_update_candidates`
2. `self_model_update_gate` 校验：
   - source legitimacy
   - field allowlist
   - identity invariants
   - drift thresholds
   - audit completeness
3. gate 通过后：
   - 写入 formal owner store
   - 记录 revision / diff / trace ref / timestamp

## Allowed Update Triggers

- repeated behavioral evidence
- stable developmental cycle patterns
- verified long-horizon consistency
- governance-approved revision
- contradiction resolution with evidence

## Invalid Update Triggers

- one-off self-description text
- isolated user wording imitation
- ungrounded introspective guess
- legacy mirror output without formal normalization
- direct host shortcut write

## Gate Checks

- field is in formal owner contract
- update mode is declared
- before/after snapshot present
- diff present
- trace reference present
- confidence class present
- hard invariants not violated
- drift response selected when thresholds are exceeded

## Writeback Outcomes

- `allow_writeback`
- `hold_for_review`
- `reject`
- `rollback_to_last_stable`

## Hard Rules

- no direct write from EgoCore into formal owner store
- no write from legacy mirror path
- no update may grant reply authority or tool authority
