# v0.3 当前实现的实际离线实验

标签来自合成生成器，不来自真实模型或人类测试。所有预测器看到同一训练历史；测试集不更新。它不是闭环现实收益评测。

| 方法 | 测试 MSE ↓ | 平均后悔值 ↓ | 选中最优动作比例 ↑ |
|---|---:|---:|---:|
| neural | 0.126171 | 0.307760 | 52.7% |
| similarity | 0.031720 | 0.035502 | 88.3% |
| adaptive | 0.031720 | 0.035502 | 88.3% |
| frozen_prior | 0.124980 | 0.351252 | 46.5% |
| oracle | 0.000000 | 0.000000 | 100.0% |

独立生成种子：4；每种子 160 条训练观测、64 个留出情境。
oracle 使用真实生成函数，仅为有限任务上界。frozen_prior 固定输出 0.5。

## 重放与保留（两项确定性任务，非终身学习证明）

```json
{
  "no_replay": {
    "old_task_mse_before": 0.01710000784401823,
    "old_task_mse_after": 0.2302378004138114,
    "new_task_mse": 0.009170347670973583,
    "new_external_samples": 200,
    "gradient_updates": 200
  },
  "replay": {
    "old_task_mse_before": 0.01710000784401823,
    "old_task_mse_after": 0.018183854848254955,
    "new_task_mse": 0.003276087193212543,
    "new_external_samples": 200,
    "gradient_updates": 400
  },
  "matched_current_only": {
    "old_task_mse_before": 0.01710000784401823,
    "old_task_mse_after": 0.34387102420680654,
    "new_task_mse": 0.0018816944393017395,
    "new_external_samples": 200,
    "gradient_updates": 400
  },
  "task_keyed_lookup": {
    "old_task_mse_after": 0.0,
    "new_task_mse": 0.0,
    "note": "A task-keyed table saturates these two deterministic tasks; no neural necessity shown."
  }
}
```

matched_current_only 与 replay 的真实样本数、总梯度次数相同；它将额外计算全部用于当前任务，而不是旧经历。

## 完整控制器中的历史干预

```json
[
  {
    "preferred_in_training": "compare",
    "chosen_on_identical_candidates": "compare",
    "scores": {
      "compare": 1.0,
      "direct": 0.0
    },
    "counterfactual_history_scope": "same candidate set, different explicitly supplied histories",
    "evidence_kind": "synthetic_main_controller_intervention_not_real_language_quality"
  },
  {
    "preferred_in_training": "direct",
    "chosen_on_identical_candidates": "direct",
    "scores": {
      "compare": 0.0,
      "direct": 1.0
    },
    "counterfactual_history_scope": "same candidate set, different explicitly supplied histories",
    "evidence_kind": "synthetic_main_controller_intervention_not_real_language_quality"
  }
]
```

两个历史都经过真实 AdaptiveCore.message/analyse/express/outcome 入口；语言候选和回复是明确标注的夹具。
参数变化、候选变化与任务成功是不同结论。即使出现正向差异，也不证明社交理解、主体性、开放价值形成或现实净收益。

简单预测器若胜出，默认混合控制器可选择它；不通过重写测试指标保证神经方案获胜。
没有对长上下文语言模型和跨 episode 元学习器完成公平比较；当前架构相对普通 LLM 的净收益为 unknown。