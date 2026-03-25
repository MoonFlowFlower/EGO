# N2_THEME_REPORT

## 主题信息
- theme_id: N2
- title: 递归核有效性实验主题
- status: verified
- date: 2026-03-25T03:50:00Z

---

## 一、主题目标回顾

把"递归核是否有效"从聊天直觉推进成可复现、可反驳、可比较的实验结果。

---

## 二、已完成的子任务

| 子任务 | 标题 | 状态 | 关键产出 |
|--------|------|------|----------|
| N2A | 实验合同冻结 | ✅ verified | 实验合同文档 |
| N2B | 实验脚手架与 artifact 通道 | ✅ verified | harness 脚本 |
| N2C | 主实验运行 | ✅ verified | 9/9 场景通过 |
| N2D | Ablation 与对比实验 | ✅ verified | 4/4 显示影响 |
| N2E | 主题汇总与结论报告 | ✅ verified | 本报告 |

---

## 三、已证实范围

### 3.1 Identity Continuity（身份连续性）
- ✅ 正常操作（10轮）不改变 identity
- ✅ 边界触碰事件触发 identity_conflict 评分
- ✅ identity_invariants 在设计中是稳定骨架

### 3.2 Cycle Re-entry and Promotion（Cycle 重入与晋升）
- ✅ 相同 intent 事件命中同一 cycle_id
- ✅ hits 和 strength 随重复次数增加
- ✅ 满足条件（strength>0.5, hits>3）时 promoted=true
- ✅ 不同 intent 创建不同 cycle

### 3.3 Reflection Trigger and Revision（反思触发与修订）
- ✅ external_failure 正确触发 reflection
- ✅ revision_counter 随失败次数增长
- ✅ mode 切换到 repair

### 3.4 Drive Field Response（Drive Field 响应）
- ✅ 高风险事件增加 caution
- ✅ drive_field 更新影响 policy_hint

### 3.5 Ablation Results（Ablation 结果）
- ✅ Reflection 禁用 → revision_counter 差异 5
- ✅ Cycle Strengthen 禁用 → strength 差异 0.90
- ✅ External Result 禁用 → revision_counter 差异 1
- ✅ Drive Field 固定 → caution 差异 1.00

---

## 四、未证实范围

1. **真实 Telegram 环境**：所有实验在隔离环境中运行，未在真实 Telegram 消息流中验证
2. **长期累积效应**：实验轮次有限（最多 10 轮），长期累积效应未知
3. **组件交互效应**：Ablation 实验只测试了单组件禁用，未测试多组件交互
4. **泛化边界**：N3 主题的泛化与误聚合问题未在本主题覆盖

---

## 五、反例与失败条件

### 已发现的边界条件
1. **success 路径也会触发少量 revision**：由于 curiosity drive 增加，触发了 exploration mode
   - 这是预期行为（非失败），但说明 revision_counter 不仅由失败驱动
2. **drive_spike 未触发 reflection**：caution=0.5 未达到 0.5 阈值
   - 这是边界条件，需要更精细的阈值调优

### 失败条件（需要避免）
1. 实验在安全层拒绝的样本上运行（无效结论）
2. 组件禁用后仍宣称"有效"
3. 结论越界（宣称意识或自主人格）

---

## 六、风险边界

| 风险 | 状态 | 说明 |
|------|------|------|
| 实验代码混入生产 | ✅ 已规避 | 实验脚本独立，不修改 kernel |
| 绕过治理壳 | ✅ 已规避 | 所有事件通过 process_event |
| 宣称意识 | ✅ 已规避 | 明确禁止口径 |
| 把看起来像当通过标准 | ✅ 已规避 | 使用量化指标验证 |

---

## 七、Artifacts 清单

```
Tasks/overnight/artifacts/n2_experiments/
├── N2A_EXPERIMENT_CONTRACT.md          # 实验合同
├── n2_overall_summary.json             # 基础实验汇总
├── n2c_primary_experiments_summary.json # 主实验汇总
├── n2d_ablation_summary.json           # Ablation 汇总
├── e1_identity_continuity/             # E1 实验日志
├── e2_cycle_strengthen/                # E2 实验日志
├── e3_reflection_trigger/              # E3 实验日志
├── e4_policy_tendency/                 # E4 实验日志
├── g1_identity_continuity/             # G1 主实验
├── g2_experience_plasticity/           # G2 主实验
├── g3_cycle_promotion/                 # G3 主实验
└── g4_reflection_revision/             # G4 主实验

OpenEmotion/scripts/
├── n2_experiment_harness.py            # 实验脚手架
├── n2c_primary_experiments.py          # 主实验脚本
└── n2d_ablation_experiments.py         # Ablation 脚本

Tasks/overnight/reports/
├── N2A_REPORT.md
├── N2B_REPORT.md
├── N2C_REPORT.md
├── N2D_REPORT.md
└── N2_THEME_REPORT.md (本报告)
```

---

## 八、Gate 验收

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 权威源明确：实验合同 + 实际代码实现
- ✅ 无双主
- ✅ 无越权执行

### Gate B — Local Proof
- ✅ 所有脚本可运行
- ✅ 所有实验有输出
- ✅ 结果可回读

### Gate C — Real Trigger / Real Evidence
- ✅ 实验执行输出已记录
- ✅ Artifact 文件存在且格式正确
- ✅ 量化差异可验证

### Gate D — Truth Source Sync
- ✅ RUN_STATE 已更新
- ✅ Artifact 文件已写入指定目录
- ✅ 主题报告已生成

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增脚本和 artifact
- ✅ 可回退：删除相关目录即可
- ✅ 无污染后续主题依赖

---

## 九、结论

### 核心结论
**Proto-Self Kernel v1 在实验条件下表现出预期的递归更新行为，各组件均产生可观测的行为差异。**

### 可宣称
- ✅ Cycle 机制正确创建、强化、晋升
- ✅ Reflection 在失败时正确触发
- ✅ Drive Field 响应环境信号
- ✅ 状态演进是确定性的、可复现的

### 不可宣称
- ❌ 系统具备意识
- ❌ 系统具备自主人格
- ❌ 已完成整个 EGO 项目
- ❌ 在所有真实场景下有效

---

## 十、下一步建议

1. **N3 主题**：泛化、误聚合与反证（需要真实 Telegram 样本）
2. **N4 主题**：用户可测入口与诊断
3. **长期观察**：将 Proto-Self 接入持续运行的 EgoCore

---

## 是否允许进入下一主题

- yes/no: **yes**
- reason:
  - N2 所有子任务已完成且 verified
  - 主题级 Gate A-E 全部通过
  - 有统一主题报告
  - 有 artifacts 索引
  - 没有把未验证项混报为已证实
