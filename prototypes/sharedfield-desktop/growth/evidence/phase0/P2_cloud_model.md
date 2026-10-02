# P2 云端模型单回合工程摸底 — 2026-10-02

使用负责人指定的本机 codex 标签凭据，由服务端沿用既有标签解析方式读取；凭据值不写文件、日志、证据或网页。最终固定 OpenRouter `deepseek/deepseek-v4-flash-0731`、`open-inference/fp8`，拒绝路由回退，ZDR=true、data_collection=deny。仅发送 P1 v1 受限游戏观察和近四次动作历史；无个人叙事、全图、绝对坐标、原始录制或模型代码执行。

## 实测与失败保留

| 尝试 / JSON | 决定 / 步 | 墙钟秒 | 结果 | 回执 USD |
|---|---:|---:|---|---:|
| p2_initial | 0 / 0 | 1.617 | deepinfra/fp8 HTTP 429 | 未知 |
| p2_fallback | 0 / 0 | 0.990 | qwen3.5-flash alibaba HTTP 404 | 未知 |
| p2_verified_route | 13 / 9 | 51.210 | 连续两次输出协议拒绝后停止 | 0.000606244014 |
| p2_strict_protocol | 180 / 180 | 811.446 | 到 180 步上限 | 0.009896152917 |

两次连通失败后停止试换端点，回到隐私与路由兼容性层检查，发现公开 ZDR 列表未列该 Alibaba 路由；404 的确切原因未验证，未保存 HTTP 错误正文。添加调用前 ZDR/参数/价格预检后使用明确兼容路由。协议连续失败后再次停止并分析，将 JSON object 改为严格枚举 schema。早期没有保存错误输出正文，具体错误字段未验证。旧证据不覆盖、不删去。

最终回合 seed=11，180 步封顶；固定 17 动作及 1–4 重复。每次决定延迟中位 4.312 秒、最大 6.766 秒；输入 358,664 token，输出 15,383 token。逐次延迟见 `p2_decisions.json`。终局负责人统计 collect_drink=2、collect_sapling=10、collect_wood=3，未制作；这些计数不供后续策略读取，也不能作为能力证据。

全部可计费响应回执总额 **0.010502396931 USD**。两个失败请求分别保留 0.05 USD 未知预留，因此保守账本总计 **0.110502396931 USD**，低于 5 USD。`missing_cost_receipts=0` 仅指成功取得的响应，不代表两个 HTTP 失败免费。账户最终账单未验证。

预算：每次请求前 SQLite 事务预留 0.05 USD，提示限制 16,000 UTF-8 字节、输出 512 token，路由最高单价输入 1 / 输出 2 USD 每百万 token；未知费用不释放，不自动重试。密钥只驻本机服务端内存；账本不存密钥。

最终回合 181 次边界采样：全机 GPU 58–80 °C、382–2092 MHz、2549–9257 MiB；这段与本地模型/其他工作重叠，不能归因于云端模型自身显存或功耗。采样均插电；CPU 温度未验证。证据含完整边界采样，原始允许观察保留本地 runs/phase0/p2_*。

协议修复后完整单回合未再拒绝。未触发 5 USD 或 2 小时时间盒；触发过连通与协议停止，均在上一层分析后续行。完整出生包、学习、长期费用、供应商实际留存执行、跨模型能力比较均未验证。

公开依据：[模型与端点元数据](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4-flash-0731/endpoints)、[ZDR 列表](https://openrouter.ai/api/v1/endpoints/zdr)、[提供商路由](https://openrouter.ai/docs/guides/routing/provider-selection)、[数据收集设置](https://openrouter.ai/docs/guides/privacy/data-collection)。本批元数据快照 `p2_zdr_routes.json`。
