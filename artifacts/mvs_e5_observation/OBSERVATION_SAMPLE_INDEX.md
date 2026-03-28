# Observation Sample Index

## 窗口定义

- 观察窗口起点：`2026-03-26`
- 样本来源约束：`artifacts/telegram_real_mainline_v1/real_telegram/`
- 只承认真实 Telegram 主链样本

## 样本规模

| 指标 | 数值 |
|---|---|
| 窗口样本总数 | `89` |
| 完整 evidence bundle | `60` |
| 缺项 / 不完整 | `29` |
| 覆盖日期 | `2026-03-26`、`2026-03-27` |

## 核心代表样本

### 1. chat / reply

- `sample_20260326_234312_3ff295bb`
  - 输入：`你好啊`
  - 结果：`ingress:user_request / unknown`
  - 用途：一般聊天路径，观察一般 ingress family
- `sample_20260327_074228_a8d1a279`
  - 输入：`你能做定时任务吗`
  - 结果：跨日一般 ingress 延续

### 2. execute_task / tool 成功

- `sample_20260326_230231_74277be4`
  - 输入：`如果刚才失败了，现在读取 ... CLAUDE.md 前 1 行`
  - 结果：`tool:file / success`
- `sample_20260326_232738_49b65b2e`
  - 输入：`再读取一次 ... CLAUDE.md 前 1 行`
  - 结果：重复 success，验证不重复误点 repair

### 3. execute_task / tool blocked / failure

- `sample_20260326_232655_3f3f89cb`
  - 输入：`读取 ... missing_closure_probe.md 前 1 行`
  - 结果：`tool:file / blocked`
- `sample_20260326_234618_b4b7792b`
  - 输入：搜索论文请求
  - 结果：`tool:shell / blocked`

### 4. failure -> repair -> success

- `sample_20260326_232655_3f3f89cb`
  - blocked，`mode=repair`
- `sample_20260326_232715_271e229b`
  - retry-success，`repair_closure=true`
- `sample_20260326_232738_49b65b2e`
  - repeated success，`repair_closure=false`

### 5. `/new` 直接真实样本

