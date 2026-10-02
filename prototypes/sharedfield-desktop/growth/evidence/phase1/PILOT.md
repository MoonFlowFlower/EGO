# 阶段 1 描述性预实验

**不是 E1。不做显著性检验，不据此判断学会、有效或 B 优于 A。** 数字用于后续样本量和指标设计。

完成 1/78 局（18 练习、60 测试）；已留存 1 次有汇总的尝试。停止状态：`运行中`。

冻结设置见 [PILOT_MANIFEST.json](PILOT_MANIFEST.json)。逐局摘要、费用、所有配对差值和并发事件见 [pilot_summary.json](pilot_summary.json)。原始允许观察、执行前依据、逐动作预测、事件和模型输出在本机 `runs/phase1/pilot/episodes/`。测试种子未用于调试；提示词 v2 在开跑前冻结，测试间不传经历。

以下均值 ± 样本标准差（n−1）。未做出木镐的正常结束回合统一以步数上限截断，包括提前死亡；表中注明截断数。基础设施/协议中止的尝试单列，不伪装成正常完成样本。云决定不含回合末整理，费用和总调用包含整理；总墙钟由 job 文件写入到 summary 文件写入的时间差计量，包含启动、加载和整理。

| 组 | n | 做出木镐 | 截断 | 失败尝试 | 达成步数（截断） | 云决定 | 费用 USD | 墙钟秒 |
|---|---:|---:|---:|---|---|---|---|---|
| B_F1_auto_practice | 0 | 未运行/未完成 | — | — | — | — | — | — |
| B_F1_teach_practice | 1 | 1 | 0 | 0.00 (SD 未定义) | 133.00 (SD 未定义) | 133.00 (SD 未定义) | 0.010511 (SD 未定义) | 801.39 (SD 未定义) |
| B_F2_train_practice | 0 | 未运行/未完成 | — | — | — | — | — | — |
| B_F1_auto_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| B_F1_teach_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| B_F1_fresh_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| B_F2_train_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| B_F2_fresh_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F1_auto_practice | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F1_teach_practice | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F2_train_practice | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F1_auto_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F1_teach_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F1_fresh_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F2_train_test | 0 | 未运行/未完成 | — | — | — | — | — | — |
| A_F2_fresh_test | 0 | 未运行/未完成 | — | — | — | — | — | — |

配对差值方向均为左组减右组；只使用双方都正常完成的相同种子。完整逐种子及全部指标见 JSON。

| 左组 − 右组 | 配对 n | 失败尝试差 | 截断达成步数差 | 云决定差 |
|---|---:|---|---|---|
| B_F1_auto_test − B_F1_fresh_test | 0 | — | — | — |
| B_F1_teach_test − B_F1_fresh_test | 0 | — | — | — |
| B_F1_teach_test − B_F1_auto_test | 0 | — | — | — |
| B_F2_train_test − B_F2_fresh_test | 0 | — | — | — |
| A_F1_auto_test − A_F1_fresh_test | 0 | — | — | — |
| A_F1_teach_test − A_F1_fresh_test | 0 | — | — | — |
| A_F1_teach_test − A_F1_auto_test | 0 | — | — | — |
| A_F2_train_test − A_F2_fresh_test | 0 | — | — | — |
| B_F1_auto_test − A_F1_auto_test | 0 | — | — | — |
| B_F1_teach_test − A_F1_teach_test | 0 | — | — | — |
| B_F1_fresh_test − A_F1_fresh_test | 0 | — | — | — |
| B_F2_train_test − A_F2_train_test | 0 | — | — | — |
| B_F2_fresh_test − A_F2_fresh_test | 0 | — | — | — |

B 的预测准确率按卡片预测逐条计分，覆盖率按有至少一条适用卡的制作/放置/do 动作计分；do 包含采集和实体互动，不借内部真值挑出成功采集。无预测时准确率未定义。以下同时给出分子/分母。

| 组 | 正确预测 / 全预测 | 覆盖动作 / 可计动作 | 回合准确率均值 ± SD | 回合覆盖率均值 ± SD |
|---|---|---|---|---|
| B_F1_teach_practice | 0 / 0 | 0 / 48 | — | 0.000 (SD 未定义) |

练习结束的全文与出现时间：

| 组 / 回合 | 规则 / 技能 / 反思 | 符合工作台卡形式的编号 | 全文 |
|---|---|---|---|
| B_F1_teach / 1 | 2 / 0 / 0 | 9c032cffe1954e44920fe5e7141e81c3 | [JSON](pilot_memory\B_F1_teach_practice_0.json) |

“符合工作台卡形式”只检查动作 make_wood_pickaxe、前提含 nearby table、预期 wood_pickaxe +1。它不证明必要性、完整性或学会；支持/反例仍以程序记录为准。教学是否送达见每局 teaching 记录；模型是否提出卡、程序是否拒收、重启后是否检索，分别可在 sleep_result、全文存储、input 中核对。没有提案只说明本轮未形成该持久记录，不能反推内部是否学到。

费用与资源（含失败尝试；阶段 1 账本还含工程调试）：

```json
{
  "charges": [
    {
      "status": "reported",
      "requests": 377,
      "usd": 0.031582703721
    },
    {
      "status": "reserved_unknown",
      "requests": 3,
      "usd": 0.15000000000000002
    }
  ],
  "latency_s": {
    "n": 134,
    "median": 5.71871149999788,
    "max": 17.4241253999935
  },
  "thermal": {
    "samples": 34,
    "all_ac": true,
    "gpu_min_C_MHz_MiB_W": [
      61.0,
      600.0,
      2887.0,
      26.72
    ],
    "gpu_max_C_MHz_MiB_W": [
      87.0,
      2595.0,
      3832.0,
      119.73
    ]
  },
  "elapsed_seconds": null
}
```

失败、偏离与未验证：

- HTTP/协议失败、重试与并发调整保留在原始尝试和 status.events；任何未结束而被取消的在途请求仍保留费用预留。
- 不跑 D8 无关经历组；这是本轮已允许的范围。没有接观察台自由演示，不混入实验数据。
- 记忆采用 UTF-8 字节保守上界，没有伪称已运行该模型原生 tokenizer；两组上界相同。
- GPU 为整机采样，不能归因于云模型；CPU 温度、跨机器复现、操作系统级通用代码沙箱未验证。
- 不产生 E1 判决，不因本批数据修改已冻结提示词。
