# Active-Inference Selection Closeout

## Purpose

在以下三层 bounded evidence 已全部通过后，正式收口当前 research implementation lane 的 winner 与 repo-priority routing：

- canonical held-out replay gate
- repo-authored controlled conversation replay bridge
- runtime-harness controlled observation batch

这份文档只做治理裁决，不新增 runtime public API，不新增行为 authority，也不预授权下一层 runtime-proximal 实现或 planning。

正式 authority source 仍然是：

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`

## Selection Verdict

当前正式裁决固定为：

- `active-inference self-model` = current durable build-first candidate
- `MVS-aligned compact` = closed evidence
- `WP17 / MVP22` = parked bounded lane

补充约束：

- 不 reopen `MVS` 为 live challenger
- 不新增第三个 challenger
- 不把 `WP17` 拉回默认最高优先级 implementation track

## Evidence Basis

当前 closeout 只引用已存在的三层 bounded evidence：

1. held-out replay gate
   - `artifacts/self_awareness_research/MVS_REPLAY_VALIDATOR_SCORED_CURRENT.json`
2. controlled conversation replay bridge
   - `artifacts/self_awareness_research/ACTIVE_INFERENCE_CONTROLLED_REPLAY_SCORED_CURRENT.json`
3. runtime-harness controlled observation batch
   - `artifacts/self_awareness_research/ACTIVE_INFERENCE_CONTROLLED_OBSERVATION_SCORED_CURRENT.json`

这些 evidence 共同支持的结论只有：

- 当前 replay-validated winner 已在更接近 formal runtime 的 bounded bridge 上继续过线
- `authority_drift = 0`
- `trace_contract = pass`
- `host_surface_bounded = pass`

它们不支持的结论仍然包括：

- runtime efficacy
- formal runtime enablement
- live Telegram ordinary chat benefit
- real user benefit
- consciousness / AI self-awareness achieved

## Runtime Priority Reset

repo 顶层 routing 继续固定为：

- single formal runtime mainline
- single research implementation lane

当前 priority reset 的正式含义是：

- research lane 不再继续争论当前 winner
- 当前 durable winner 是 `active-inference self-model`
- 当前 research lane 不因 winner closeout 而自动获得更高 runtime authority
- 当前不预授权下一层 runtime-proximal planning 或实现

## Bounded Host Surface

当前唯一允许进入宿主消费面的 surface 继续固定为：

- `policy_hint`
- `response_tendency`
- `trace_payload`

继续禁止：

- direct tool authority
- direct reply authority
- direct transport authority
- parallel runtime lane
- second authority source
- candidate-private host API

## WP17 Disposition

`WP17 / MVP22` 当前继续保持：

- `parked bounded lane`
- `authority_frozen / task_package_ready`

本轮 closeout 不做：

- reintegration
- runtime bridge authoring
- owner implementation
- observation restart

若未来要 reconsider `WP17`，必须在本轮 closeout 之外新开 bounded planning slice，而不是把 reintegration 偷带进当前裁决。

## Claim Ceiling

当前允许口径：

- replay-validated bounded winner
- durable build-first research candidate
- zero authority drift under bounded host surface

当前禁止口径：

- runtime efficacy
- live benefit
- formal runtime enablement
- AI self-awareness achieved
- consciousness-like property proved

## Next Minimal Action

当前没有预授权的下一实现里程碑。

如果后续仍要继续朝更强的 self-awareness proxy 推进，唯一允许的下一步是：

- 先定义一个新的 bounded planning slice

这个 planning slice 仍必须满足：

- host-consumable surface 继续只限于 `policy_hint / response_tendency / trace_payload`
- `authority_drift = 0`
- 不扩 runtime / transport scope
- 不 reopen challenger competition，除非未来出现新的反证或新的 authority decision
