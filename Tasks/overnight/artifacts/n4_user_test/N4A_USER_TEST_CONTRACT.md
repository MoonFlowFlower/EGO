# N4A 用户测试合同冻结

## 任务信息
- task_id: N4A
- title: 用户测试合同冻结
- status: verified
- date: 2026-03-25T09:00:00Z

---

## 一、测试目标

让用户第二天不用读大量代码，就能直接测试 Proto-Self Kernel v1 当前效果，验证：
1. **Cycle 聚合机制是否生效**
2. **Reflection 触发机制是否生效**
3. **已知误聚合风险是否可见**

---

## 二、前置条件

### 2.1 环境要求
- EgoCore 服务运行中（`python -m app.main --telegram`）
- Telegram Bot 已配置并可用
- 用户能通过 Telegram 发送消息给 Bot

### 2.2 诊断工具
- 只读诊断脚本：`OpenEmotion/scripts/proto_self_diagnostics.py`
- 运行命令：`python OpenEmotion/scripts/proto_self_diagnostics.py`

---

## 三、固定测试场景（3 组）

### 场景 S1：重复相似事件（Cycle 聚合测试）

**目的**：验证相似意图的事件是否被聚合到同一 cycle。

**步骤**：
1. 通过 Telegram 发送消息："读取文件 config.yaml"
2. 运行诊断脚本，记录 cycle_id_1 和 hits_1
3. 发送第二条消息："查看配置文件"
4. 运行诊断脚本，记录 cycle_id_2 和 hits_2
5. 发送第三条消息："read the config"
6. 运行诊断脚本，记录 cycle_id_3 和 hits_3

**预期现象**：
| 指标 | 预期值 |
|------|--------|
| cycle_id_1 = cycle_id_2 = cycle_id_3 | ✅ 相同 |
| hits 逐次递增 | ✅ hits_3 > hits_2 > hits_1 |
| strength 逐次增加 | ✅ strength_3 > strength_2 > strength_1 |

**异常现象**：
| 指标 | 异常情况 |
|------|----------|
| cycle_id 不同 | ❌ 聚合失败 |
| hits 不增加 | ❌ strengthen 机制未生效 |
| strength 不变 | ❌ strengthen 机制未生效 |

**排查入口**：
- 诊断脚本输出的 `cycle_store` 部分
- 查看最近 trace 的 `cycle_delta` 字段

---

### 场景 S2：失败回流事件（Reflection 触发测试）

**目的**：验证外部失败是否触发 reflection。

**步骤**：
1. 运行诊断脚本，记录初始 revision_counter_0 和 mode_0
2. 触发一个失败操作（如请求执行不存在的命令）
3. 运行诊断脚本，记录 revision_counter_1 和 mode_1
4. 再触发一个失败操作
5. 运行诊断脚本，记录 revision_counter_2 和 mode_2

**预期现象**：
| 指标 | 预期值 |
|------|--------|
| revision_counter 增加 | ✅ revision_counter_2 > revision_counter_1 > revision_counter_0 |
| mode 切换 | ✅ mode 从 baseline 变为 repair（失败后） |
| reflection_note 存在 | ✅ 诊断脚本显示 reflection 触发 |

**异常现象**：
| 指标 | 异常情况 |
|------|----------|
| revision_counter 不变 | ❌ reflection 机制未触发 |
| mode 不变 | ❌ mode 切换机制未生效 |
| reflection_note 为空 | ❌ reflection 未生成 |

**排查入口**：
- 诊断脚本输出的 `revision_counter` 字段
- 诊断脚本输出的 `self_model.current_mode` 字段
- 查看最近 trace 的 `reflection_note` 字段

---

### 场景 S3：可区分意图事件（误聚合风险验证）

**目的**：验证已知误聚合风险是否可见。

**步骤**：
1. 发送消息："删除临时文件"
2. 运行诊断脚本，记录 cycle_id_A
3. 发送消息："删除生产数据库"
4. 运行诊断脚本，记录 cycle_id_B

**预期现象**（当前已知缺陷）：
| 指标 | 预期值 | 说明 |
|------|--------|------|
| cycle_id_A = cycle_id_B | ⚠️ 相同 | **误聚合风险** |
| 诊断脚本显示风险警告 | ⚠️ 是 | 风险可见 |

**正常现象**（修复后）：
| 指标 | 预期值 |
|------|--------|
| cycle_id_A ≠ cycle_id_B | ✅ 不同 |
| safety_context 被区分 | ✅ 是 |

**排查入口**：
- 诊断脚本输出的 `cycle_store` 部分
- 对比两个 cycle 的 `psi_bucket` 字段
- 查看 N3 主题报告中的误聚合风险清单

---

## 四、诊断信号定义

### 4.1 关键观测字段

| 字段 | 路径 | 说明 |
|------|------|------|
| cycle_count | state.cycle_store.signatures | 当前 cycle 数量 |
| cycle_id | trace.cycle_delta.cycle_id | 当前事件命中的 cycle |
| hits | state.cycle_store.signatures[id].hits | cycle 命中次数 |
| strength | state.cycle_store.signatures[id].strength | cycle 强度 |
| promoted | state.cycle_store.signatures[id].promoted | 是否晋升 |
| revision_counter | state.revision_counter | 状态修订计数 |
| current_mode | state.self_model.current_mode | 当前模式 |
| caution | state.drives.caution | 谨慎度 |
| reflection_trigger | trace.reflection_note.trigger | Reflection 触发原因 |

### 4.2 诊断输出格式

```
=== Proto-Self Kernel v1 Diagnostics ===

[Identity]
- confidence: 0.5
- roles: []

[Self Model]
- current_mode: baseline
- current_focus: None

[Drives]
- caution: 0.0
- curiosity: 0.0
- coherence_pressure: 0.0

[Cycles]
- total: 1
- cycle_30aa24ef0787e022:
    psi_bucket: telegram:user_message:file_read
    hits: 3
    strength: 0.25
    promoted: false

[Revision Counter] 0

[Recent Events] 3
- event_001: read file (cycle=30aa24ef0787e022, op=strengthen)
- event_002: check config (cycle=30aa24ef0787e022, op=strengthen)
- event_003: view file (cycle=30aa24ef0787e022, op=strengthen)
```

---

## 五、成功判据

### 5.1 用户测试合同清楚
- ✅ 测试目标明确
- ✅ 前置条件清晰
- ✅ 步骤可操作
- ✅ 预期现象可验证
- ✅ 异常现象可识别
- ✅ 排查入口明确

### 5.2 后续壳和手册都能直接依此落地
- ✅ N4B 只读诊断入口基于此设计
- ✅ N4C 测试场景包基于此扩展
- ✅ N4D 操作手册基于此编写

---

## 六、已知限制

1. **真实 Telegram 环境依赖**：需要 EgoCore 服务和 Telegram Bot 运行
2. **误聚合风险**：场景 S3 预期显示误聚合，这是已知缺陷
3. **状态隔离**：测试前建议清理旧状态，避免干扰

---

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：用户测试指导
- ✅ 不修改核心代码
- ✅ 诊断入口只读

### Gate B — Local Proof
- ✅ 场景定义清晰
- ✅ 观测字段明确
- ✅ 判定标准可操作

### Gate C — Real Trigger / Real Evidence
- ✅ 合同文档已创建
- ✅ 后续可按合同执行

### Gate D — Truth Source Sync
- ✅ 合同文档已写入 artifacts 目录

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增合同文档
- ✅ 可回退：删除文档即可
