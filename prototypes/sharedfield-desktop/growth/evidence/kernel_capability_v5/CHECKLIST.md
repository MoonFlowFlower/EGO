# 固定模型的推理模式：验收前判据

继承v2至v4的C1–C6、同一原话、同一体素/参数迁移/反例场景、形状与材料标准。v4失败保留。本次独立claim上限100请求/600秒/新增0.15美元，仍受原batch和总账本控制。

唯一生产行为变量：companion任务执行的模型调用显式reasoning.enabled=true、effort=high、exclude=true，输出与推理合计最多8192token（既有代理已允许的推理上限）。路由/纯聊天仍无推理、最多1600；不改P7代码、不换DeepSeek/Wafer、不提高原金钱上限、不采集隐藏推理文本。记录请求选项与usage中的推理token数用于核对是否实际生效。若接口不支持、超时、预算不足或输出截断，真实记录失败，不换路线完成。

2026-10-04只读GET /api/v1/models返回本模型default_enabled=true、supported_efforts=[max,high,low]；/models/deepseek/deepseek-v4.1-flash/endpoints返回Wafer支持reasoning与reasoning_effort。官方文档说明exclude=true仅排除返回的推理文本，推理仍计费并占用max_tokens：[OpenRouter reasoning](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)。本地旧请求未指定reasoning，p7/proxy.py补enabled=false。

任务执行结果、空间结构和缺口回复仍由同一冻结场景与人工语义检查判定。开启推理不作为通过证据，更不等于经验学习。其它生产提示、流程与工具保持v4；新增离线请求检查后冻结。
