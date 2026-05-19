# Canonical Patch Plan

## Patch Objective

把 Trial-2 的 bounded H1 结果翻译成 canonical `proto_self` 的**最小 shadow-only patch**，目标只有两个：

- 在 canonical kernel 中计算 `shadow_h1`
- 把它作为 telemetry 暴露给 EgoCore 与 observation harness

不做：

- live decision promotion
- scorer ontology 变更
- second authority source

## Small-Change Verdict

这是一个小改任务，不需要 `canonical-contract-stabilization first`。

原因：

- 不改 `KernelEvent` / `KernelOutput` schema
- 不改 repo-level authority
- 只改 canonical `proto_self` 现有模块里的 derivation 逻辑
- 只使用现有 state/output surfaces

## Files To Touch In The Future Implementation Task

### Required

- `OpenEmotion/openemotion/proto_self/appraisal.py`
- `OpenEmotion/openemotion/proto_self/self_model.py`
- `OpenEmotion/openemotion/proto_self/reducers.py`
- `OpenEmotion/openemotion/proto_self/kernel.py`

### Optional, Only If Needed For Test Coverage

- `OpenEmotion/openemotion/proto_self/tests/*`
- `EgoCore/tests/*shadow*`

### Explicitly Not Allowed As Owner

- `OpenEmotion/openemotion/proto_self/trial1_shadow.py`
- `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/*`

## Planned Patch Shape

### Step 1: Read Host-Owned Shadow Flag

输入来源固定为 canonical `KernelEvent.runtime_summary`。

目标：

- 只在 host 明确开启时计算 `shadow_h1`
- OpenEmotion 不拥有 rollout authority

### Step 2: Normalize A Canonical Action Key

不要再用 Trial probe key。

canonical key 来源固定为：

- `perceived["action_class_seed"]`
- 或一个与之等价的 canonical action-family key

要求：

- deterministic
- replayable
- independent of Trial artifacts

### Step 3: Maintain Shadow H1 State

在 `self_model.update_self_model()` 中，按 canonical external outcome 更新：

- `counterfactual_success_by_action[action_key]`
- `recent_correction_tags[action_key]`

这一步只允许：

- bounded patch
- deterministic update
- replayable writeback

不允许：

- anthropomorphic state
- second memory owner

### Step 4: Split Shadow Derivation From Live Public Derivation

这是整个 patch 的关键。

future implementation 必须把 H1 分成两层：

- `shadow_h1 telemetry derivation`
- `live public decision derivation`

在 shadow-only 阶段：

- 允许计算 `would_guard`
- 允许计算 `would_ask`
- 允许写 `trace_payload["shadow_h1"]`
- 允许写 `confidence_meta["shadow_h1_*"]`

但不允许：

- 修改 live `policy_hint.ask_preferred`
- 修改 live `response_tendency.ask_needed`
- 修改 `decision_engine` prompt injection

### Step 5: Emit Traceable Shadow Telemetry

输出建议固定为两面：

- `confidence_meta`
- `trace_payload`

推荐字段：

- `shadow_h1_enabled`
- `shadow_h1_action_key`
- `shadow_h1_predicted_success`
- `shadow_h1_threshold`
- `shadow_h1_would_guard`
- `shadow_h1_neighboring_signals`

## Invariants

- flag off = zero behavior change
- flag on = telemetry only
- no second authority source
- no new proto-self engine
- no repo-level state upgrade
- no runtime efficacy claim

## Negative Cases / False-Positive Traps

- `recent_correction_tags` 升高但 `predicted_success` 不低
  - 不得报 H1 positive
- `viability_pressure` 升高但 `counterfactual signal` 不低
  - 只记 neighboring signal，不记 H1 guard
- 没有 `external_result`
  - 不得强行写 H1 success estimate
- 只有 trace change、无 host-consumable candidate
  - 只能算 telemetry presence，不能算 efficacy

## Kill Criteria

一旦 future implementation 命中以下任一条件，应停止并改做 stabilization：

- 必须改 `KernelOutput` schema 才能表达 shadow_h1
- 必须新建第二 state owner 才能保存 H1 estimate
- 必须让 `decision_engine` 直接消费 H1 才能完成最小 patch
- 必须改 scorer ontology 才能采样

## Validation Plan For The Future Implementation Task

- `python3 -m py_compile OpenEmotion/openemotion/proto_self/*.py`
- 定向 `proto_self` tests
- 定向 EgoCore shadow bridge tests
- `python3 scripts/codex/verify_repo.py --mode fast`
- task closeout 前再跑 `python3 scripts/codex/verify_repo.py --mode full`

## Rollback Point

最小 rollback 单位：

- 关闭 host-owned feature flag
- 忽略 `trace_payload.shadow_h1`
- 不消费 `confidence_meta.shadow_h1_*`

不需要：

- schema migration
- state backfill
- repo-level status change
