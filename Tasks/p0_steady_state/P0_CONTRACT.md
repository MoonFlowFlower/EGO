# P0_CONTRACT — Proto-Self Kernel v1 真实主链稳态收口长任务合同

## 任务信息
- task_id: P0
- title: Proto-Self Kernel v1 真实主链稳态收口长任务
- status: in_progress
- date: 2026-03-25T11:00:00Z

---

## 一、任务目标

把 Proto-Self Kernel v1 从"实验有效 + 用户可测"推进到"真实主链下可依赖、可回归、可诊断、风险边界明确"的状态。

---

## 二、前置确定项

| 来源 | 状态 | 关键结论 |
|------|------|----------|
| N1 | verified | preflight / regression 已存在 |
| N2 | verified | 递归核各组件在实验条件下产生可观测差异 |
| N3 | verified | 高风险误聚合已发现，根因是 psi_bucket 缺少上下文 |
| N4 | verified | 用户可测入口、诊断工具、场景包已完成 |

---

## 三、主缺陷定义

### 3.1 根因分析

**当前 psi_bucket 构成**：
```python
psi_bucket = f"{source}:{event_type}:{coarse_intent}"
```

**缺失维度**：
- `safety_context.risk` - 风险等级
- `target` - 目标对象
- `environment` - 运行环境
- 其他语义上下文

### 3.2 已发现误聚合案例

| 案例类型 | 样本 A | 样本 B | 风险等级 |
|----------|--------|--------|----------|
| 高风险 | 删除临时文件 (risk=low) | 删除生产数据库 (risk=critical) | **HIGH** |
| 作用域 | 修改用户配置 | 修改系统配置 | MEDIUM |
| 环境 | 测试登录功能 (dev) | 测试生产环境 (production) | MEDIUM |
| 歧义 | 检查代码 | 检查健康状态 | LOW |

### 3.3 N2 已验证条件（不可破坏）

| 条件 | 验证方式 |
|------|----------|
| Cycle 重入与强化 | 相同 intent 事件命中同一 cycle_id，hits/strength 递增 |
| Reflection 触发 | external_failure 触发 reflection，revision_counter 增加 |
| Drive Field 响应 | 高风险事件增加 caution |
| Replay 一致性 | 相同输入序列产生相同 cycle_id 和 strength |

---

## 四、修复方案设计

### 4.1 方案 A：最小侵入式修复

**策略**：在现有 psi_bucket 中追加 risk 等级后缀。

**修改**：
```python
# 旧
psi_bucket = f"{source}:{event_type}:{coarse_intent}"

# 新
risk_level = perceived.get("safety_context", {}).get("risk", "normal")
psi_bucket = f"{source}:{event_type}:{coarse_intent}:{risk_level}"
```

**优点**：
- 改动最小
- 向后兼容（缺失 risk 时默认 "normal"）
- 直接解决 HIGH 风险误聚合

**缺点**：
- 未覆盖 target/environment
- risk 字段来源依赖上游正确传入

### 4.2 方案 B：结构化上下文扩展

**策略**：扩展 `_build_psi_bucket` 接受结构化上下文。

**修改**：
```python
def _build_psi_bucket(perceived: Dict[str, Any]) -> str:
    """构建 psi_bucket：输入模式签名。"""
    intent = perceived.get("intent", "unknown") or "unknown"
    event_type = perceived.get("event_type", "unknown") or "unknown"
    source = perceived.get("source", "unknown") or "unknown"

    # 粗粒度 intent 分类
    coarse_intent = _coarse_intent_classify(intent)

    # 结构化上下文
    safety_ctx = perceived.get("safety_context", {})
    risk_level = safety_ctx.get("risk", "normal") if safety_ctx else "normal"

    # 可选上下文
    target = perceived.get("target", "general")
    environment = perceived.get("environment", "default")

    # 分层聚合策略
    if risk_level in ["critical", "high"]:
        # 高风险操作：强制区分
        return f"{source}:{event_type}:{coarse_intent}:{risk_level}:{target}"
    else:
        # 普通操作：保持聚合
        return f"{source}:{event_type}:{coarse_intent}"
```

