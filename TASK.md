# MVP-7.1 Goal: Self-Model Capability Boundary + Tool Routing

**Status:** COMPLETE ✅

## Hard Gates (Must Pass)

- [x] B1 回归：全量 tests 0 failed（允许 skipped 仅来自 quarantine registry）
- [x] B2 追溯：reports 必含 commit/hash/scenario_set_id + tool_policy_version
- [x] B3 防过拟合：holdout + ood 不退化
- [x] B4 因果证据：tool availability intervention effect size 过阈值；ablation drop ratio 过阈值

## Deliverables

### US-7101 ToolRegistry v0 ✅
- `emotiond/tool_registry.py`: 工具定义、权限、冷却、成本模型
- `emotiond/tool_policy.py`: is_tool_allowed(self_model, tool, context) -> (allowed, reason_code)
- 结构化 reason codes（可聚合统计）

### US-7102 Capability Router ✅
- `emotiond/agent_router.py`: 任务意图分类 + 工具路由
- 输入：task_intent + self_model + user_state + drive_state
- 输出：plan = {steps, tool_calls, fallback}
- Fallback 策略：clarify, degrade, request_human, decline

### US-7103 Audit & Provenance ✅
- 工具调用写入 episode/ledger 时带 provenance
- Trace_id + policy_version 审计链

### US-7104 Causal Tests ✅
- `scenarios/test_tool_availability_intervention.yaml`
- `scenarios/test_tool_availability_ablation.yaml`
- `tests/test_tool_system.py`: 36 tests (registry/policy/router/intervention/ablation)

### US-7105 DMN Integration ✅
- `emotiond/dmn_tick.py`: 后台 tick 支持 tool-needed backlog
- Tension + cooldown 门控防止刷屏

## Test Results

- **Total tests:** 2094 collected
- **Passed:** 2084+ (full suite passing)
- **Failed:** 0
- **Skipped:** 0 (quarantine empty)

## Commits

```
f4953ec feat(mvp71): US-7101/7102/7104 tool registry, policy, router + causal tests
f18e980 feat(mvp7.1): remediate test_outcome_capture_integration.py
c4867a0 feat(mvp7.1): remediate first 2 integration tests
```

## Architecture Principle

**外部符号变量硬约束（B 路线）**
- LLM 不决定"我能不能用工具"
- LLM 只提出候选计划
- ToolPolicy 决定并审计落盘

## Next: MVP-7.2 Planning

- Tool execution layer
- Advanced fallback strategies
- Multi-tool orchestration
