# Shared Field v0.4 — 实际离线比较

8 个初始世界 × 5 个方法；每次至多 80 步。第21个循环隐藏工具故障，第41个循环隐藏路况变化；未通知候选。

评价：新发现的信息收益 − 0.05×动作数 − 0.20×失败动作数。只是本环境的人工效用，不是意识、情感真实性或智能分数。
初始种子配对；不同动作会消耗不同随机序列，因此不声称逐步噪声完全匹配。

| 方法 | 平均发现数 | 平均步数 | 平均失败 | 平均效用 |
|---|---:|---:|---:|---:|
| full | 11.25 | 69.88 | 23.25 | -1.043 |
| affect_off | 11.88 | 62.50 | 22.62 | -0.315 |
| self_off | 9.62 | 74.00 | 32.12 | -3.950 |
| learning_frozen | 4.38 | 80.00 | 44.12 | -9.949 |
| flat_baseline | 11.75 | 62.00 | 21.50 | -0.082 |

完整候选减平坦基线，平均效用差：-0.9603。不能因正/负单项指标就升级或否定所有机制。
同历史决策干预只检查数值状态是否参与选择，不证明该状态有主观感受，也不证明设计优于更简单替代。

缺失强基线：history-conditioned recurrent meta-learner；long-context LLM with matched observations and action budget；learned social world model；oracle with hidden dynamics access (upper reference, not a fair agent)。

**结论上限：当前机制优越性 NOT_ESTABLISHED。真实语言质量和共同游玩的实际体验需另外测试。**
