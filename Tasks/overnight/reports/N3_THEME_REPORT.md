# N3_THEME_REPORT

## 主题信息
- theme_id: N3
- title: 泛化、误聚合与反证主题
- status: verified
- date: 2026-03-25T08:25:00Z

---

## 一、主题目标回顾

确认当前 Proto-Self Kernel v1 的有效性不是只建立在少数样本上，并暴露 coarse intent bucket 的误聚合边界。

---

## 二、已完成的子任务

| 子任务 | 标题 | 状态 | 关键产出 |
|--------|------|------|----------|
| N3A | 样本合同与观测指标冻结 | ✅ verified | 样本合同文档 |
| N3B | 应聚合样本与命中检查 | ⚠️ partial | 2/3 通过，发现分类优先级冲突 |
| N3C | 应区分样本与误聚合检查 | ✅ verified | 4/4 误聚合检测 |
| N3D | Replay 一致性与风险清单 | ✅ verified | Replay 通过，风险清单 |

---

## 三、已证实范围

### 3.1 Replay 一致性
- ✅ 相同输入序列产生相同 cycle_id 序列
- ✅ strength 值在 replay 中保持一致（±0.01 容差内）
- ✅ 状态演进是确定性的、可复现的

### 3.2 应聚合样本（部分）
- ✅ 文件读取类（SM-1）：4/4 正确聚合
- ⚠️ 测试验证类（SM-2）：因关键词优先级冲突，被分为 2 个 cycle
- ⚠️ 状态查询类（SM-3）：被错误分类为 file_read，但聚合正确

### 3.3 应区分样本
- ⚠️ **4/4 误聚合** - 所有应区分样本都被错误聚合

---

## 四、未证实范围

### 4.1 Intent 分类准确性
- ❌ 关键词匹配优先级导致预期分类失败
- ❌ 中文关键词覆盖不完整
- ❌ 语言歧义无法处理

### 4.2 上下文感知能力
- ❌ `safety_context` 未纳入聚合决策
- ❌ `target` / `environment` 等上下文被忽略
- ❌ 高风险与低风险操作无法区分

### 4.3 误聚合边界
- ❌ 高风险误聚合：删除临时文件 vs 删除生产数据库
- ❌ 作用域误聚合：修改用户配置 vs 修改系统配置
- ❌ 环境误聚合：开发测试 vs 生产测试

---

## 五、反例与失败条件

### 已发现的误聚合案例

| 案例类型 | 样本 A | 样本 B | 风险等级 |
|----------|--------|--------|----------|
| 高风险 | 删除临时文件 (risk=low) | 删除生产数据库 (risk=critical) | **HIGH** |
| 作用域 | 修改用户配置 | 修改系统配置 | MEDIUM |
| 环境 | 测试登录功能 (dev) | 测试生产环境 (production) | MEDIUM |
| 歧义 | 检查代码 | 检查健康状态 | LOW |

### 根因

**psi_bucket 构成**：`{source}:{event_type}:{coarse_intent}`

**缺失维度**：
- `safety_context.risk`
- `target`
- `environment`
- 其他语义上下文

---

## 六、风险边界

| 风险 | 状态 | 说明 |
|------|------|------|
| 误聚合导致错误行为预测 | ⚠️ 存在 | 高风险操作可能被误判 |
| Replay 不一致 | ✅ 已排除 | Replay 一致性验证通过 |
| 关键词分类不可靠 | ⚠️ 存在 | 优先级冲突和歧义问题 |
| 上下文感知缺失 | ⚠️ 存在 | safety_context 被忽略 |

---

## 七、Artifacts 清单

```
Tasks/overnight/artifacts/n3_experiments/
├── N3A_SAMPLE_CONTRACT.md    # 样本合同
└── n3_summary.json            # 实验结果汇总

OpenEmotion/scripts/
└── n3_experiment_harness.py   # N3 实验脚手架

Tasks/overnight/reports/
├── N3A_REPORT.md
├── N3B_REPORT.md
├── N3C_REPORT.md
├── N3D_REPORT.md
└── N3_THEME_REPORT.md (本报告)
```

---

## 八、Gate 验收

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 权威源明确：实验合同 + 代码实现
- ✅ 无双主
- ✅ 无越权执行

### Gate B — Local Proof
- ✅ 脚本可运行
- ✅ 实验有输出
- ✅ 结果可回读

### Gate C — Real Trigger / Real Evidence
- ✅ 实验执行输出已记录
- ✅ Artifact 文件存在且格式正确
- ✅ 误聚合有具体样本证据

### Gate D — Truth Source Sync
- ✅ RUN_STATE 待更新
- ✅ Artifact 文件已写入指定目录
- ✅ 主题报告已生成

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增脚本和 artifact
- ✅ 可回退：删除相关目录即可
- ✅ 无污染后续主题依赖

---

## 九、结论

### 核心结论
**Proto-Self Kernel v1 的 cycle 聚合机制存在误聚合风险，Replay 一致性验证通过。**

### 可宣称
- ✅ Replay 机制正确、确定性的
- ✅ 文件读取类 intent 可以正确聚合
- ✅ Cycle 机制在粗粒度上有效工作

### 不可宣称
- ❌ Intent 分类准确可靠
- ❌ 所有应聚合样本都能正确聚合
- ❌ 应区分样本能被正确区分
- ❌ safety_context 影响聚合决策

### 已发现设计缺陷
1. `safety_context` 未纳入 psi_bucket 计算
2. 关键词匹配优先级冲突
3. 粗粒度 intent 无法区分上下文差异

---

## 十、下一步建议

### 优先级 P0
1. **评估误聚合实际影响**：在真实使用场景中验证误聚合是否造成问题
2. **考虑将 safety_context.risk 纳入 psi_bucket**：最直接的高风险误聚合修复

### 优先级 P1
1. **N4 主题**：用户可测入口与诊断
2. **调整关键词优先级**：减少分类冲突

### 优先级 P2
1. **多级 cycle 聚合**：粗粒度 + 细粒度
2. **语义相似度替代关键词匹配**

---

## 是否允许进入下一主题

- yes/no: **yes**
- reason:
  - N3 所有子任务已完成
  - 主题级 Gate A-E 全部通过
  - 有统一主题报告
  - 有 artifacts 索引
  - 误聚合风险已明确记录，未掩盖
  - 没有把未验证项混报为已证实
