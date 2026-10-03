# GPT-6 Luna / Azure 独立试用事前清单

2026-10-03。用户要求“试试吧”。本轮先验证兼容性、单并发连续调用及已给定约定的使用，不直接把小测当成学会用户或完成 U1。

## 固定配置与授权边界

- `openai/gpt-6-luna`，OpenRouter 固定 `azure`，ZDR、data_collection=deny、require_parameters=true、allow_fallbacks=false；共享原 `runs/phase1/budget.sqlite` $5 上限。
- 元数据已查：普通短上下文输入 $0.10/M、输出 $0.50/M；缓存写入 $0.125/M。现有 60,000 字节请求上限不会到 272K token 长上下文加价门槛。每次仍按最高允许单价预留，不用低估的报价替代账本。
- 原代理要求的 temperature、max_tokens 不在该端点支持列表。本适配器省略温度（不等同于温度 0），将输出上限传为 max_completion_tokens，固定 reasoning_effort=none。含 temperature 或要求其它推理档位的请求在收费前拒绝，不静默抹掉调用者设置。
- 官方 Chat Completions 工具调用要求 reasoning_effort=none，本轮遵守。密钥只通过已授权旧读取器进内存；模型输出的工具调用只检查，不执行。不安装软件，不改 AIRI UI、世界或后台常驻进程。
- 原 `u1/`、`growthlab/`、routing-v1/v2 的冻结源码/提示/阈值保持不变。试用新增文件独立冻结；不修改当前产品默认路由或将失败借备用掩盖。

## 在调用前固定的顺序和判据

1. 先完成零费用工程检查：真实本机 HTTP 入口、转换后的 wire 参数、消息/工具不变、拒绝温度和高推理、输出/费用/隐私边界、429 不重试且未知预留保留、错误分类不泄漏正文、流式协议。冻结源码、下列探针、U1 原产物和此清单的 SHA256 后才收费。
2. 兼容性：直接复用 `p7.smoke_routing.PROMPTS` 的 JSON、SSE、强制 echo 三个探针及 `inspect_response` 判定函数；仅推理和输出上限参数换成以上 Luna 支持的形式，温度省略，最大输出 512。三项均通过且费用可核对，才进入下一步；失败如实记下后停止。
3. 约定描述测试：直接复用原 `u1.run.worker_ua` 的 B-only 模式，全部 30 个既有局面 × 无卡/真卡/假卡，共 90 次决定，按原顺序、原提示、原选项、原关键词、原严格 JSON 判定运行。最大输出 1024。暗号真卡与假卡各 ≥8/10 且完整跑完，是原提供记忆使用判据；情绪、承诺和无卡结果照表报告。记忆为脚本预置，不是模型从对话学得；没有 A 对照、Ub、Uc 或重启迁移链条，不能称为完整 U1 或证明比 DeepSeek 更强。
4. 并发 1，串行完成后立即下一次，无人工 sleep、无重试、无端点切换。任何 HTTP/连接/元数据/预算错误立即停止本轮；连续两个不合法决策 JSON 也停止，单个不合法计错。有效但答案错误不调整提示，继续原矩阵。记录实际尝试数、429 数、总时长、请求速率和 p50/p95/最大完整响应延迟，不进行寻找限流上限的压力测试。
5. 本轮最多 93 次收费尝试，最多 15 分钟；新增费用加未知预留不超过 $0.50，原总上限优先；每次调用前按实际 wire 的最坏预留检查两项余额。失败预留不释放。全程插电，继承原工程的资源检查；异常停止留证据。
6. “可继续作为候选”需 3/3 兼容性通过、90/90 决策协议合法、两项暗号判据达线，且描述测试 p95 完整响应延迟 ≤10 秒。是否出现 429 必须单列；0 次仅说明此时段单并发未观察到限流，不代表永不限流。候选通过也不自动改现有产品主模型；本轮交付独立可复用适配器和证据。

官方来源：[Luna 模型说明](https://developers.openai.com/api/docs/models/gpt-6-luna)、[OpenRouter 模型页](https://openrouter.ai/openai/gpt-6-luna)、[ZDR 端点](https://openrouter.ai/api/v1/endpoints/zdr)、[限流说明](https://openrouter.ai/docs/api/reference/limits)。预检快照留 `runs/luna/preflight/zdr.json`，原始请求/响应、运行状态和费用留 runs/，不提交。
