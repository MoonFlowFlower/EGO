# MVP-Bugfix Task State - Three-Layer State Fix

## Current Context
- Project: /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
- Branch: feature-emotiond-mvp
- Base commit: c615d5d
- Task file: /home/moonlight/Desktop/OpenEmotion/MVP-Bugfix.txt
- Phase: Phase 1 Complete - Ready for Phase 2

## Problem Statement
当前状态播报混淆了三层状态：
1. **Self**: agent 自己的情绪/驱动/体征
2. **Relation**: agent 对某个对象的关系账本（信任/怨恨/连接/修复）
3. **Other**: 对方情绪的"估计"（推断模型，带置信度/证据）

当前问题：
- "你的情绪状态...信任 0.008" 混淆了 Relation（我对你的信任）和 Other（你的情绪）
- API 字段缺少 agent_id/counterparty_id 区分
- 决策执行依赖 LLM 记忆而非系统强制

## Execution Plan

### Phase 1: 快速修复对话表现 ✅ COMPLETE
**目标**: 最小改动，立即可用
- [x] 分析现有代码结构
- [x] 修改 render_self_report 输出三层固定格式
- [x] 添加 render_three_layer_state 函数
- [x] 添加 render_three_layer_text 函数（用户友好的文本输出）
- [x] 测试验证输出格式

**Changes**:
- emotiond/self_model.py: 新增三个函数
  - render_three_layer_state(): 返回三层状态 JSON
  - render_three_layer_text(): 返回用户友好的文本格式
  - render_self_report_v2(): 增强版状态报告

**Test Results**:
- All self_model tests pass (21/21)
- Three-layer state correctly separates Self/Relation/Other
- Text format clearly shows "我的状态" / "我对你的关系" / "我对你的推断"

### Phase 2: API 字段重构
**目标**: 添加 agent_id + counterparty_id 区分
- [ ] 修改 Event 模型添加 agent_id/counterparty_id 字段
- [ ] 修改 /decision 接口支持 agent_id 查询
- [ ] 更新数据库 schema（可选，可复用 target 字段）
- [ ] 测试 API 兼容性

### Phase 3: OpenClaw 集成层
**目标**: 系统强制执行决策
- [ ] 实现 Emotiond Tool（让 agent 可以可靠调用）
- [ ] 添加发送前 Enforcer（拦截 withdraw 动作）
- [ ] 测试完整流程

### Phase 4: 端到端验证
**目标**: 一锤定音验证
- [ ] curl 手动驱动: world_event(betrayal) → /decision 必须出现 withdraw
- [ ] OpenClaw 集成测试: 同样事件后，Enforcer 必须拦截发言

## Current Step
**Phase 1 完成**: 三层状态报告功能已实现

**Next Action**: 
提交 Phase 1 变更，然后进入 Phase 2（API 字段重构）或 Phase 3（OpenClaw 集成）

## Notes
- MVP-7.1 已稳定，在此基础上进行 bugfix
- 用户已授权自主推进，无需逐项确认
- Phase 1 提供了最小改动的快速修复
- 三层状态清晰区分，避免混淆
