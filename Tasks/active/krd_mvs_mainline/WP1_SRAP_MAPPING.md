# WP1 SRAP / self_report -> ResponsePlan Mapping

> authority: `Tasks/MVS_task_plan.md`
> scope: `WP1 宿主壳收稳（MVP11.5）`
> date: 2026-03-31
> conclusion: `partial_mapping_without_host_gate`

## Summary

`ResponsePlan` 现在已经承载了 `WP1` 需要的核心表达字段，但当前结论只能到：

- **contract carrier 已成型**
- **host-side SRAP gate 尚未形成**

决定性证据有两条：

1. `ResponsePlan` 已正式带上 `speaker_mode / epistemic_status / commitment_level / must_include / must_not_upgrade / tone_bounds`
2. `EgoCore` 当前输出主链里，没有正式调用 `ResponseIntentChecker`

因此，`WP1` 当前不是“字段还没落地”，而是“字段已落地，但还没有形成会真正阻断越权表达的宿主 gate”。

## Authority Source

- [response_plan.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/response_contract/response_plan.py)
- [output_check.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/response_contract/output_check.py)
- [memory_claim_gate.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/response_contract/memory_claim_gate.py)
- [response_intent_checker.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/emotiond/response_intent_checker.py)
- [core.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/emotiond/core.py)
- [test_response_intent_checker.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/tests/test_response_intent_checker.py)
- [test_shadow_mode.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/tests/test_shadow_mode.py)

## 映射表

| SRAP / self_report 约束 | 当前宿主承载点 | 状态 | 说明 |
|---|---|---|---|
| `speaker_mode` | `ResponsePlan.speaker_mode` | 已映射 | 已进入 direct/runtime/status plan builder |
| `epistemic_status` | `ResponsePlan.epistemic_status` | 已映射 | 已进入宿主表达合同 |
| `commitment_level` | `ResponsePlan.commitment_level` | 已映射 | 已进入宿主表达合同 |
| `must_not_upgrade` | `ResponsePlan.must_not_upgrade` | 已映射 | 现有默认值已覆盖 `epistemic/commitment/tone` |
| `tone_bounds` | `ResponsePlan.tone_bounds` | 部分映射 | 已有 `intensity_cap / allowed_tones / forbidden_tones`，但尚未进入 host-side checker |
| `must_include` | `ResponsePlan.must_include` | 部分映射 | 已落成 tuple[str]，但丢失了 `type / position` 这类结构化语义 |
| `allowed_claims` | 无 | 未映射 | 当前宿主合同没有 claim 白名单 |
| `forbidden_claims` | 无 | 未映射 | 当前宿主合同没有 pattern 级禁止项 |
| `grounding / raw_state` | 无 | 未映射 | 当前宿主主链没有把 grounding state 送入 intent checker |
| `violation result` (`status / would_block / confidence / violation_class`) | 无 | 未映射 | 当前宿主没有正式生成 intent violation verdict |
| `shadow logging / SRAP report` | OpenEmotion shadow path | 未接宿主主链 | 仍停在 OpenEmotion 侧 shadow 观察，不是 EgoCore host gate |

## 当前已证实

### 1. 宿主表达合同字段已形成

证据：

- [response_plan.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/response_contract/response_plan.py)
- [test_response_contract.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/tests/test_response_contract.py)

结论：

- `ResponsePlan` 已经不只是 skeleton
- 它已经能承载 `WP1` 要求的核心表达边界字段
- 这证明方向正确，不需要另造 `response_contract_v2`

### 2. `numeric_leak` checker 本体可工作

复算证据：

- `env PYTHONPATH=OpenEmotion python3 -m pytest -s -q --noconftest OpenEmotion/tests/test_response_intent_checker.py -k numeric`
  - `5 passed`
- `env PYTHONPATH=OpenEmotion python3 -m pytest -s -q --noconftest OpenEmotion/tests/test_response_intent_checker.py`
  - `47 passed`

结论：

- OpenEmotion 侧 `ResponseIntentChecker` 本体不是坏的
- `numeric_leak` 规则族在局部验证层面是成立的

## 当前决定性缺口

### 1. 宿主输出主链没有调用 `ResponseIntentChecker`

代码证据：

- `rg -n "check_intent\\(|ResponseIntentChecker\\(" EgoCore/app OpenEmotion/emotiond OpenEmotion/tests/testbot`
- 结果显示：
  - `EgoCore/app/*` 无调用
  - `OpenEmotion/emotiond/core.py` 有 shadow path 调用

结论：

- 当前 SRAP intent gate 仍停在 OpenEmotion 侧 shadow / runtime 语义
- 没有进入 EgoCore 宿主正式输出主链
- 因此 `WP1` 不能宣称“表达主权已真正 enforced”

### 2. SRAP shadow 当前也未达到 readiness 稳态

复算证据：

- `env PYTHONPATH=OpenEmotion python3 -m pytest -s -q --noconftest OpenEmotion/tests/test_response_intent_checker.py OpenEmotion/tests/test_shadow_mode.py`
  - 结果：`4 failed, 93 passed`

失败集中在：

- qualitative error `would_block`
- shadow log severity
- qualitative confidence
- full workflow integration

结论：

- 当前不能把 shadow report 当成 readiness 完成证据
- `numeric_leak = 0` 也不能借由 shadow 稳态直接宣称成立

## Readiness 裁决

- `WP1` 方向：正确
- `WP1` 当前 readiness：不成立
- 根因层级：不是字段缺失，而是 **host-side intent gate 未接 + shadow readiness 未稳**

## 下一步唯一最高优先级动作

在现有主路径上实现最小 `ResponsePlan -> ResponseIntentChecker` 宿主接线，然后重跑 `WP1 readiness` 复算。
