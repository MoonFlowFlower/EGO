# 阶段 1 描述性预实验

**不是 E1。不做显著性检验，不据此判断学会、有效或 B 优于 A。** 数字用于后续样本量和指标设计。

正常结束 3/78 局（计划 18 练习、60 测试）；留存 8 次尝试，其中 6 份 worker 汇总、2 份取消后的完整已写日志前缀。停止状态：`http_502`。

冻结设置见 [PILOT_MANIFEST.json](PILOT_MANIFEST.json)。逐局摘要、费用、所有配对差值和并发事件见 [pilot_summary.json](pilot_summary.json)。原始允许观察、执行前依据、逐动作预测、事件和模型输出在本机 `runs/phase1/pilot/episodes/`。测试种子未用于调试；提示词 v2 在开跑前冻结，测试间不传经历。

以下均值 ± 样本标准差（n−1）。未做出木镐的正常结束回合统一以步数上限截断，包括提前死亡；表中注明截断数。基础设施/协议中止的尝试单列，不伪装成正常完成样本。云决定不含回合末整理，费用和总调用包含整理；总墙钟由 job 文件写入到 summary 文件写入的时间差计量，包含启动、加载和整理。

| 组 | n | 做出木镐 | 截断 | 失败尝试 | 达成步数（截断） | 云决定 | 费用 USD | 墙钟秒 |
|---|---:|---:|---:|---|---|---|---|---|
| B_F1_auto_practice | 1 | 0 | 1 | 0.00 (SD 未定义) | 300.00 (SD 未定义) | 156.00 (SD 未定义) | 0.013550 (SD 未定义) | 791.65 (SD 未定义) |
| B_F1_teach_practice | 1 | 1 | 0 | 0.00 (SD 未定义) | 133.00 (SD 未定义) | 133.00 (SD 未定义) | 0.010511 (SD 未定义) | 801.39 (SD 未定义) |
| B_F2_train_practice | 1 | 0 | 1 | 0.00 (SD 未定义) | 300.00 (SD 未定义) | 101.00 (SD 未定义) | 0.011423 (SD 未定义) | 622.58 (SD 未定义) |
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

基础设施中止及取消的尝试（以下均不计入上表均值、截断数和配对样本）：

| 尝试 | 停止 | 已观察步数 | 已返回决定 | 已返回总调用 | 失败尝试 | 回执 USD | 墙钟秒 | 正确预测 / 全预测 | 覆盖 / 可计动作 | 最后日志 |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| B_F1_auto_practice_0_a1 | http_502 | 194 | 194 | 194 | 0 | 0.015802556271 | 1142.778 | 0 / 0 | 0 / 17 | stop |
| B_F1_auto_practice_1_a1 | cancelled_for_batch_stop | 92 | 92 | 92 | 0 | 0.010800191352 | 543.446 | 0 / 0 | 0 / 31 | input |
| B_F1_teach_practice_1_a1 | cancelled_for_batch_stop | 94 | 94 | 94 | 0 | 0.011243795055 | 544.167 | 0 / 0 | 0 / 35 | progress |
| B_F2_train_practice_1_a1 | http_502 | 72 | 72 | 72 | 0 | 0.006849890601 | 374.699 | 41 / 41 | 41 / 52 | stop |
| B_F2_train_practice_1_a2 | http_502 | 29 | 29 | 29 | 0 | 0.002310641487 | 136.465 | 10 / 10 | 10 / 10 | stop |

B_F1_auto_practice_1_a1 最后已记录 tick=92 的下一次输入，没有对应回执；B_F1_teach_practice_1_a1 最后记录 tick=94 的 progress。两者没有 summary 或睡眠整理，回合结果未定，不补算为失败完成。F2 第二练习的两次尝试分别在 tick=72、29 后的请求返回 502；自动重试一次后触发整批停止。

事件计数（零值显式列出；包含中断尝试）：

| 尝试 | 无可见效果 | 被挡住 | 掉血 |
|---|---:|---:|---:|
| B_F1_auto_practice_0_a1 | 61 | 46 | 2 |
| B_F1_auto_practice_0_a2 | 88 | 7 | 5 |
| B_F1_auto_practice_1_a1 | 60 | 35 | 0 |
| B_F1_teach_practice_0_a1 | 47 | 6 | 0 |
| B_F1_teach_practice_1_a1 | 56 | 29 | 2 |
| B_F2_train_practice_0_a1 | 51 | 21 | 5 |
| B_F2_train_practice_1_a1 | 45 | 3 | 0 |
| B_F2_train_practice_1_a2 | 11 | 2 | 0 |

