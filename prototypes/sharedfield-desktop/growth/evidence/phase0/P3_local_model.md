# P3 本地模型单回合工程摸底 — 2026-10-02

负责人确认 Ollama 已卸载，改用已有 LM Studio；未安装 Ollama、未下载新模型。使用现有 google/gemma-4-12b-qat（Gemma 4 12B it QAT Q4_0 GGUF），本地标识 growth-p3，context 8192，GPU offload 0.65。加载 8.29 秒，lms 报模型占用 6.66 GiB；这与全机显存采样不是同一指标。

运行 `scripts/play_probe.py lmstudio --model growth-p3 --tag lmstudio`。种子 11，180 环境步上限；17 固定动作与 1–4 次重复，阻挡时提前停止移动。未生成/执行模型代码。输入为 P1 v1 观察和近四次动作历史；提示仅给基本操作说明，并非设计第 3 节完整出生包。

| 指标 | 实测 |
|---|---:|
| 决定次数 / 环境步 | 30 / 30 |
| 墙钟时间 | 195.815 秒 |
| 每次决定延迟中位 / 最大 | 6.363 / 9.003 秒 |
| 输入 / 输出 token | 56,963 / 1,428 |
| 云端调用费用 | 0 USD |
| 终止 | 第 30 步死亡 |
| 终局负责人统计 | collect_wood=1，未制作工具 |

证据：`p3_lmstudio.json`、`p3_decisions.json`（逐决定延迟与用量）；原始允许观察 replay 在 runs/phase0/p3_lmstudio。决定延迟包含本机 HTTP 往返与模型生成，不含环境步/采样开销，模型内部阶段延迟未分解。

31 次决策边界采样加后半段 78 次约秒级采样：全机 GPU 69–80 °C、682–2295 MHz、8611–9216 MiB、28.48–133.37 W，采样均插电；后半段采样不是全程覆盖，CPU 温度未验证。额外采样摘要见 `p3_lmstudio_thermal.json`，逐秒原始采样仅留 runs/phase0/p3_lmstudio_thermal.json。

失败与偏离：Ollama 不存在，使用负责人已有 LM Studio。没有协议拒绝或调用错误；游戏死亡按正常停止记录。此单回合成绩只供接通与成本摸底，不能作为能力证据；不同协议版本/运行环境下不能与 P2 作模型优劣比较。长期稳定性、完整出生包、示范后表现、换模型连续性未验证。未触发 2 小时时间盒。

接口依据：[LM Studio OpenAI compatibility](https://lmstudio.ai/docs/developer/openai-compat)。
