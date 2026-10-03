# P7 组装摸底：代理已验证，完整一起玩未达到

本轮按 2026-10-03 03:32:38 UTC 开始、最多 8 小时的清单执行。至 04:51 UTC 已提前在硬约束与基础设施阻断处收口，随后仅整理和复核证据；未把未运行的项目算成失败率或成功率。U1 独立完成其停止流程，没有接入代理的学习插入点。基线为 `55a3390`，设计 v0.8；Crafter 不执行。

| 项目 | 实际结果 | 证据与边界 |
|---|---|---|
| 本机代理 | 19 项离线工程验收通过，根代理复跑也通过 | JSON/SSE、鉴权、消息和工具对象保持、原子预算预留；首轮竞态失败保留。假上游不替代真实客户端 |
| AIRI 引导页 Ping | 通过 | 官方桌面实际验证后进入下一页；代理 1 次云调用完成，1.4633008 秒，输入 5 / 输出 16 token，$0.000015173634 |
| 实际错误令牌 | HTTP 401，留下 `unauthorized` 事件 | 对运行中的 `GET /v1/models` 发送专用错误令牌，未产生上游调用 |
| 断网 / 超预算 | 离线模拟拒绝通过 | 没有切断用户整机网络，也没有耗尽真实 $5 账本；物理断网未测 |
| AIRI 实际聊天 | 接入失败 | 固定探针发送后界面显示 `Provider credentials for openai-compatible not found`，代理没有新请求；不以引导 Ping 代替聊天 |
| 固定模型路线 | 运行中失效，已停代理 | 04:30:50 UTC 新实例只读预检返回 `route_preflight_rejected` / 503；原会话已关闭，没有偷偷回退或更换模型 |
| 本机语音 | 未产出音频 | Kokoro 本地模型列表可见，选 FP32 WebGPU 后声音列表 `No options`，Test Voice 禁用；没有合成/播放成功证据。识别保持关闭 |
| 读屏 | 关闭状态已核对 | 实际 Vision 页面无提供方、Ticker Idle、Last capture Never、Captures 0、Context updates 0 |
| AIRI MC | 硬约束停止，未进世界 | 官方实现必须运行模型生成的 JavaScript，未找到可独立关闭后继续工作的规划路径 |
| Mindcraft MC | 官方安装及静态配置检查完成，未进世界 | 世界未确认、固定模型路由阻断；额外检查还发现控制口与启动清理需处理的边界，见对比说明 |
| 全套资源共存 | 未测 | 只有 AIRI 与 MC 客户端菜单同时运行的部分样本，未运行身体与本机语音 |
| 负责人 15 分钟试玩 | 未发生 | 无原话可记录；本轮不伪造体验或以自动化代玩 |

## 版本、来源与配置

