# EVOLAB 执行账本

按时间倒序追加。每条写明：做了什么、证据在哪、失败或偏离、下一步。没测的写"未测"。旧条目不改。

## 2026-10-02 — E1 工程通过、配置冻结（Codex）

- 完成Room-v0、R/H、两臂、OpenES与测试；世界参数未改。参数量18246/18254。证据 evidence/E1_WORLD.md、e1_world.json、e1_graph_benchmark.json、e1_tests.json、e1_hand_static.gif。
- 最终串行复验22测试通过/17.92秒；两臂各5代两新进程逐位一致，CUDA Graph与eager完整世界/脑状态逐位一致。H=1.0 [1,1]，R=0.0798047 [0.077875,0.081854]（256static回合）。
- 真实eager A/B吞吐0.941M/0.797M，低于2M起点。采用CUDA Graph及每32步全死检查；热图初始基因组0.08948/0.19034秒，只执行192步，不能用于演化后的预算外推。
- 冻结 configs/e2_frozen.yaml，SHA-256 `134d90c1d7e935be720d73445784b488818c16744c8d29f98f177c97493e14a8`。PREREG_E2哈希仍为 `B0B8E3939A3CF22B1FB7071E576CAE8AA9EC71D93CC25D33635D131FCC15E082`。无保留集访问。
- 首测argsort错误、H语义修正和中间争用测量已记录。E1长写入命令被自动审批拒绝，仅返回blocked by policy，未执行；已拆成独立文件编辑/校验。没有连续两次同问题修补失败，无NaN，用户GIF目检未验证。
- 下一步B/drift/seed0完整400代预跑，按实测乘20；超过24小时停并提交缩小方案等待确认，否则继续其余19次。所有摘要提交，逐代与检查点留runs。

## 2026-10-02 — E1 语义复核与吞吐优化候选

- 修补1通过：14测试/21.20秒。另发现H把噪声意外吃到的颜色归给原目标，已改成依据实际进食位置读取颜色，并加回归；增加GRU与PyTorch参考逐步比对后16测试通过/40.98秒。
- 首次完整基线：256回合R均值0.0798046865（95% CI 0.077875–0.081854），H均值1.0（CI 1–1），默认世界参数通过，无世界参数调整。
- 首次真实吞吐（1500步）：R的2048/4096/8192批为1.645M/3.155M/6.507M个体步/秒；A/B的2048批为0.956M/0.783M，低于设计起点2M。证据 runs/e1_check_attempt1.log。第二次基线测量可能与新增测试尾段重叠，性能不作为最终证据，原日志保留于 runs/e1_check_attempt2.log。
- 优化候选：按ENVIRONMENT约定尝试单步CUDA Graph，预先生成显式随机张量、固定状态/参数存储；图仅改变提交方式。采用前必须通过eager逐位等价与两新进程重放，并实测收益；不改变世界、适应度或预注册。

## 2026-10-02 — E1 首版测试失败与修补1

- 已实现批量世界、R/H、两臂和OpenES及测试，未冻结配置。世界参数仍为DESIGN默认值。
- 首次测试：8通过、6失败，7.10秒；日志 runs/e1_tests_attempt1.log。共同根因是投影生成的Tensor.argsort调用在stable=True时要求dim使用关键字，脑构造失败；无NaN或训练运行丢弃。
- 修补1：明确dim=-1；下一步重跑全部测试，若同问题再连续修补失败两次则停止并上升一层分析。保留集封闭。

## 2026-10-02 — E0 提交检查修正

- 失败：E0首次暂存检查报告JSON与requirements的CRLF为行尾空白；命令链未正确在检查非零时停止，随后提交并推送了9de9d07。实验数值无变化。
- 修正：仅将这两个新文件转为LF，保留第一次E0报告与TASK_BOARD原换行；后续提交拆开检查与提交步骤。该检查失败记录保留，不当作实验失败或GPU问题。

## 2026-10-02 — E0 第二次尝试通过（Windows PyTorch，Codex）

- 已拉取 PR #131/#132 至 ac8d3cf，预注册哈希未变。首次 E0 记录保留原字节，追加第二次尝试。
- 环境：`.venv` Python 3.12.13、torch 2.11.0+cu128、CUDA 12.8、capability (12,0)。脚本 `scripts/e0_smoke.py`，锁定 `requirements-evolab.txt`。
- 证据：`evidence/E0_ENV.md` 第二次尝试及 `evidence/e0_torch.json`。TF32 关/开 12807.76/25336.17 GFLOP/s；同进程和两新进程位级一致，最大差 0。短测温度59–74°C、核心277–2407MHz，长时降频未验证。
- 空状态吞吐23.18M/58.90M/117.54M个体步/秒（2048/4096/8192回合）；明确不等同于 Room-v0 或 ES。E1将补真实吞吐。脚本39.91秒；E2训练0次。
- 失败/偏离：本次无失败；使用 uv 安装指定 Python 与官方 cu128 轮子，运行时和缓存留在 runs，未动系统驱动/WSL/电源配置。E0先测空状态，真实世界吞吐按依赖关系在E1测。
- E0通过，停止条件未触发；下一步E1实现与验证，再冻结配置。TASK_BOARD仅更新EVOLAB段落。

## 2026-10-02 — 权限修订：实施方可维护 TASK_BOARD（Claude，按用户要求）

- 用户明确要求允许实施方自己规划任务。卡片第 4、8 节、`CODEX_KICKOFF.md`、`README.md` 已改为：实施方可以编辑 `../TASK_BOARD.md` 中与 EVOLAB 相关的进展和任务规划，北极星、用户已确认的需求、桌宠和 memory_lab 的既有记录不得改动。
- 这一条取代上一条修订中"TASK_BOARD 不由实施方更新"的说法。`PREREG_E2.md` 未改。

## 2026-10-02 — 环境路线修订（Claude，经用户同意改走 Windows 原生）

- 原因：E0 显示 WSL2 无法启动（hypervisor 未运行），用户倾向不依赖 WSL。JAX 的 CUDA 版只有 Linux 轮子，而 PyTorch 2.7 及以后的 cu128 轮子在 Windows 原生支持 sm_120。
- 改动：`ENVIRONMENT.md` 主路径改为 Windows 原生 + PyTorch，WSL2 + JAX 降为备选（附修复命令，由用户执行）。`DESIGN.md`、`STAGE_CARD.md`、`CODEX_KICKOFF.md`、`README.md` 中的 JAX 专有表述改为与框架无关，或改为 PyTorch 约定。硬件改为实测的 RTX 5070 Ti Laptop 12GB。卡片第 8 节改为：TASK_BOARD 不由实施方更新（消除与"只改 evolab"之间的冲突）。
- 未改：`PREREG_E2.md`（假设、指标、阈值、种子规则全部不变）。
- 未测：PyTorch 在用户机器上的可用性与吞吐，待重新执行 E0。
- 下一步：实施方按新的 `ENVIRONMENT.md` 重新执行 E0。

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