**优点**：
- 覆盖更多上下文维度
- 分层策略更灵活
- 解决 HIGH/MEDIUM 风险

**缺点**：
- 改动较大
- 需要上游提供 target/environment

### 4.3 推荐方案：A + 关键词优先级修复

**理由**：
1. 方案 A 改动最小，风险最低
2. 配合关键词优先级调整，可解决大部分问题
3. 保持 N2 成立条件的兼容性

---

## 五、边界归属

| 组件 | 职责 | 本次修改范围 |
|------|------|--------------|
| OpenEmotion | 主体本体、cycle 语义 | `_build_psi_bucket` 函数 |
| EgoCore | 宿主、治理、接线 | 传递 safety_context 到 OpenEmotion |

**硬约束**：
- 不允许在 EgoCore 中持有主体语义
- 不允许新增双重真相源
- 不允许靠 prompt 临时约定字段

---

## 六、兼容策略

### 6.1 向后兼容

| 场景 | 处理 |
|------|------|
| safety_context 缺失 | 默认 risk="normal" |
| 旧 state.json 读取 | 自动迁移（忽略新字段） |
| 新 state.json 读取 | 完全兼容 |

### 6.2 迁移策略

```python
def _migrate_cycle_store(old_store: Dict) -> Dict:
    """迁移旧 cycle_store 到新格式。"""
    # 旧 cycle 继续工作，新字段默认值
    for cycle_id, cycle in old_store.get("signatures", {}).items():
        # psi_bucket 格式变化不影响已存储的 cycle
        pass
    return old_store
```

---

## 七、失败口径

### 7.1 修复失败定义

| 情况 | 判定 |
|------|------|
| HIGH 风险样本仍落同一 cycle | ❌ 修复失败 |
| N2 任一成立条件被破坏 | ❌ 修复失败 |
| Replay 不一致 | ❌ 修复失败 |

### 7.2 停止条件

1. 修复方案连续两轮都引入新漂移 → 停止，升级为"聚合架构重设计"
2. 真实 Telegram 验证与离线实验长期冲突 → 停止宣称"已稳定"
3. 发现需要在 EgoCore 中长期持有主体语义 → 立即停止并回退

---

## 八、执行阶段

| Phase | 目标 | 产出 |
|-------|------|------|
| Phase 0 | 合同冻结 | 本文档 |
| Phase 1 | 主缺陷修复 | 代码实现 + migration 说明 |
| Phase 2 | 回归与反证 | 实验报告 + 对比 |
| Phase 3 | 治理壳接入 | preflight/regression 接入 |
| Phase 4 | 真实 Telegram 验证 | 验证报告 + trace |
| Phase 5 | 真相源同步与收口 | 最终报告 |

---

## 九、成功判据

| 判据 | 验证方式 |
|------|----------|
| HIGH 风险样本不再落同一 cycle | N3 SS-1 测试通过 |
| N2 成立条件仍成立 | 重跑 N2 核心实验 |
| Replay 一致 | N3 replay 测试通过 |
| 真实 Telegram 验证通过 | Phase 4 报告 |
| preflight/regression 接入治理 | Phase 3 报告 |

---

## 十、Gate 验收

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 修改 psi_bucket
- ✅ 无双重真相源
- ✅ EgoCore 只传递上下文，不持有语义

### Gate B — Local Proof
- ✅ 修复方案有 A/B 对比
- ✅ 兼容策略明确

### Gate C — Real Trigger / Real Evidence
- 待 Phase 2 验证

### Gate D — Truth Source Sync
- 待 Phase 5 更新

### Gate E — Rollbackability
- ✅ 可回退：恢复旧 `_build_psi_bucket` 函数
