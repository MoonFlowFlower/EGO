# P7 本机代理：事前验收清单

状态：`PRE-REGISTERED / NOT YET RUN`。本清单写于首次代理测试之前，依据设计 v0.8、第 17 节、D9、D10 与 P7 kickoff。试验结果只追加，不按结果更改以下验收条件。

本轮用户指令优先于 kickoff 的旧密钥规则：不新写密钥文件，上游密钥与每次启动的随机令牌不写入日志或命令行。代理接受父进程内存注入；父进程沿用已授权 `growthlab.models.read_key` 读取既有凭据。交互启动面板接受内存输入；代理本身不读取旧密钥文件。会话令牌仅在进程内存和受控本地交互界面使用。

| 项目 | 事前判据 | 证据边界 |
|---|---|---|
| 本机隔离 | 仅绑定 `127.0.0.1`，每实例新令牌，错误/缺失令牌返回 401，未调用上游，并有脱敏事件记录 | 离线 HTTP 测试 |
| 路由 | 仅 `deepseek/deepseek-v4-flash-0731` / `open-inference/fp8`；ZDR 清单预检；`only`、`allow_fallbacks=false`、`data_collection=deny`、`zdr=true`、`require_parameters=true`；单价上限输入 1/输出 2 美元每百万 token；拒绝客户覆写 provider、模型或其他出站地址 | 假上游验证请求；真实预检另记 |
| 预算 | 真实默认与阶段 1 共用 `growth/runs/phase1/budget.sqlite`，上限 5 美元；`BEGIN IMMEDIATE` 原子预留，超额返回 402 且不调用 completion；未知/失败费用不释放；离线并发只允许总预留不超过上限 | 临时账本测试不冒充真实账本 |
| 消息 | 文本、工具定义、工具调用、工具结果语义保持不变；默认前/后插入点均为 passthrough；拒绝图片、音频、远程资源、服务端工具或插件 | 离线逐对象比较 |
| 兼容性 | Bearer 鉴权的 `GET /v1/models`、JSON 与 SSE 的 `POST /v1/chat/completions` 可用；SSE 正确处理注释、usage、`[DONE]`、工具调用；不执行任何生成代码 | 假上游协议证据；AIRI 真实 Ping 单独验收 |
| 断网 | 模拟网络连接失败返回 502；记录失败类别和预留金额；不将异常正文、头部或密钥写出 | 模拟断网不冒充物理断网 |
| 敏感信息 | 事件和本机内容日志均不含测试注入的上游密钥/代理令牌；HTTP 默认访问日志关闭；错误不回显客户端输入和上游错误正文 | 离线扫描；真实凭据不在测试中使用 |
| 实际接入 | AIRI 的真实 Ping 成功才写 `AIRI PING PASS`；未做或失败均保留原状 | 由根代理记录，不用离线测试代替 |

限制在运行前写定：JSON 请求不超过 60,000 UTF-8 字节；只允许一个 completion；输出默认 512 token，非推理最多 2,048，显式推理最多 8,192；预留 `max(0.05, (请求字节数 + 2048) * 0.000001 + 最大输出 token * 0.000002)` 美元，继承 P2 的保守字节界和价格上限。客户端断流时保留未知费用预留。若上游报告费用超过预留，记真实费用并将后续调用挡在总预算检查处。

不允许通过调整判据、提示词或脚本把未通过的真实探针改记为通过。工程缺陷修复与重测如有发生，逐次记录；不涉及学习效果或 Crafter 研究线。

