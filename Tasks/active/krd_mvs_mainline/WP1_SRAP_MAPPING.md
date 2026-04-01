# WP1 SRAP / self_report -> ResponsePlan Mapping

> authority: `Tasks/MVS_task_plan.md`
> scope: `WP1 宿主壳收稳（MVP11.5）`
> date: 2026-03-31
> conclusion: `host_gate_connected_but_not_ready`

## Summary

`ResponsePlan` 现在已经承载了 `WP1` 需要的核心表达字段，并且最小 host-side intent gate 已接入宿主输出主链，但当前结论仍只能到：

- **contract carrier 已成型**
- **最小 host-side SRAP gate 已接入**
- **尚未达到 readiness**

决定性证据有三条：

1. `ResponsePlan` 已正式带上 `speaker_mode / epistemic_status / commitment_level / must_include / must_not_upgrade / tone_bounds`
2. `EgoCore` 当前输出主链已在 `output_check` 中正式调用 `ResponseIntentChecker`
3. 当前 gate 只覆盖最小 `model_chat + chat_mainline` 路径，且还没有 E4 真实样本

因此，`WP1` 当前不再是“字段未落地 / gate 未接”，而是“最小 gate 已接，但 claim/grounding/readiness 仍未收稳”。

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
| `tone_bounds` | `ResponsePlan.tone_bounds` + `output_check` | 已映射 | 已进入最小 host-side checker |
| `must_include` | `ResponsePlan.must_include` | 部分映射 | 已落成 tuple[str]，但丢失了 `type / position` 这类结构化语义 |
| `allowed_claims` | `ResponsePlan.metadata` -> `output_check` | 部分映射 | checker 可消费，但主链还没有稳定 source |
| `forbidden_claims` | `ResponsePlan.metadata` -> `output_check` | 部分映射 | checker 可消费，但主链还没有稳定 source |
| `grounding / raw_state` | `ResponsePlan.metadata/ingress_context` -> `output_check` | 部分映射 | 通道已留，但当前没有正式 grounding source |
| `violation result` (`status / would_block / confidence / violation_class`) | `OutputCheckVerdict` | 已映射 | 宿主已生成 intent gate verdict 并写入交付证据 |
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

### 2. `numeric_leak` checker 本体可工作，且最小 host-side gate 已接入

复算证据：

- `env PYTHONPATH=OpenEmotion python3 -m pytest -s -q --noconftest OpenEmotion/tests/test_response_intent_checker.py -k numeric`
  - `5 passed`
- `env PYTHONPATH=OpenEmotion python3 -m pytest -s -q --noconftest OpenEmotion/tests/test_response_intent_checker.py`
  - `47 passed`
- `env PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest -s -q EgoCore/tests/test_output_check.py EgoCore/tests/test_response_contract.py EgoCore/tests/test_runtime_v2_chat_mainline.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py`
  - `29 passed, 1 warning`

结论：

- OpenEmotion 侧 `ResponseIntentChecker` 本体不是坏的
- `numeric_leak` 规则族在局部验证层面是成立的
- EgoCore host 输出主链现在也已经接上最小 `ResponsePlan -> ResponseIntentChecker`

## 当前决定性缺口

### 1. host-side gate 已接，但只覆盖最小 `model_chat` 路径

代码证据：

- `rg -n "check_intent\\(|ResponseIntentChecker\\(" EgoCore/app OpenEmotion/emotiond OpenEmotion/tests/testbot`
- 结果显示：
  - `EgoCore/app/response_contract/output_check.py` 已有调用
  - `OpenEmotion/emotiond/core.py` 有 shadow path 调用

结论：

- 当前最小 SRAP intent gate 已进入 EgoCore 宿主正式输出主链
- 但它还没有覆盖 `allowed_claims / forbidden_claims / grounding` 的正式 source
- 因此 `WP1` 仍不能宣称“表达主权已 fully enforced”

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
- 根因层级：不是字段缺失，而是 **claim/grounding 未接稳 + shadow readiness 未稳**

## 下一步唯一最高优先级动作

在现有主路径上继续，把 `allowed_claims / forbidden_claims / grounding` 接成正式 source，然后重跑 `WP1 readiness` 复算。
