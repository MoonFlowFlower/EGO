# Layer 2: 功能实现模板

> 适用：功能实现、单模块改动、接口调整、测试补充
> 预期耗时：30 分钟 - 4 小时
> 执行方式：`Spec Lite -> Author -> Self-Reviewer -> Independent Reviewer -> Verifier -> Publisher`

---

## 任务头（必须）

```yaml
task_id: L2-{YYYYMMDD}-{序号}
created_at: "2026-03-23T10:00:00Z"
owner: "负责人"
layer: 2
type: functional  # functional/verify/refactor
target_repo: EgoCore  # EgoCore/OpenEmotion/Dual
status: pending  # pending/spec_ready/author_done/review_passed/verify_passed/published
risk_level: medium  # low/medium/high
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

### Stage 1: Spec（10分钟）

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

### Stage 2: Author（主要耗时）

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

### Stage 3: Self-Reviewer（必须，findings-first）

#### 阻断发现
- [ ] 无

#### 固定检查项
- [ ] authority source 未改错
- [ ] 未引入双重真相源
- [ ] 未把 shim/mirror/cache/fallback 偷升成正式主链
- [ ] 不存在“测试能过但主链未接入”的伪完成
- [ ] 已补对应测试、文档、evidence 或明确说明为何暂缺
- [ ] 未把无关日志、state、临时样本、运行噪声带进提交

#### Review 记录
| 发现 | 严重度 | 处理状态 | 备注 |
|------|--------|----------|------|
| | blocker/warn/info | fixed/open | |

#### Review 结论
```
自 review 未发现阻断项 / 已修复以下阻断项：
```

---

### Stage 4: Independent Reviewer（分档启用）

#### 启用档位
- [ ] `L2` 低风险：可选
- [ ] `L2` 中风险：默认建议
- [ ] `L2` 高风险：强制

#### 独立 Reviewer 结论
| 发现 | 严重度 | 处理状态 | 备注 |
|------|--------|----------|------|
| | blocker/warn/info | fixed/open | |

#### 放行条件
- [ ] 若本任务属于建议/强制档位，已完成独立 Reviewer 审计
- [ ] 若未启用，已记录原因

---

### Stage 5: Verifier（必须）

#### 验证层级
- [ ] Gate A: Contract 正确
- [ ] Gate B: E2E 主链可触发
- [ ] Gate C: Preflight / tool / runtime / replay 校验通过

#### 验证门匹配
- [ ] 最低门：`py_compile` / 导入检查 / 脚本语法
- [ ] 最低门：改动相关最小测试集
- [ ] 若为 Telegram 主链：按 `TELEGRAM_TEST_PROCESS.md` 匹配层级测试
- [ ] 若为 Telegram 主链：`EgoCore/tools/run_telegram_mainline_regression.sh`
- [ ] 若触及 contract/runtime：补合同步门
- [ ] 若为真实故障修复：先 replay 复现，再修，再复跑最低回归门

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

### Stage 6: Publisher

#### 发布门槛
- [ ] Spec 已清楚
- [ ] Reviewer 无阻断发现
- [ ] Verifier 已通过对应门
- [ ] 提交范围干净，只包含本轮正式内容

#### 提交拆分计划
| 提交类型 | 是否需要 | 备注 |
|----------|----------|------|
| code/mainline | | |
| docs/observation/index | | |
| evidence bundles | | |

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
status: published
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
