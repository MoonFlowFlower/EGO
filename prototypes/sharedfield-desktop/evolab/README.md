# EVOLAB — 演化可塑性实验室

在一个像桌宠生活的小世界（Room-v0）里，用进化策略检验"演化出的终生可塑性在环境漂移中是否带来存活优势"。这是独立研究实验室，不接桌宠运行时，不调用 LLM。

当前状态：**E0、E1工程通过；E2完成20/20次，按预注册为负结果**（2026-10-02）。H1不成立，H2不适用，H3成立。报告见 [E2_REPORT.md](evidence/E2_REPORT.md)，执行记录见 `PROGRESS.md`。漂移训练后超过99.9%的独立开发回合在200步前死亡，本轮对持续适应的覆盖有限，不支持推断可塑性一般无效。

**下一张卡：EVOLAB-002A（文档已就绪，未实施）**。001A 的 E2 经审计发现，所有运行都退化成"原地不动"，没有检验到目标问题。002A 先通过三道闸门（世界要求适应、两臂学得会觅食、正式有效性）再做检验。入口：`STAGE_CARD_002A.md`、`PREREG_002A.md`、`CODEX_KICKOFF_002A.md`。

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

## 复现入口

在本目录使用 Python 3.12 建立 `.venv`，从 `requirements-evolab.txt` 安装锁定依赖（含官方 cu128 索引）。不支持用CPU代替正式GPU运行。

```powershell
.venv/Scripts/python.exe scripts/e0_smoke.py
.venv/Scripts/python.exe -m pytest tests -q --basetemp=runs/pytest-reproduction
.venv/Scripts/python.exe scripts/e1_check.py
```

正式配置已经冻结在 `configs/e2_frozen.yaml`，不要重新运行冻结脚本或修改配置。训练入口先验证配置与预注册哈希。

```powershell
.venv/Scripts/python.exe scripts/e2_train.py --arm gru_mb_plastic --regime drift --seed 0
.venv/Scripts/python.exe scripts/e2_continue.py
```

上面是从空 `runs/` 起步的正式执行顺序，不要在当前已有运行目录重复启动。预跑计入20次；执行器核算24小时预算后继续其余19次，失败即停并记账。只有20次完成且训练世界工程有效性满足后，才允许保留集评估。已访问保留集的目录禁止重新训练。最终选择始终是第400代均值。

证据入口：`evidence/E0_ENV.md`、`evidence/E1_WORLD.md`、`evidence/E2_REPORT.md`、`evidence/final_audit.json`。逐代原始日志与检查点留在被忽略的 `runs/`；Git中仅发布摘要、报告和图像。

本目录已有最终判定，按停止条件收口，不再运行上面的训练命令。保留原始 `runs/` 时，可用下面的只读审计重算保存结果；不产生新回合：

```powershell
.venv/Scripts/python.exe scripts/audit_delivery.py
```
