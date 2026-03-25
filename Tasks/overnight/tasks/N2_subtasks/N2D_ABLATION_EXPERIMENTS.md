# N2D — Ablation 与对比实验

## 目标
验证递归核中的关键组件是否真的带来差异，而不是“无论开不开都一样”。

## 建议方向
- 去掉 reflection 回流
- 固定某些 drive / appraisal 维度
- 关闭 external_result 影响
- 对比有 / 无 cycle strengthen 的差异

## 成功判据
- 至少完成一组有无对比
- 明确列出差异或无差异
- 若无明显差异，不得强行解释成“有效”

## 失败出口
若当前系统条件不足以做安全 ablation：
- 允许报 `partial`
- 但必须说明为什么不能做、还缺什么