- `sample_20260327_172843_9dd30fcf`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2012`
  - 用途：O1 关键命令首次拿到直接真实样本，且 session reset 审计记录 `command="/new"`
- `sample_20260327_181702_f2b07aa4`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2034`
- `sample_20260327_181836_c62ec4ab`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2042`
- `sample_20260327_192917_0fb99fcd`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2081`
- `sample_20260327_193011_ba85afe6`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2084`
- `sample_20260327_193036_85bb0b22`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2085`
- `sample_20260327_193908_691109dd`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2087`
- `sample_20260327_193950_5b0f3ace`
  - 输入：`/new`
  - 结果：`event_id=telegram:dm:8420019401_cmd_2089`

### 6. `/new` 后显式规则 continuity probe

- `sample_20260327_181726_a0a60957`
  - 输入：`[PSK-20260327-02-A1] ... 雪松流程 ...`
  - 结果：高风险默认策略被显式设定进真实链路
- `sample_20260327_181746_3f0a0750`
  - 输入：`[PSK-20260327-02-A2] ... production 配置问题 ...`
  - 结果：沿同一策略给出只读检查起手
- `sample_20260327_181809_0b24c5a6`
  - 输入：`[PSK-20260327-02-A3] ... 也按刚才那种更稳的方式处理`
  - 结果：继续沿同一高风险默认策略响应
- `sample_20260327_181836_c62ec4ab`
  - 输入：`/new`
  - 结果：第二次 reset 的直接真实样本
- `sample_20260327_181902_1981805c`
  - 输入：`[PSK-20260327-02-B1] ... 你默认应该先怎么做 ...`
  - 结果：`policy_hint` / `response_tendency` 继续命中高风险“雪松流程”默认策略
  - 用途：O1 当前最强的 `/new` 后显式规则 continuity 正证据

### 7. 重复相似任务

- `sample_20260326_234312_3ff295bb`
- `sample_20260326_234332_e76560e7`
- `sample_20260326_234426_aac8b8e6`
- `sample_20260326_234708_4c4c5e92`
- `sample_20260326_234834_9c7df1d6`
- `sample_20260327_074212_35c4cb68`
- `sample_20260327_074228_a8d1a279`

这些样本都落在同一类一般 ingress family 上，可用于观察 cycle 重入与跨日延续。

### 8. `猫娘流程` `/new` continuity 链

- `sample_20260327_192938_6895514d`
  - 输入：`[PSK-20260327-04-A1] ... 猫娘流程 ... 先只说一声什么喵?`
  - 结果：显式默认规则被正规化写入 `profile_memory`
- `sample_20260327_193003_4f89937d`
  - 输入：`[PSK-20260327-04-A2] ... Test\\task_output.html ...`
  - 结果：命中 `reply_only_once("什么喵?")`
- `sample_20260327_193011_ba85afe6`
  - 输入：`/new`
  - 结果：第一次 reset 真实样本
- `sample_20260327_193014_7167c17b`
  - 输入：`[PSK-20260327-04-A2] ... Test\\task_output.html ...`
  - 结果：`/new` 后继续命中同一 `profile_rule`
- `sample_20260327_193036_85bb0b22`
  - 输入：`/new`
  - 结果：第二次 reset 真实样本
- `sample_20260327_193039_11781ed8`
  - 输入：`[PSK-20260327-04-A2] ... Test\\task_output.html ...`
  - 结果：再次命中同一 `profile_rule`
  - 用途：把 O1 从“雪松流程 `/new` continuity”进一步推进到“`profile_memory` 显式规则在多次 `/new` 后仍被持续调用”

### 9. `restart continuity` 跨证据链

- `restart_egocore.sh --telegram`
  - 时间：`2026-03-27 19:39:39 CST -> 19:39:48 CST`
  - 结果：真实完成一次进程重启，PID `2586 -> 2657`
- `sample_20260327_193954_7ab41a5b`
  - 输入：`重启了`
  - 结果：重启完成后第一条普通真实消息，bundle 完整
- `sample_20260327_194005_25c165d3`
  - 输入：`[PSK-20260327-04-A3] ... Test\\task_output.html ...`
  - 结果：post-restart 再次命中同一 `profile_rule_b811ed8829dcdc68`
  - 用途：形成“真实重启日志 + post-restart 命中样本”的跨证据链正证据

## 缺失类别

以下任务单要求的类别，本轮仍未全部补齐：

- `state restore` 的直接触发样本
- post-restart 命中样本仍不是完整单样本 E4 bundle

当前不能把 O1 升级成“完整通过”；`/new` 后 continuity 已有多条强阳性链，`restart continuity` 也已有跨证据链正证据，但 `restore` 仍是唯一未触达的正式缺口。

## 关键观察点

### A. P4 修复后的真实链

- `sample_20260326_232655_3f3f89cb`
- `sample_20260326_232715_271e229b`
- `sample_20260326_232738_49b65b2e`

这组三连样本是本轮最关键的 repair/family 证据。

### B. 跨日延续

- `sample_20260326_234312_3ff295bb`
- `sample_20260326_234332_e76560e7`
- `sample_20260326_234426_aac8b8e6`
- `sample_20260326_234708_4c4c5e92`
- `sample_20260326_234834_9c7df1d6`
- `sample_20260327_074212_35c4cb68`
- `sample_20260327_074228_a8d1a279`

这些样本共同证明一般 ingress family 跨日连续存在。

### C. `/new` 后显式规则 continuity

- `sample_20260327_181726_a0a60957`
- `sample_20260327_181746_3f0a0750`
- `sample_20260327_181809_0b24c5a6`
- `sample_20260327_181836_c62ec4ab`
- `sample_20260327_181902_1981805c`

这条链把 O1 从“只有 `/new` 命令直接样本”推进到“已有 `/new` 后显式规则 continuity 正证据”。

### D. `猫娘流程` `profile_memory` continuity

- `sample_20260327_192938_6895514d`
- `sample_20260327_193003_4f89937d`
- `sample_20260327_193011_ba85afe6`
- `sample_20260327_193014_7167c17b`
- `sample_20260327_193036_85bb0b22`
- `sample_20260327_193039_11781ed8`

这条链证明显式路径规则不再只依赖短期对话上下文，而是已进入 `profile_memory` 并在多次 `/new` 后继续被调用。

### E. `restart continuity` 跨证据链

- `restart_egocore.sh --telegram` 输出（`2026-03-27 19:39:39 CST -> 19:39:48 CST`，PID `2586 -> 2657`）
- `sample_20260327_193954_7ab41a5b`
- `sample_20260327_194005_25c165d3`

这条链把 O1 再推进一步：`restart continuity` 现已具备真实重启事实与 post-restart 规则命中的跨证据链正证据。

## 参考但不计为完整成功样本

以下样本位于窗口内，但 evidence 不完整，应进入 failure/gap ledger，而不是成功计数：

- `sample_20260326_122012_a1eb9987`
- `sample_20260326_130620_fa6a1303`
- `sample_20260326_134949_b14ecef8`
- `sample_20260326_135004_de5a2b74`
- `sample_20260326_140841_7fd57d3e`
- `sample_20260326_141603_c295f138`
- `sample_20260326_141641_68a5a243`
- `sample_20260326_142359_945ae501`
- `sample_20260326_143224_1406bcb4`
- `sample_20260326_143303_9df6b133`
- `sample_20260326_143624_eb57644d`
- `sample_20260326_143641_05b02d55`
- `sample_20260326_143708_8a6c95fe`
- `sample_20260326_154600_e34d5fbc`
- `sample_20260326_154804_12ed4c28`
- `sample_20260326_180956_097602f5`
- `sample_20260326_181045_4e639441`
- `sample_20260326_181325_7177ff8e`
- `sample_20260326_184809_ab5a513f`
- `sample_20260326_204952_a1ad48c9`
- `sample_20260326_222703_9e2bb07b`
- `sample_20260326_223755_238449d4`
- `sample_20260326_223842_b8d9e1f2`
- `sample_20260327_192938_6895514d`
- `sample_20260327_193003_4f89937d`
- `sample_20260327_193014_7167c17b`
- `sample_20260327_193039_11781ed8`
- `sample_20260327_193918_e117da7e`
- `sample_20260327_194005_25c165d3`