官方协议参考（2026-10-02 读取）：[OpenRouter streaming](https://openrouter.ai/docs/api_reference/streaming)、[provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)、[Chat Completions](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion)。

## 实现与接口

原清单以上部分保留为事前快照；本节及其后是实现与结果，不能倒改事前判据。

新增 `growth/p7/proxy.py`，仅用 Python 标准库。复用 `growthlab.models` 的固定模型与路由常量，适配其 P2 `charges` 表、价格上限、保守预留和 `BEGIN IMMEDIATE` 规则；未改旧模型代码、设计或旧证据。每个账本操作使用独立 SQLite 连接，可与 U1/P2 进程同时预留。

父进程从 `growth/` 目录运行，或将该目录放到 Python 导入路径。下面的 `key` 是父进程已持有的内存变量，示例不包含凭据：

```python
from p7.proxy import FixedRouteTransport, ProxyServer

transport = FixedRouteTransport(api_key=key)
transport.preflight()  # 只查官方 ZDR 元数据，不请求 completion
server = ProxyServer(transport, port=8787).start()
base_url = server.base_url  # http://127.0.0.1:8787/v1
session_token = server.token  # 仅在内存中转交给不持久化凭据的客户端
# 使用结束后调用 server.close()
```

`ProxyServer(..., port=0)` 可由操作系统分配空闲端口。`allowed_origins={实际 Origin}` 是显式本机 webview 白名单；默认包含 `http://tauri.localhost`、`tauri://localhost`、`app://localhost`。未给 Origin 的本机 MC 客户端可用；不允许任意网站读取代理。Base URL 不加 `/chat/completions`。

- `GET /v1/models`：返回唯一获准模型，需要 Bearer 令牌，不发上游请求。因此仅模型列表通过不算 AIRI 的真实 Ping 成功。
- `POST /v1/chat/completions`：文本、函数工具定义/调用/结果；非流式 JSON 和流式 SSE。传入 `messages`、`tools` 等对象不重写；transport 加固定路由与输出界限，流式请求加入 usage 记账要求。
- `before_forward` / `after_forward`：现为恒等函数，预留以后接 U1 库；这轮没有学习逻辑。代理不会执行函数工具或生成代码。
- `events.jsonl`：本机请求时间、耗时、结果、token、费用/预留、账本总额；`content.jsonl`：本机请求/响应内容。仅在 `growth/runs/p7/proxy/`，脱敏已知密钥与本轮令牌；被拒请求和错误正文不落内容日志。HTTP 访问日志关闭。
- 固定出站 HTTPS 到 OpenRouter；禁用环境 HTTP 代理和 HTTP 重定向。端点、支持参数或 ZDR 预检失败即拒绝，不使用回退。

`python -m p7.launch_proxy --port 8787` 提供本地 Tk 面板，输入密钥、显示地址和默认遮住的会话令牌，不接收密钥命令行参数、不保存凭据。面板已验证可导入且 Tk 可用；图形交互尚未人工试玩。AIRI 客户端若把输入的令牌写进配置，必须另找仅内存接入路径，不能直接保存令牌。

## 工程验证记录

1. 第一轮 19 项有 18 项通过、1 项失败：非流式 JSON 成功响应先于预算结算，立即读账暂见 `reserved_unknown`。原始失败证据：`runs/p7/proxy/offline-20261003T033857-d5871df8/result.json`。这是真实实现竞态，不作通过记录。
2. 仅修复响应收尾顺序：已知费用及审计先提交，再发 JSON 成功响应或 SSE `[DONE]`。原 19 项测试脚本、提示内容和判据未改；第二轮 19/19 通过：`runs/p7/proxy/offline-20261003T033924-77d012c2/result.json`。
3. 额外零费用检查确认真正缺失 Authorization 头返回 401，上游调用为 0：`runs/p7/proxy/offline-20261003T034018-dd6e367a/extra_checks.json`。独立检查启动模块以 `-W error` 导入成功，Tk 可用。修正了启动面板在用户按 Stop 后异步预检完成的收尾逻辑；面板不在这 19 项 HTTP 测试覆盖之内。
4. 最终源文件版本的原 19 项复测全部通过：`runs/p7/proxy/offline-20261003T034059-78e6ad96/result.json`。三轮使用相同测试脚本，汇总与源码哈希见 `proxy_engineering.json`。事前条件内容保持不变；追加本实现节时仅在原清单末尾增加了一个段落分隔换行，汇总保留各次捕获的原始哈希。

结论边界：`OFFLINE ENGINEERING PASS`；离线测试费用为 0。模拟上游/模拟断网不能替代 AIRI 真实 Ping、当前上游路由、物理断网或负责人体验。上述真实验收尚未由本组件执行；总报告另记。代理没有运行 Crafter，也没有启动常驻服务。

## 后续授权补充（2026-10-02）

负责人在首次离线验收之后明确允许：**仅本机代理的本轮令牌可以保存到 AIRI 的本地配置**。云端密钥仍只在进程内存中使用，不新写文件、日志或命令行。原事前清单不改；此后真实 AIRI 接入按这项明确授权执行。代理自身依旧不把令牌写入任何文件或日志；每次启动生成新令牌，旧值在代理关闭后失效。

根代理可通过父进程持有的私有管道把令牌交给本机接入进程，再填入 AIRI 设置。这项授权仅涉及本机令牌的 AIRI 配置持久化，不改变消息、提示词、模型、路由、预算、费用限制或学习判据。
