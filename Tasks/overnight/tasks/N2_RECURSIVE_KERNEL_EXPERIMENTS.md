# N2 — 递归核有效性实验包 v1

## 任务类型
实验设计 + 实验实现 + 验收脚本

## 目标
把“递归核是否有效”从聊天直觉变成可复现、可反驳、可比较的实验集合。

## 当前层级
理论可行性验证层

## 当前确定项
- 设计稿已经明确了成功标准
- 接口草案已经给出主循环、输入输出与测试骨架
- 当前最小 Telegram 闭环已证明 cycle strengthen 与 failure reflection 确实进入正式状态链

## 关键未知
- 这些现象是否可重复
- appraisal 是否真的对倾向有因果作用
- reflection 是否真的改变下一轮结构化更新
- cycle 聚合是否只是样本碰巧打中

## 主实验要求
至少完成以下 6 组实验中的适用项，形成统一实验报告：

1. 身份连续性
   - 无高价值冲突证据时 identity 不乱跳
2. 经历可塑性
   - 不同事件序列导致不同 self_model / policy_hint / tendency
3. appraisal 因果作用
   - drive_field 变化必须影响 response_tendency
4. cycle 可重入
   - 相似事件重复后命中同一 cycle 并 strengthen
5. reflection 有效
   - failure 后产生 reflection，并改变 revision / 下一轮更新
6. 边界无越权
   - 内核只输出 policy_hint / tendency，不直接输出执行命令

## 成功判据
1. 有可重复运行的实验脚本或测试集合
2. 每组实验都有：
   - 输入
   - 观测字段
   - 预期
   - 实际结果
   - 结论
3. 至少一份统一实验摘要
4. 更新 `reports/N2_REPORT.md`
5. 更新 `runtime/RUN_STATE.json`

## 硬约束
- 不要把实验代码直接混成生产主链
- 不要靠人工解释替代结构化结论
- 不要用被安全层污染的无效样本
- 不要宣称“意识已证明”
- 不要把“看起来像”当成通过标准

## 允许修改
- 实验脚本
- 测试用例
- trace 比对脚本
- 只读诊断工具
- 必要的最小宿主适配以支撑实验

## 禁止修改
- 大规模重写主链
- 重定义 EgoCore / OpenEmotion 边界
- 为了让实验通过而绕过治理壳

## 必交付物
- 实验脚本或测试集
- 实验说明
- 统一实验报告
- `reports/N2_REPORT.md`
- `runtime/RUN_STATE.json` 更新

## 必须记录的证据
- 每组实验的原始输出或 artifact 路径
- 关键 trace 字段
- 明确失败样本
- 若只做到本地实验，必须标记 `implemented_but_pending_real_validation`

## 建议子目录
- `artifacts/experiments/`
- `artifacts/experiments/reports/`
- `scripts/` 或 `tests/` 下的实验入口

## 失败出口
若实验发现递归核当前不能支撑某个成功判据：
- 不要硬修成漂亮结果
- 直接记录反例与失败条件
- 允许 N2 以 `partial` 收口，但必须留下清楚的反证
