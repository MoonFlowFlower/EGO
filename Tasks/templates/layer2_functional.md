# Layer 2: 功能实现模板

> 适用：功能实现、单模块改动、接口调整、测试补充
> 预期耗时：30 分钟 - 4 小时
> 执行方式：规划 → 实现 → 验收（文档接力，同一会话或单 subagent）

---

## 任务头（必须）

```yaml
task_id: L2-{YYYYMMDD}-{序号}
created_at: "2026-03-23T10:00:00Z"
owner: "负责人"
layer: 2
type: functional  # functional/verify/refactor
target_repo: EgoCore  # EgoCore/OpenEmotion/Dual
status: pending
```

---

## 真实目标

<!-- 一句话说清要解决什么问题，不是做什么功能 -->
解决 heuristic 职责膨胀问题，恢复语义主链边界正确性

---

## 成功判据

<!-- 必须是可验证的 -->
- [ ] heuristic 不再使用执行动词列表做主语义判定
- [ ] parser_source 在三条路径上严格保真
- [ ] timeout/invalid JSON/empty 都不会污染 source
- [ ] E2E 中能真实分辨当前命中链
- [ ] 日志、graph、runtime 观测一致

---

## 当前层级与主链状态

```yaml
current_layer: implementation  # 目标/策略/表示/实现/验证/收口
main_chain_status: planning    # 想法/构件/接入/启用/生效/观察
enabled_status: false
trigger_evidence: none
```

---

## 已知与未知

### 确定项
- [ ] 已确认 1
- [ ] 已确认 2

### 关键未知（可能推翻方案）
- [ ] 待验证 1
- [ ] 待验证 2

---

## 路由信息

<!-- 根据 04_CHANGE_ROUTING.md 填写 -->

| 项目 | 内容 |
|------|------|
| 能力归属 | EgoCore / OpenEmotion |
| 第一落点 | `app/runtime_v2/semantic_parser.py` |
| 权威源 | `semantic_parse_message()` |
| 耦合模块 | `telegram_bridge.py`, `safe_semantic_parse()` |
| 是否涉及双核接口 | 否 |
| 失败兜底 | heuristic_parse |

---

## 阶段规划

### Stage 1: 规划（10分钟）

#### 入口检查
- [ ] 已读 `00_MASTER_INDEX.md`
- [ ] 已读 `03_BOUNDARY_AND_OWNERSHIP.md`（如涉及边界）
- [ ] 已读 `04_CHANGE_ROUTING.md`
- [ ] 六问门禁已回答

#### 六问门禁
| 问题 | 答案 |
|------|------|
| 这个能力归 EgoCore 还是 OpenEmotion？ | |
| 它的权威源是谁？ | |
| 它和哪个现有模块耦合？ | |
| 是否引入双重真相源？ | |
| 是否让 shim 变成长期黑箱？ | |
| 失败由谁兜底？ | |

#### 方案草稿
```
主方案：
备选方案：
回退策略：
```

---

### Stage 2: 实现（主要耗时）

#### 修改文件清单
| 文件路径 | 修改类型 | 影响范围 | 风险 |
|----------|----------|----------|------|
| | | | |

#### 关键实现点
```python
# 伪代码或关键逻辑
```

#### 过程中发现的问题
```
问题 1：
解决方案：
```

---

### Stage 3: 验证（必须）

#### 验证层级
- [ ] Gate A: Contract 正确
- [ ] Gate B: E2E 主链可触发
- [ ] Gate C: Preflight / tool / runtime / replay 校验通过

#### 测试覆盖
| 测试类型 | 测试文件 | 结果 |
|----------|----------|------|
| 单元测试 | | |
| 集成测试 | | |
| E2E 验证 | | |

#### 真实触发证据
```
日志片段：
截图/输出：
```

---

## 完成声明

```yaml
completed_at: ""
verified_by: "self"  # self/peer/e2e
main_chain_status: enabled  # 接入/启用/生效
enabled_status: true
trigger_evidence: "日志/Telegram E2E"
commit_hash: ""
solution_grade: formal  # formal/transitional/temporary/assumption
next_action: observe  # 观察期
```

---

## 交接区

<!-- 如需接力，填写此区域 -->

### HANDOFF
```yaml
from: "规划者"
to: "实现者"  # 或验收者
status: READY_FOR_IMPLEMENTATION  # READY_FOR_VERIFY/READY_FOR_FIX
blocked_by: []
estimated_effort: 2h
notes: |
  关键上下文：
  1.
  2.
```

---

## 归档信息

```yaml
archived_at: ""
archive_reason: completed  # completed/cancelled/merged
lessons_learned: |
  1.
  2.
```
