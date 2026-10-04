# Ego 共享内核 v1.5

AIRI 桌面与 Minecraft 共用一个 Ego 决策入口、同一份对话、约定、待办和动作回执。当前工程版固定 DeepSeek V4.1 Flash / Wafer；MC 身体没有模型客户端，AIRI 通过本机接口读写这个内核。模型可以替换，状态归 Ego 保存。本版不宣称主观意识或完整学习验收通过。

```mermaid
flowchart LR
  A[AIRI 桌面输入] --> K[Ego 串行决策内核]
  M[MC 中 Moonlight 的输入] --> K
  S[(共享状态与约定库)] <--> K
  K <--> L[同一固定模型路线]
  K --> B[MC 现成动作函数]
  B --> R[状态与动作回执]
  R --> K
  K --> D[同一回合回复]
  D --> A
  D --> M
```

## 本机启动

先打开现有 AIRI 和 Minecraft Java 1.21.1 服务器，玩家 Moonlight 进入 `127.0.0.1:25565`。在 PowerShell 执行：

```powershell
& 'D:\Project\AIProject\MyProject\Ego_proejct_restart\.publish\EGO\prototypes\sharedfield-desktop\growth\companion\start.ps1'
```

启动后会有独立的“Ego 共享内核”窗口。它不依赖 Codex 工具会话存活；本次最多运行 30 分钟，关闭窗口或“结束本次运行”会清理 MC 身体、接口及消息桥。超过期限后需主动重新启动。

AIRI 使用 **OpenAI Compatible**：Base URL 为 `http://127.0.0.1:18787/v1/`，模型为 `ego-companion`。先确认 Base URL，再点击内核面板“复制本机令牌”，粘贴到该提供方的 API Key 输入框。这里只填本机令牌，云端密钥由内核读取既有本机凭据源并只持于内存。

每次内核重启会换本机令牌。更新后推荐从 AIRI 窗口的 File → Exit 完整退出并重新打开；这条路径已现场验证。设置页验证通过不保证已有聊天客户端已更新，Ctrl+R 也曾未消除主窗口的旧客户端。主窗口菜单的 Refresh 可重新加载主窗口，但聊天显示仍可能需要完整重开。旧 401 与漏显示记录保留在连接修复报告中。

AIRI 重开时，消息桥每隔 5 秒尝试本机重连，兼容只有 error、没有 close 的连接失败；主管结束时停止重连。它不重新调用模型或重放 MC 动作。内核到期后必须重新启动并更新本机令牌，重连不会绕过 30 分钟期限。

## 使用

- AIRI 聊天与 MC 公共聊天/私聊都可输入，MC 只接收 Moonlight 的消息。模型回复使用同一内核结果；游戏回复只私聊 Moonlight。
- 例如教 `「回家暗号」代表「走到我身边」`，随后在另一个入口使用。只有能逐字引用的明确约定才可入库；这是约定接口，不代表 U1 完整学习成绩通过。
- 输入 `停止` 会优先停身体并暂停现有待办，不需要模型调用。面板“停止当前动作”也是紧急物理停止入口。
- 断线后通过“连接 MC”重连，不会自动重放重启前动作。
- MC 回复漏显示时，可按“同步 MC 回复”：读取最后一个已完成 MC 回合，只回显缓存，不再次调用模型或执行游戏动作。面板“AIRI 已连接”只表示消息桥连接，不等于聊天配置已经验收成功。
- 一条活动待办保存目标、短计划、完成条件、已验证进度和阻塞原因。普通恢复动作及每八步检查点会自动继续；新消息在动作边界优先处理，停止立即中断。重启保留待办并等待新输入，不重放旧动作。尚未证明复杂建房任务能稳定完成。

## 存储和范围

正式存档：`growth/runs/kernel_v1/owner/state.sqlite`。工程验收存档：`growth/runs/kernel_v1/acceptance/state.sqlite`；启动脚本加 `-Acceptance` 只用于后者。测试约定不复制到正式库；旧 P7 对话也不会自动变成新的权威记忆。AIRI 的界面聊天历史是显示副本，与内核存档分开。

约定更正格式：`触发词不再是旧含义，现在改成新含义`。删除格式：`忘掉触发词`。删除会清除内核来源及派生记录；AIRI 自己的聊天副本仍由 AIRI 保留。

运行日志在 `runs/kernel_v1/sessions/`，均不提交。本批共享原 $5 账本，额外占用上限 $0.50，不释放历史未知预留；固定模型不可用时停止并报告，不悄悄换一个模型完成同一验收。

