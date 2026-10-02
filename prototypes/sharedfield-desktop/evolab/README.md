# EVOLAB — 演化可塑性实验室

在一个像桌宠生活的小世界（Room-v0）里，用进化策略检验"演化出的终生可塑性在环境漂移中是否带来存活优势"。这是独立研究实验室，不接桌宠运行时，不调用 LLM。

当前状态：**文档已就绪，代码未实施**（2026-10-02）。执行记录见 `PROGRESS.md`。

## 阅读顺序

1. `STAGE_CARD.md`：目标、阶段、边界、证据契约、停止条件、声明上限（约束）
2. `PREREG_E2.md`：E2 的假设、阈值与判定规则（冻结，不可改）
3. `DESIGN.md`：推荐实现，包括世界、两种大脑、ES、评估、测试、目录
4. `ENVIRONMENT.md`：Windows 原生 + PyTorch 的 GPU 环境与实现约定（WSL2 + JAX 为备选）
5. `RESEARCH_BACKGROUND.md`：为什么走这条路
6. `JAXLIFE_ASSESSMENT.md`：参考项目评估与 CPU 实测
7. `CODEX_KICKOFF.md`：交给实施代理的开场白

## 边界

只在本目录内工作；唯一例外是可以在 `../TASK_BOARD.md` 中记录 EVOLAB 进展和规划任务（见卡片第 4 节）。不修改 `../desktop_pet/`、`../memory_lab/`、`../SharedField/` 和仓库根目录主线。大文件放 `runs/`（已忽略），证据摘要放 `evidence/`。
