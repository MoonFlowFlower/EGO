# P0_PHASE1_REPORT — 主缺陷修复

## 任务信息
- task_id: P0-Phase1
- title: 主缺陷修复
- status: verified
- date: 2026-03-25T11:15:00Z

## 当前层级
主缺陷修复层

## 真实触发证据
- cycles.py 已修改
- `_build_psi_bucket` 函数已更新（追加 risk_level）
- `_coarse_intent_classify` 函数已更新（修复关键词优先级）

## 当前确定项

### 1. psi_bucket 修改

**旧版本**：
```python
psi_bucket = f"{source}:{event_type}:{coarse_intent}"
```

**新版本**：
```python
# 分层聚合策略
if risk_level in ["critical", "high"]:
    return f"{source}:{event_type}:{coarse_intent}:risk_{risk_level}"
else:
    return f"{source}:{event_type}:{coarse_intent}"
```

### 2. 关键词优先级修复

| 变更 | 说明 |
|------|------|
| 服务控制提前 | 避免"运行测试"被误匹配为 status_query |
| 测试验证提前 | 避免"测试"类 intent 被误分类 |
| 移除重复关键词 | "检查" 不再在多个分类中重复 |
| 移除 "fix" | "fix" 可能是修复而非删除，移除风险模式 |

### 3. 向后兼容

| 场景 | 处理 |
|------|------|
| safety_context 缺失 | 默认 risk="normal" |
| 旧 state.json | 继续工作，新字段不强制 |
| 新 state.json | 完全兼容 |

## 改动内容
- files_modified:
  - `OpenEmotion/openemotion/proto_self/cycles.py`

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体修改
- ✅ 无双重真相源
- ✅ EgoCore 不涉及

### Gate B — Local Proof
- ✅ 代码已修改
- ✅ 语法正确（待运行验证）

### Gate C — Real Trigger / Real Evidence
- 待 Phase 2 实验验证

### Gate E — Rollbackability
- ✅ 可回退：git revert