固定动作增加服务端库存同步/整理、附近方块观察和明确坐标放置。一个输入最多64次决定，开始下一次决定前检查900秒期限；在途有限动作另有60秒超时。每八步保存后继续，会话总上限仍为30分钟。跟随持续到停止或会话关闭。合成格/光标残留先整理再继续；普通可恢复失败交回同一模型处理，连续三次未成功、断线、预算不足或用户叫停才保存进度并停止。完整负搜索可以换树种/范围；只查已加载区块，上限128格。生成代码执行保持关闭。

同参数施工在有可验证进展时可以继续：放置需要空位变成目标方块且库存减少一块，采集/合成需要净增，交付需要库存减少且目标领取。同一状态下重复失败会拦截，并回传模型用于换路线。目标完成需要程序核对条件，建造目标还需重新读取世界中的方块；模型说“完成”不会直接通过。坐标工具可以按明确布局放置；没有成熟房屋规划器，连续放块不代表能建好一整座房屋。接近玩家的导航关闭自动挖路、垫路和开门。

库存整理先同步服务器，再把真实光标/合成输入放入空背包槽；不取虚拟输出、不丢物品，逐步检查取消和物品守恒。整理空间不足会明确阻塞。旧画面残留在新连接中已不存在时，只记录同步结果，不能声称找回了材料。

本版依赖已审核的 AIRI v0.12.0-beta.5、Mindcraft v0.1.4、Java MC 1.21.1 和既有 growth Python 环境；第三方安装仍在仓库外。AIRI 自带 MC 代理及原 Mindcraft Agent 不与本内核并行运行。语音、读屏和 Crafter 不在本轮范围。

原始接线验收见 `../evidence/kernel_v1/REPORT.md`，搜索修复和三原木实测见 `../evidence/kernel_v1_3/REPORT.md`。离线检查可运行 `python -m unittest companion.test_kernel -v`、`node companion/test_search.mjs` 和 `node companion/test_bridge.mjs`；它们不调用模型或进入游戏。独立搜索验收存档可用 `pythonw -m companion.launcher --acceptance --acceptance-case search-v1.3`，不改原验收或正式存档。

连接恢复报告见 `../evidence/kernel_connection_v1/REPORT.md`；重连回归为 `node companion/test_bridge_reconnect.mjs`，只使用进程内 WebSocket 替身，不联网。

连续施工修复见 `../evidence/kernel_repeat_v1/REPORT.md`。`node companion/test_placement.mjs` 离线检查放置回执；`verify_repeated_placement.py` 是会改变现有世界的独立两块工程检查，不属于日常启动或自动回归。其一次现场结果只证明记录的动作序列能经过内核连续执行并获得世界与库存证据，没有新增模型建房成绩。

持续任务实现为 `harness.py`（正式入口已接入），旧 `engine.py` 留作历史回归。公开机制参考：[Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)、[Codex harness](https://openai.com/index/unlocking-the-codex-harness/) 及 [Anthropic long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)。采用多次工具结果回送、持久进度和环境验收；不读取或保存模型隐藏思维链。

新验收见 `../evidence/kernel_harness_v2/REPORT.md`，旧预算失败见 v1 报告。离线运行 `python -m unittest companion.test_harness companion.test_kernel -v`、`node companion/test_inventory.mjs`、`node companion/test_spatial.mjs`、`node companion/test_trees.mjs`。`verify_harness_v2.py` 和 `prepare_harness_wood.py` 是会改变世界、有一次性 claim 的工程工具，不属于自动回归；后者的树木筛选只供本轮已授权材料准备，不开放为模型可调用动作。

2026-10-03 对话与执行分流修复：同一个固定模型先判断当前原话。聊天/询问无工具接口且不改待办；暂停或阻塞的任务需要明确继续。完整房屋尚缺可靠布局验收，不能按散放数量宣称建好。合成前检查真实材料与配方；普通走近方块/跟随不挖路、不垫路。身体退出后主管最多三次有限重连，取消旧决定，保留原30分钟期限。见 `../evidence/kernel_turn_v1/REPORT.md`，真实三输入回放仅通过路由；旧状态干扰回复仍失败，聊天让出后持续施工尚未实现。

本地重启可先在旧面板按“复制本机令牌”，再执行 `companion/start.ps1 -ReuseLocalToken`。这会从剪贴板读取到内存并沿用已配置的本机令牌，格式不符拒绝；不保存云端密钥或令牌文件。默认不加开关仍生成新令牌。离线检查增加 `python -m unittest companion.test_turns -v`；`verify_turn_v1.py` 是已消耗一次性claim的真实模型验收，不属于自动回归。