B 的预测准确率按卡片预测逐条计分，覆盖率按有至少一条适用卡的制作/放置/do 动作计分；do 包含采集和实体互动，不借内部真值挑出成功采集。无预测时准确率未定义。以下同时给出分子/分母。

| 组 | 正确预测 / 全预测 | 覆盖动作 / 可计动作 | 回合准确率均值 ± SD | 回合覆盖率均值 ± SD |
|---|---|---|---|---|
| B_F1_auto_practice | 0 / 0 | 0 / 95 | — | 0.000 (SD 未定义) |
| B_F1_teach_practice | 0 / 0 | 0 / 48 | — | 0.000 (SD 未定义) |
| B_F2_train_practice | 0 / 0 | 0 / 33 | — | 0.000 (SD 未定义) |

练习结束的全文与出现时间：

| 组 / 回合 | 规则 / 技能 / 反思 | 符合工作台卡形式的编号 | 全文 |
|---|---|---|---|
| B_F1_auto / 1 | 0 / 0 / 0 | 无 | [JSON](pilot_memory\B_F1_auto_practice_0.json) |
| B_F1_teach / 1 | 2 / 0 / 0 | 9c032cffe1954e44920fe5e7141e81c3 | [JSON](pilot_memory\B_F1_teach_practice_0.json) |
| B_F2_train / 1 | 6 / 0 / 0 | 无 | [JSON](pilot_memory\B_F2_train_practice_0.json) |

中断处持久记忆（只读导出；不表示完成了本回合整理）：

| 尝试 | 规则 / 技能 / 反思 | 全文 |
|---|---|---|
| B_F1_auto_practice_0_a1 | 0 / 0 / 0 | [JSON](pilot_memory\B_F1_auto_practice_0_a1_interrupted.json) |
| B_F1_auto_practice_1_a1 | 0 / 0 / 0 | [JSON](pilot_memory\B_F1_auto_practice_1_a1_interrupted.json) |
| B_F1_teach_practice_1_a1 | 2 / 0 / 0 | [JSON](pilot_memory\B_F1_teach_practice_1_a1_interrupted.json) |
| B_F2_train_practice_1_a1 | 6 / 0 / 0 | [JSON](pilot_memory\B_F2_train_practice_1_a1_interrupted.json) |
| B_F2_train_practice_1_a2 | 6 / 0 / 0 | [JSON](pilot_memory\B_F2_train_practice_1_a2_interrupted.json) |

“符合工作台卡形式”只检查动作 make_wood_pickaxe、前提含 nearby table、预期 wood_pickaxe +1。它不证明必要性、完整性或学会；支持/反例仍以程序记录为准。教学是否送达见每局 teaching 记录；模型是否提出卡、程序是否拒收、重启后是否检索，分别可在 sleep_result、全文存储、input 中核对。没有提案只说明本轮未形成该持久记录，不能反推内部是否学到。

费用与资源（含失败和取消；本处阶段 1 账本是停止后、G0 调用前的快照，还含工程调试，见 pilot_budget_close.json；后来 G0 的费用另列 G0.md）：

```json
{
  "charges": [
    {
      "status": "reported",
      "requests": 937,
      "usd": 0.088509930822
    },
    {
      "status": "reserved_unknown",
      "requests": 5,
      "usd": 0.25
    }
  ],
  "pilot_reported_receipts": {
    "requests": 874,
    "usd": 0.082491064479
  },
  "latency_s": {
    "n": 874,
    "median": 5.203372449999733,
    "max": 25.012255800000275
  },
  "thermal": {
    "samples": 96,
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
  "concurrency": {
    "initial_cap": 2,
    "final_cap": 4,
    "peak_job_interval_overlap": 3,
    "measurement": "job-file start to summary-file end or cancellation; process launches/exits are not individually timestamped",
    "http_429_events": 0
  },
  "elapsed_seconds": 2510.466907978058
}
```

失败、偏离与未验证：

- HTTP/协议失败、重试与并发调整保留在原始尝试和 status.events；任何未结束而被取消的在途请求仍保留费用预留。
- 不跑 D8 无关经历组；这是本轮已允许的范围。没有接观察台自由演示，不混入实验数据。
- 记忆采用 UTF-8 字节保守上界，没有伪称已运行该模型原生 tokenizer；两组上界相同。
- GPU 为整机采样，不能归因于云模型；CPU 温度、跨机器复现、操作系统级通用代码沙箱未验证。
- 不产生 E1 判决，不因本批数据修改已冻结提示词。