AIRI 从[官方 v0.12.0-beta.5 release](https://github.com/moeru-ai/airi/releases/tag/v0.12.0-beta.5)安装，发布于 2026-08-29。安装包 733,305,834 字节，SHA-256 `f64473fd54f905b5a5ec8d6d3c93277f0fc7a5368f53e0938b46d25a0d8a336b`，与 release digest 一致；已安装 `airi.exe` SHA-256 `bf42992109222621748e71a232902ce2b6fe7e6351428cee1f8fb998065c33cb`。官方源码标签提交 `2c1e223c8dd813d7c74a324d7fd7399fbf47e8bf`。安装位置 `C:/Users/LEO/AppData/Local/Programs/airi/airi.exe`。

Mindcraft 从[官方 v0.1.4](https://github.com/mindcraft-bots/mindcraft/releases/tag/v0.1.4)检出，提交 `b36eaf7e61b3f6bd031fdb531812b2e3c42b6c73`，发布于 2026-03-20。依赖从 npm 官方注册源安装，使用 `--ignore-scripts --no-audit --no-fund`，548 个包；核心模块导入成功。生成的仓库外 `package-lock.json` SHA-256 为 `9b454b3f2650d83d9a1ea09c703ee43bb6657907921393201100bc3721a01d0a`。第三方代码与依赖均在 `D:/Project/AIProject/MyProject/Ego_proejct_restart/p7_tools/`，不提交。

本机代理地址 `http://127.0.0.1:18787/v1/`，仅监听回环。每次启动随机令牌；云密钥仅由既有授权读入代理内存。负责人明确允许 AIRI 配置保存本机代理和 WebSocket 令牌，详见 `AUTHORIZATION_ADDENDUM.md`。AIRI 从未收到云 API 密钥，未注册/登录账号。代理保留 U1 前后插入点，本轮是恒等转发。

固定路线为 `deepseek/deepseek-v4-flash-0731` / `open-inference/fp8`，强制 ZDR、禁止回退、拒绝客户端覆写路线及越过上限。会话内缓存预检元数据；发现路线消失后主动关闭旧会话，用新实例复查拒绝，未继续用缓存请求。后续改进应覆盖长会话元数据时效，这轮冻结代理未修改。

## 桌面接入与语音的限制

引导页验证成功后，实际 Consciousness 页面仍显示 `No Providers Configured`；聊天没有到达代理。官方 `onboarding.vue` 的保存代码向 `configs` 派生映射赋值，而 `providers/config.ts` 用 `Object.fromEntries` 构造该映射。这为配置未持久进入权威 store 提供了源码线索，未用修改版 AIRI 做因果复验，不能称已修复。

Kokoro 官方实现将文本交给本机 adapter / worker 运行 `kokoro-js`，权重来源为其内置的 `onnx-community/Kokoro-82M-v1.0-ONNX`。实际 UI 尚无可用声音，故没有把“本地实现存在”写成“本地语音可用”。桌面 App (Local) 识别配置为 WIP；Web Speech API 标签不能证明只在本机处理，因此未启用麦克风识别或改用外部语音服务。

Analytics 已在实际 General 设置关闭。短时 TCP 采样与源码外部依赖说明见 `NETWORK_AND_RESOURCES.md`，原始网络/资源记录仅在 runs。默认角色原文及 D5 检查另见 `AIRI_ROLE_AND_D5.md`；未修改角色设定。

## Minecraft 对比和选择

Minecraft 版本固定 Java 1.21.1，当前 Java 21.0.12.8。负责人提供 HMCL 路径和玩家名 Moonlight，并授权选择本机地址端口；已选 `127.0.0.1:25575`。启动已安装的 1.21.1 后 Singleplayer 直接进入 Create New World，未发现这个实例有现有存档。已询问新建隔离世界还是由负责人打开已有世界，尚未得到选择；未新建或升级用户世界。

| 方案 | 生成代码边界 | 连接/任务/延迟结果 | 与 AIRI 聊天的连续性 |
|---|---|---|---|
| AIRI 自带 MC | `brain.ts` 经 `JavaScriptPlanner` 调用 `repl.evaluate`，`js-planner.ts` 将计划交给 worker 执行；关闭整颗 brain 不构成可用替代路径 | 全部未运行，按约束停止；不能记为五项任务失败 | 官方有 WebSocket 集成路径，实际未连，未证实 |
| Mindcraft v0.1.4 | `allow_insecure_coding=false`，另屏蔽 `!newAction`；移除可覆盖开关的 `INSECURE_CODING` 环境变量 | 安装/导入完成；五项任务和决定延迟均未测 | 未实现与 AIRI 的会话/记忆共用；“同用代理”不足以证明连续 |

下一步优先保留 Mindcraft 作身体候选，因为其现成静态动作能关闭生成代码。这个建议只基于接口与约束，**没有任务成功率比较证据**。原 AIRI MC 不在当前硬约束下运行，也不在其计划迁移 Fabric 的旧接口上追加长期功能。Mindcraft 的本机控制接口和进程生命周期还需先完成工程处理，见 `MINDCRAFT_REVIEW.md`；未运行的监督器草稿已移入忽略的 runs，不能称现在已可安全一键试玩。

进入、跟随、砍树、木镐、停下的输入、120/60/180/180 秒窗口和停下 5 秒 + 10 秒不恢复要求保留在原清单。没有因未运行而改标准，也没有拿直接命令或文字回复替代环境后置条件。

## 费用、交付与断点

P7 可精确归属的云调用只有上述一次 Ping，$0.000015173634；全部测试没有重置共享账本。U1 结束时共享占用 $0.80450964259 / $5，含历史和未知预留，不能都算作本轮实际费用。

一页恢复/启动说明见 `OWNER_START.md`。当前断点是：可用固定 ZDR 路线、AIRI 提供方保存链路、Mindcraft 控制/清理边界、世界选择。负责人试玩及全套资源采样均待真正连通后再做；本轮工程证据不支持学习、理解或共同经历已经成立。

根代理核对：实际角色 UI 与官方默认文本在规范化换行后完全一致；160 个本轮源码/证据/本机记录文件未发现实际云密钥字节，217 个 P7 文件未发现本机会话令牌字节（AIRI 配置按负责人授权排除在这个扫描范围外）。代理退出码 0，18787、18080、25575 均无监听。代理原始请求/响应日志只在 runs，角色原文是负责人明确要求保存的审计材料；这不等于审计过 AIRI 自身全部本地存储。
