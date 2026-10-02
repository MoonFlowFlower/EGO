# EVOLAB 执行账本

按时间倒序追加。每条写明：做了什么、证据在哪、失败或偏离、下一步。没测的写"未测"。旧条目不改。

## 2026-10-02 — E0 环境阻断（Codex）

- 状态：**BLOCKED / E0 未通过 / E1、E2 未开始**。E2 运行数 0/20，训练启动数 0，训练 GPU 时间 0 小时；性能、确定性与存活率均未验证。
- 操作：从现有 `.publish/EGO` checkout 快进同步指定分支到 `14dc7cb86b5407523d33692fe190a3d837ef639b`；该分支已包含文档，无需备用分支。按指定顺序读完六份研究文档，执行 Windows GPU 与 WSL 只读检查。
- 证据：`evidence/E0_ENV.md`，含版本组合、失败命令、原始错误文本、硬件差异、未验证项及恢复路径。
- 阻断：唯一一次 Ubuntu 启动尝试退出码 1，错误 `Wsl/Service/CreateInstance/CreateVm/HCS/HCS_E_SERVICE_NOT_AVAILABLE`。固件虚拟化 True、HypervisorPresent False，找不到 vmcompute/hns；可选功能状态查询需要管理员权限，具体根因未验证。未进行修补或依赖降级。
- 实机偏差：RTX 5070 Ti **Laptop GPU，12227 MiB**，驱动 616.56，CUDA UMD 13.4；任务描述为 16GB。WSL 2.6.3.0 / 报告 kernel 6.6.87.2-1 / Windows 10.0.26100.6584；Linux CUDA、JAX、jaxlib 版本未验证。
- 其他失败与偏离：初始 cwd 无 Git 仓库，已定位；WSL 前置启动检查早于研究文档读取，未开展实现/训练。bcdedit 查询参数错误；根上下文文件的直接读取失败，已通过 Git 对象读取。细节均见 E0 报告。WSL 不可启动，因此尚未克隆到 Linux 原生文件系统；Windows checkout 仅保存证据，不用于运行实验。
- 停止条件：触发 STAGE_CARD 第 3、6 节的 GPU 运行环境不可用条件。无 CPU 正式运行、无保留集访问、无训练失败被丢弃、无世界参数调整、无配置冻结。未修改 PREREG_E2，文档 SHA-256 `B0B8E3939A3CF22B1FB7071E576CAE8AA9EC71D93CC25D33635D131FCC15E082`。
- 边界：仅编写 evolab 下证据与账本；不执行卡片末尾的 TASK_BOARD 修改要求，因为本轮用户明确禁止修改 evolab 外文件。
- 下一步：用户安排管理员检查/恢复 WSL2 所需 Windows 功能及必要重启；恢复后在 `~/EGO` 继续 E0 并实测全部指标。此次环境阻断不作科学负结果判定。

## 2026-10-02 — 文档阶段（Claude）

- 完成：`STAGE_CARD.md`、`PREREG_E2.md`（冻结）、`DESIGN.md`、`ENVIRONMENT.md`、`RESEARCH_BACKGROUND.md`、`JAXLIFE_ASSESSMENT.md`、`CODEX_KICKOFF.md`。
- 证据：JaxLife CPU 基准见 `evidence/jaxlife_bench/`。
- 未测：用户机器上的 WSL2 / JAX GPU 环境、Room-v0 吞吐。全部代码尚未编写。
- 当前层级：想法 → 构件（设计已完成，实现未开始）。
- 下一步：实施方执行 E0（`ENVIRONMENT.md`），把结果写入 `evidence/E0_ENV.md`。
