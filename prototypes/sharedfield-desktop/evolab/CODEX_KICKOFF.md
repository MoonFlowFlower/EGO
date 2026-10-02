# 给 Codex 的开场白（可直接粘贴）

---

你要实施 EGO 仓库中的研究卡 **EVOLAB-001A**：在一个桌宠式小世界里，用进化策略检验"演化出的终生可塑性在环境漂移中是否带来存活优势"。所有文档都已经写好，你的工作是按文档把它做出来、跑出来，并如实记录。

**仓库与位置**
- 仓库：`MoonFlowFlower/EGO`
- 分支：`codex/desktop-pet-memory-lab-20261001`。如果分支里还没有 `prototypes/sharedfield-desktop/evolab/` 目录，说明文档 PR 尚未合并，请改从 `ccr-3d0efea2-b4lya7` 分支开始。
- 工作目录：`prototypes/sharedfield-desktop/evolab/`
- 机器：Windows + RTX 5070 Ti Laptop（12GB，Blackwell，sm_120）。主路径为 **Windows 原生 + PyTorch（cu128 及以上）**，不需要 WSL；直接在 Windows 的 git checkout 中工作。

**开工前先按顺序读完**
1. `evolab/STAGE_CARD.md`：约束，包括边界、证据契约、停止条件、声明上限
2. `evolab/PREREG_E2.md`：冻结的假设与判定，任何时候都不能改
3. `evolab/DESIGN.md`：推荐实现
4. `evolab/ENVIRONMENT.md`：Windows 原生 PyTorch 环境步骤与实现约定
5. `evolab/RESEARCH_BACKGROUND.md`、`evolab/JAXLIFE_ASSESSMENT.md`：背景

**任务契约**
- 任务类型：执行（研究实现）
- 真实目标：得到一个可信的 E2 判定（正、部分或负都行），而不是"做出正结果"
- 成功判据：E0、E1 的工程证据齐全；E2 的 20 次运行完成；严格按预注册判定；报告与执行账本如实记录
- 当前层级：设计已完成，实现从零开始
- 权威来源：`STAGE_CARD.md` 和 `PREREG_E2.md`。两者与 `DESIGN.md` 冲突时，以前两者为准

**执行顺序与检查点**
1. **E0**：按 `ENVIRONMENT.md` 搭建环境并做冒烟测试，结果写入 `evidence/E0_ENV.md`，内容包括驱动、CUDA、PyTorch 版本，设备名与计算能力，矩阵乘吞吐，确定性检查。GPU 不可用时，停下来向我报告具体错误和版本组合。不要退回 CPU 跑正式规模，也不要靠猜测反复降级。
2. **E1**：实现 Room-v0 世界、两种大脑（`gru_fixed`、`gru_mb_plastic`）、基线 R 和 H、OpenES，以及 `DESIGN.md` 第 8 节列出的全部测试。实测吞吐，渲染一段 GIF。世界参数只允许在这个阶段调整，每次调整都写进 `PROGRESS.md`。完成后冻结 `configs/e2_frozen.yaml`，把 SHA-256 记入 `PROGRESS.md`。
3. **E2 预跑**：先完整跑 1 次正式运行，记录实际耗时，按 20 次核算总时长。预计 ≤24 GPU 小时就直接继续。超出时停下来，把"缩小规模的方案"写进 `PROGRESS.md` 并问我，在我确认前不要开跑。
4. **E2 正式**：跑完 20 次运行，在保留集上评估，做消融，按 `PREREG_E2.md` 判定，写出 `evidence/E2_REPORT.md`。

**硬性禁止**
- 看到保留集结果后修改阈值、指标、条件或选择规则；用中途最佳检查点替代第 400 代均值基因组；开发期间使用保留集种子。
- 复制 JaxLife 代码（它没有许可证），只能借鉴思路。
- 修改 `evolab/` 以外的目录，包括 `desktop_pet/`、`memory_lab/`、`SharedField/` 和仓库根目录主线。
- 宣称生命、意识、情感、主观能动性，或宣称结果能迁移到桌宠。声明上限见卡片第 7 节。
- 把 NaN、崩溃或失败的运行删掉不记。所有失败都写进 `PROGRESS.md`。
- 同一个工程问题连续两次修补失败后继续第三次同方向修补。这时要停下来，上升一层重新分析原因。

**Git 规则**
- 只提交 `evolab/` 下的文件，按路径逐个 `git add`，禁止 `git add -A` 或 `git add .`。
- `runs/` 已被 gitignore，逐代日志和检查点不要提交；提交摘要 JSON、报告和 GIF。
- 每完成一个阶段就提交并推送到当前分支，提交信息写清楚阶段和证据位置。

**每个阶段结束时向我汇报**
- 做了什么，证据文件在哪里；
- 实测数字（吞吐、耗时、存活率），以及与预期的偏差；
- 失败和偏离；
- 下一步，以及是否触发了任何停止条件。

没有验证证据的事情一律写"未验证"。不要用"已完成"包装没跑过的东西。

---
