# D17 工程试跑

已完成官方本机动态注册、PKCE、回环回调、OIDC 签名／受众／nonce 校验、旋转刷新令牌的串行更新与 DPAPI 保存。没有读取 Codex 认证文件。`companion.model.Model(..., route='chatgpt')` 是显式选择；传输还要求 `synthetic=True`。默认 DeepSeek 与美元日账本继续保留。

账户目录实际列出的模型中，选定 `gpt-6-astra`、`medium` 作为 U4 的 D2。此选择发生在任何 U4 调用之前。

| 合成试跑 | 完成 | 严格四字段 JSON | 中位数 | P95 |
|---|---:|---:|---:|---:|
| 推理 medium | 20 | 20/20 | 4.1223 秒 | 7.3247 秒 |
| 推理 none | 0 | 不适用 | 不可测 | 不可测 |

关闭推理的首个请求被服务器拒绝，HTTP 400、`unsupported_value`；原文在 `PILOT_CALLS.jsonl`。没有把 low 冒充关闭推理，也没有重复发送另外 19 个必然不支持的请求。

首次解析器没有收集 `response.output_item.done`，误把 4 次成功流的空终止 `output` 当作无 JSON，发现后停下修复。4 次原记录保留；修复后另起 v2 合成试跑，20 次全部通过。两轮加不支持请求共 25 次推理请求；已知输入 5,712、输出 1,668 tokens，其中不支持请求未返回 usage。费用属于订阅，不计入美元账本。

撤销仅针对 Ego 自有会话。官方撤销端点成功后，再用已撤销刷新令牌调用官方 token 端点，得到真实 HTTP 400：`invalid_grant`，`error_reason=refresh_token_invalidated`。原文与 request ID 在 `REVOCATION.json`，令牌从未写入证据。负责人已重新登录。

套餐额度耗尽尚未在实网出现，不编造原文，也不为制造错误耗尽整份套餐。离线注入已验证 HTTP／流内额度错误停止、没有付费回退；U4 若实际遇到上限，将保留原始错误并续跑剩余决定。严格 JSON 通过不代表全部错误分支都已实网验证。

面板已加入账号选择、连接状态、次数／token／错误、Manage usage 与断开按钮；真实 GUI 的显示布局尚未人工验收。数据条款原文短摘录及适用范围限制见 `DATA_TERMS.md`。
